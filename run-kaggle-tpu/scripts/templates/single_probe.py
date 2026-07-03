"""Single-process Kaggle TPU smoke test.

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
"""

import datetime

print("PROBE_START", datetime.datetime.now(datetime.timezone.utc).isoformat())

import torch_xla
import torch_xla.runtime as xr

device = torch_xla.device()
print("TPU_DEVICE", device)
print("WORLD_SIZE", xr.world_size())
print("PROBE_DONE", datetime.datetime.now(datetime.timezone.utc).isoformat())
