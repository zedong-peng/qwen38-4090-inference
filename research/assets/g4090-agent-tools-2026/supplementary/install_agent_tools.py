#!/usr/bin/env python3
"""Pinned user-only Linux x86_64 agent-tool installer; does not configure providers."""
import hashlib
import json
import os
import platform
import subprocess
import tarfile
import tempfile
from pathlib import Path

NODE_VERSION = "v24.21.0"
NODE_SHA256 = "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6"
PACKAGES = ["@anthropic-ai/claude-code@2.1.286", "@openai/codex@0.159.2", "opencode-ai@1.18.33"]
RELEASES = [
    ("SaladDay/cc-switch-cli", "v5.10.5", "cc-switch-cli-linux-x64-musl.tar.gz",
     "feda4dca0ecf01ec90708141cc346972683c27c1097fba22235c5022143f80ed"),
    ("farion1231/cc-switch", "v3.20.4", "CC-Switch-v3.20.4-Linux-x86_64.AppImage",
     "c8d66d8193fd00fd12239bd06a8c50f517badbf50d9020a4662e95e907b318ef"),
]


def run(args, **kwargs):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download(url, destination, expected):
    if destination.is_file() and sha256(destination) == expected:
        return
    partial = destination.with_suffix(destination.suffix + ".part")
    run(["curl", "-fL", "--retry", "3", "--connect-timeout", "20", "--max-time", "1200",
         "--silent", "--show-error", "-o", partial, url])
    actual = sha256(partial)
    if actual != expected:
        raise RuntimeError(f"Checksum mismatch for {destination.name}: {actual}")
    partial.rename(destination)


def link_without_overwrite(target, link):
    if link.is_symlink() and link.resolve() == target.resolve():
        return
    if link.exists() or link.is_symlink():
        raise RuntimeError(f"Preserving existing launcher: {link}")
    link.symlink_to(target)


def extract_archive(archive, target, top_level=None):
    if target.exists():
        return
    with tarfile.open(archive) as handle:
        members = handle.getmembers()
        if len(members) > 100000 or sum(member.size for member in members) > 2 * 1024**3:
            raise RuntimeError("Archive expansion limit exceeded")
        for member in members:
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or not (
                    member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise RuntimeError(f"Unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                link_target = Path(member.linkname)
                relative = name.parent / link_target if member.issym() else link_target
                normalized = Path(os.path.normpath(str(relative)))
                if link_target.is_absolute() or normalized.is_absolute() or ".." in normalized.parts:
                    raise RuntimeError(f"Archive link escapes extraction root: {member.name}")
    with tempfile.TemporaryDirectory(prefix="agent-tools-extract-", dir=target.parent) as temporary:
        content = Path(temporary) / "content"
        content.mkdir()
        run(["tar", "-xf", archive, "-C", content])
        source = content / top_level if top_level else content
        source.rename(target)


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("This pinned installer targets Linux x86_64 only")
    task_home = Path.home()
    base = task_home / ".local/share/g4090-agent-tools"
    downloads = base / "downloads"
    prefix = base / "npm"
    local_bin = task_home / ".local/bin"
    for directory in [downloads, prefix, local_bin]:
        directory.mkdir(parents=True, exist_ok=True)

    node_name = f"node-{NODE_VERSION}-linux-x64"
    node_archive = downloads / f"{node_name}.tar.xz"
    download(f"https://nodejs.org/dist/{NODE_VERSION}/{node_archive.name}", node_archive, NODE_SHA256)
    node_dir = base / node_name
    extract_archive(node_archive, node_dir, top_level=node_name)
    env = os.environ.copy()
    env["PATH"] = f"{node_dir}/bin:{local_bin}:" + env.get("PATH", "")
    env["npm_config_cache"] = str(base / "npm-cache")
    env["CC_SWITCH_CONFIG_DIR"] = str(base / "cc-switch-smoke-config")
    # A dedicated prefix and cache leave existing npm configuration and credentials intact.
    run([node_dir / "bin/npm", "install", "--global", "--prefix", prefix,
         "--registry=https://registry.npmjs.org", "--no-audit", "--no-fund",
         "--allow-scripts=@anthropic-ai/claude-code,opencode-ai", *PACKAGES], env=env)

    for name in ["node", "npm", "npx"]:
        link_without_overwrite(node_dir / "bin" / name, local_bin / name)
    for name in ["claude", "codex", "opencode"]:
        link_without_overwrite(prefix / "bin" / name, local_bin / name)

    artifacts = []
    for repo, tag, name, digest in RELEASES:
        path = downloads / name
        url = f"https://github.com/{repo}/releases/download/{tag}/{name}"
        download(url, path, digest)
        artifacts.append({"repository": repo, "version": tag, "filename": name,
                          "url": url, "sha256": digest, "bytes": path.stat().st_size})
        if repo.endswith("cc-switch-cli"):
            destination = base / f"cc-switch-cli-{tag}"
            extract_archive(path, destination)
            candidates = list(destination.rglob("cc-switch"))
            binaries = [candidate for candidate in candidates if candidate.is_file()]
            if len(binaries) != 1:
                raise RuntimeError("Unexpected cc-switch-cli archive layout")
            binary = binaries[0]
            binary.chmod(0o755)
            link_without_overwrite(binary, local_bin / "cc-switch")
        else:
            path.chmod(0o755)
            link_without_overwrite(path, local_bin / "cc-switch-gui")

    # Bash reads .bashrc for remote noninteractive SSH commands. Put the PATH block
    # before Ubuntu's interactive-shell early return; preserve the original contents.
    marker = "# g4090-agent-tools PATH (2026-10-01)"
    path_block = marker + '\ncase ":$PATH:" in\n  *":$HOME/.local/bin:"*) ;;\n  *) export PATH="$HOME/.local/bin:$PATH" ;;\nesac\n'
    for filename in [".bashrc", ".profile"]:
        rc = task_home / filename
        contents = rc.read_text() if rc.exists() else ""
        if marker not in contents:
            backup = base / (filename.lstrip(".") + ".before-agent-tools")
            if not backup.exists():
                backup.write_text(contents)
                backup.chmod(0o600)
            rc.write_text(path_block + "\n" + contents)

    (base / "env.sh").write_text('export PATH="$HOME/.local/bin:$PATH"\n')
    versions = {}
    for name in ["node", "npm", "claude", "codex", "opencode", "cc-switch"]:
        result = run([local_bin / name, "--version"], env=env, text=True, capture_output=True)
        versions[name] = result.stdout.strip()
        print(name + ": " + versions[name], flush=True)
    manifest = {"date": "2026-10-01", "platform": "Linux x86_64", "packages": PACKAGES,
                "node": {"version": NODE_VERSION, "sha256": NODE_SHA256},
                "release_artifacts": artifacts, "versions": versions,
                "gui_status": "downloaded, no graphical session available", "base": str(base)}
    (base / "install-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("Installation complete; provider authentication has not been configured.", flush=True)


if __name__ == "__main__":
    main()
