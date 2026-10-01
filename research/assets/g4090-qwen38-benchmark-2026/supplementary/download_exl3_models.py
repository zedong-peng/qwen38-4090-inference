#!/usr/bin/env python3
"""Download pinned EXL3 manifests through hf-mirror, checking LFS SHA256 and git blob IDs."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import quote

ROOT = Path.home() / "qwen38-4090"
MANIFESTS = [
    "Qwen3.8-27B-DFlash2-EXL3-4.00bpw-manifest.json",
    "Qwen3.8-27B-EXL3-4.00bpw-manifest.json",
]


def digest_file(path, algorithm, git_blob=False):
    digest = hashlib.new(algorithm)
    if git_blob:
        digest.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def matches(path, entry):
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return False
    expected = entry.get("lfs", {}).get("oid") or entry["oid"]
    actual = digest_file(path, "sha256" if entry.get("lfs") else "sha1", not entry.get("lfs"))
    return actual == expected


def main():
    results = []
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    endpoint = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com").rstrip("/")
    for filename in MANIFESTS:
        manifest = json.loads((ROOT / filename).read_text())
        destination = ROOT / "models" / manifest["repo_id"].split("/", 1)[1]
        destination.mkdir(parents=True, exist_ok=True)
        verified = []
        for entry in manifest["files"]:
            if entry.get("type") != "file":
                continue
            relative = Path(entry["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Manifest path escapes model directory")
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"{endpoint}/{manifest['repo_id']}/resolve/{manifest['revision']}/{quote(entry['path'], safe='/')}"
            if not matches(path, entry):
                partial = path.with_name(path.name + ".part")
                args = ["curl", "-fL", "--retry", "5", "--retry-all-errors", "--connect-timeout", "20",
                        "--max-time", "7200", "--silent", "--show-error", "-C", "-", "-o", str(partial), url]
                print("Downloading", manifest["repo_id"], entry["path"], entry["size"], flush=True)
                subprocess.run(args, check=True)
                if not matches(partial, entry):
                    raise RuntimeError(f"Size or digest mismatch: {entry['path']}")
                partial.rename(path)
            verified.append({"path": entry["path"], "bytes": path.stat().st_size,
                             "sha256": entry.get("lfs", {}).get("oid") or digest_file(path, "sha256"),
                             "expected_oid": entry.get("lfs", {}).get("oid") or entry["oid"],
                             "oid_type": "lfs_sha256" if entry.get("lfs") else "git_blob_sha1"})
            print("Verified", manifest["repo_id"], entry["path"], flush=True)
        results.append({"repo_id": manifest["repo_id"], "revision": manifest["revision"],
                        "endpoint": endpoint, "directory": str(destination), "files": verified})
        (ROOT / "results/exl3-model-downloads.json").write_text(json.dumps(results, indent=2) + "\n")
    print("Both pinned EXL3 model downloads verified", flush=True)


if __name__ == "__main__":
    main()
