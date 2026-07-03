"""Kaggle TPU v3-8 multicore smoke test.

Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Verified launch contract:
  1. Do NOT call torch_xla.device() in the parent process.
  2. Pop TPU_PROCESS_ADDRESSES / CLOUD_TPU_TASK_ID before spawning — Kaggle
     sets TPU_PROCESS_ADDRESSES=local for its single host process, and if
     that leaks into the 8 spawned XLA workers they fail with
     "Expected 8 worker addresses, got 1".
  3. Spawn with xmp.spawn(..., start_method="fork").
  4. Acquire torch_xla.device() inside each worker, not the parent.
"""

import json
import os
from pathlib import Path

import torch_xla.distributed.xla_multiprocessing as xmp

STATUS_DIR = Path("/kaggle/working/worker-status")
STATUS_DIR.mkdir(parents=True, exist_ok=True)


def worker(index):
    import torch
    import torch_xla
    import torch_xla.runtime as xr
    import torch_xla.core.xla_model as xm

    device = torch_xla.device()
    ordinal = xr.global_ordinal()
    world_size = xr.world_size()

    t = torch.tensor([float(ordinal)], device=device)
    gathered = xm.all_gather(t)
    xm.mark_step()

    (STATUS_DIR / f"{ordinal}.json").write_text(
        json.dumps(
            {
                "index": index,
                "ordinal": ordinal,
                "world_size": world_size,
                "device": str(device),
                "gathered_shape": list(gathered.shape),
                "all_finite": bool(torch.isfinite(gathered).all().item()),
            }
        )
    )


def main():
    os.environ.pop("TPU_PROCESS_ADDRESSES", None)
    os.environ.pop("CLOUD_TPU_TASK_ID", None)

    try:
        xmp.spawn(worker, start_method="fork")

        statuses = sorted(STATUS_DIR.glob("*.json"))
        assert len(statuses) == 8, f"expected 8 worker-status files, got {len(statuses)}"
        for p in statuses:
            data = json.loads(p.read_text())
            assert data["world_size"] == 8, data
            assert data["all_finite"], data

        Path("/kaggle/working/run_status.json").write_text(
            json.dumps({"status": "multicore_smoke_pass"})
        )
        print("MULTICORE_SMOKE_PASS")
    except Exception:
        Path("/kaggle/working/run_status.json").write_text(
            json.dumps({"status": "failed"})
        )
        raise


if __name__ == "__main__":
    main()
