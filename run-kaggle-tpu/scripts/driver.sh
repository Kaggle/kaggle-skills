#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Driver for scaffolding, pushing, polling, and pulling Kaggle TPU kernels.
# See SKILL.md for the full workflow write-up.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$SKILL_DIR/templates"

usage() {
  cat <<'EOF'
Usage:
  driver.sh scaffold <dir> <kernel-slug> [single|multicore]
      Create <dir>/kernel-metadata.json + probe.py from a template.
      kernel-slug becomes both the kaggle kernel id (<user>/<slug>) and title.
      Defaults to "single" (no xmp.spawn) if the mode arg is omitted.

  driver.sh push <dir>
      kaggle kernels push -p <dir>

  driver.sh status <kernel-ref>
      One-shot status check. <kernel-ref> is "<user>/<slug>".

  driver.sh poll <kernel-ref> [interval_seconds] [max_iterations]
      Poll status every interval_seconds (default 15) up to max_iterations
      (default 60, i.e. ~15 min) and print a timestamped line every time the
      status changes. Exits 0 on COMPLETE, 1 on ERROR/CANCELLED, 2 on timeout.

  driver.sh pull <kernel-ref> [out_dir]
      kaggle kernels output -p <out_dir> (default: <dir>/output next to cwd)

  driver.sh run <dir> <kernel-ref> [interval_seconds] [max_iterations]
      push + poll + pull in one shot. Convenience wrapper for the common case.
EOF
}

cmd_scaffold() {
  local dir="$1" slug="$2" mode="${3:-single}"
  local user
  user="$(kaggle config view 2>/dev/null | sed -n 's/^- username: //p')"
  if [ -z "$user" ]; then
    echo "Could not read kaggle username from 'kaggle config view'. Is ~/.kaggle/kaggle.json set up?" >&2
    exit 1
  fi

  mkdir -p "$dir"
  local meta_template probe_template
  case "$mode" in
    single) meta_template="$TEMPLATES/kernel-metadata.single.json"; probe_template="$TEMPLATES/single_probe.py" ;;
    multicore) meta_template="$TEMPLATES/kernel-metadata.multicore.json"; probe_template="$TEMPLATES/multicore_probe.py" ;;
    *) echo "mode must be 'single' or 'multicore', got '$mode'" >&2; exit 1 ;;
  esac

  sed -e "s/__KAGGLE_USER__/$user/g" -e "s/__KERNEL_SLUG__/$slug/g" \
    "$meta_template" > "$dir/kernel-metadata.json"
  cp "$probe_template" "$dir/probe.py"

  echo "Scaffolded $mode kernel at $dir"
  echo "  id: $user/$slug"
  echo "Next: driver.sh push $dir"
}

cmd_push() {
  local dir="$1"
  kaggle kernels push -p "$dir"
}

cmd_status() {
  local ref="$1"
  kaggle kernels status "$ref" 2>/dev/null | tail -1
}

cmd_poll() {
  local ref="$1" interval="${2:-15}" max_iter="${3:-60}"
  local prev="" st ts
  for ((i = 1; i <= max_iter; i++)); do
    ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    st="$(cmd_status "$ref")"
    if [ "$st" != "$prev" ]; then
      echo "$ts  $st"
      prev="$st"
    fi
    if echo "$st" | grep -q "COMPLETE"; then
      return 0
    fi
    if echo "$st" | grep -qE "ERROR|CANCEL"; then
      return 1
    fi
    sleep "$interval"
  done
  echo "poll: timed out after $((interval * max_iter))s, still: $st" >&2
  return 2
}

cmd_pull() {
  local ref="$1" out="${2:-./output}"
  mkdir -p "$out"
  kaggle kernels output "$ref" -p "$out"
}

cmd_run() {
  local dir="$1" ref="$2" interval="${3:-15}" max_iter="${4:-60}"
  cmd_push "$dir"
  cmd_poll "$ref" "$interval" "$max_iter"
  local rc=$?
  cmd_pull "$ref" "$dir/output"
  return $rc
}

main() {
  local sub="${1:-}"
  [ -n "$sub" ] || { usage; exit 1; }
  shift
  case "$sub" in
    scaffold) cmd_scaffold "$@" ;;
    push) cmd_push "$@" ;;
    status) cmd_status "$@" ;;
    poll) cmd_poll "$@" ;;
    pull) cmd_pull "$@" ;;
    run) cmd_run "$@" ;;
    -h|--help|help) usage ;;
    *) echo "Unknown subcommand: $sub" >&2; usage; exit 1 ;;
  esac
}

main "$@"
