#!/usr/bin/env python3
"""Triage a Dependabot PR: is the proposed version already shipped by
Kaggle/docker-python (and, for competitions/hearth, within uv's exclude-newer
cutoff and not a major bump)? Prints a JSON verdict. Stdlib only; needs `gh`."""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

DP_IMAGE = "gcr.io/kaggle-images/python:latest"
HEARTH_PYPROJECT = "competitions/hearth/pyproject.toml"

TITLE_RE = re.compile(
    r"Bump\s+(?P<pkg>\S+)\s+from\s+(?P<old>\S+)\s+to\s+(?P<new>\S+)"
    r"(?:\s+in\s+(?P<dir>\S+))?", re.IGNORECASE)
JS_PKGS = {"vitest", "vite", "ws", "eslint", "prettier", "typescript", "react",
           "react-dom", "next", "axios", "webpack", "rollup", "jest", "esbuild"}


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_version(v):
    m = re.match(r"v?(\d+(?:\.\d+)*)", v.strip()) if v else None
    return tuple(int(x) for x in m.group(1).split(".")) if m else ()


def version_le(a, b):
    """True if version a <= version b, comparing numeric release segments."""
    pa, pb = parse_version(a), parse_version(b)
    n = max(len(pa), len(pb))
    return pa + (0,) * (n - len(pa)) <= pb + (0,) * (n - len(pb))


def is_major_bump(old, new):
    po, pn = parse_version(old), parse_version(new)
    return bool(po and pn and po[0] != pn[0])


def within_cutoff(upload_iso, cutoff_iso):
    """True if no cutoff applies or the upload happened on/before the cutoff."""
    def at(s):
        d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    if not cutoff_iso:
        return True
    if not upload_iso:
        return False
    return at(upload_iso) <= at(cutoff_iso)


def _gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def _fetch(repo, path):
    """Raw file contents from the repo's default branch."""
    return _gh("api", f"repos/{repo}/contents/{path}",
               "-H", "Accept: application/vnd.github.raw")


def docker_python_versions():
    """Get all installed packages from the live docker-python image."""
    try:
        out = subprocess.run(
            ["docker", "run", "--rm", DP_IMAGE, "pip", "list", "--format=freeze"],
            capture_output=True, text=True, check=True, timeout=120).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    pkgs = {}
    for line in out.strip().splitlines():
        if "==" in line:
            name, ver = line.split("==", 1)
            pkgs[normalize(name.strip())] = ver.strip()
    return pkgs


def exclude_newer_date(repo, directory):
    """The hearth exclude-newer cutoff, only when the PR targets competitions/hearth."""
    if repo != "Kaggle/competitions" or "hearth" not in (directory or ""):
        return None
    try:
        text = _fetch(repo, HEARTH_PYPROJECT)
    except subprocess.CalledProcessError:
        return None
    m = re.search(r"""exclude-newer\s*=\s*["']([^"']+)["']""", text)
    return m.group(1) if m else None


def pypi_upload_time(package, version):
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.load(resp)
    except Exception:
        return None
    src = (data.get("urls") or [data.get("info", {})])[0]
    return src.get("upload_time_iso_8601") or src.get("upload_time")


def triage(repo, pr, versions=None):
    title = json.loads(_gh("pr", "view", str(pr), "-R", repo, "--json", "title"))["title"]
    m = TITLE_RE.search(title or "")
    if not m:
        return {"verdict": "needs-attention", "package": None, "version": None,
                "reason": f"could not parse Dependabot title: {title!r}"}
    pkg, old, new = m.group("pkg"), m.group("old"), m.group("new")
    out = {"verdict": "needs-attention", "package": pkg, "version": new, "reason": ""}
    directory = m.group("dir") or ""
    if repo == "Kaggle/competitions-prep" and ("closed" in directory or "never_launched" in directory):
        out.update(verdict="skip-obsolete",
                   reason="targets obsolete directory (closed/never_launched) — safe to close")
        return out
    if pkg.startswith("@") or pkg.lower() in JS_PKGS:
        out.update(verdict="skip-js", reason="JS package — no docker-python baseline, review manually")
        return out

    reasons = []
    if versions is None:
        versions = docker_python_versions()
    key = normalize(pkg)
    shipped = versions.get(key)
    if key not in versions:
        reasons.append("package not in docker-python")
    elif shipped and not version_le(new, shipped):
        reasons.append(f"docker-python pins {shipped}, older than proposed {new}")
    if is_major_bump(old, new):
        reasons.append(f"major version bump ({old} -> {new})")
    cutoff = exclude_newer_date(repo, m.group("dir"))
    if cutoff and not within_cutoff(pypi_upload_time(key, new), cutoff):
        reasons.append(f"upload is after hearth exclude-newer cutoff {cutoff}")

    if reasons:
        out["reason"] = "; ".join(reasons)
    else:
        out["verdict"] = "auto-approve"
        out["reason"] = (f"docker-python pins {shipped} >= proposed {new}" if shipped
                         else "already shipped in docker-python (tracks latest)")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, help="e.g. Kaggle/competitions")
    args = p.parse_args(argv)
    try:
        prs = json.loads(_gh("pr", "list", "-R", args.repo,
                             "--author", "app/dependabot", "--state", "open",
                             "--json", "number,title"))
        versions = docker_python_versions()
        result = [triage(args.repo, pr["number"], versions) for pr in prs]
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"gh error: {e.stderr or e}\n")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
