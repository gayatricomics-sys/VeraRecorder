"""Pack the Windows offline kit into a single zip.

Usage: python3 offline/make-windows-zip.py <repo root> <output.zip>

Contents (all under a top-level "VeraRecorder/" folder):
  - every file tracked in git, except the macOS-only Python wheels
    (python/wheels/*.whl; the Windows ones live in python/wheels/windows/)
  - the Windows-only kit produced by prepare-offline-kit.sh:
      offline/installers/, offline/npm-cache/, offline/electron-cache/,
      offline/electron-builder-cache/, offline/KIT_VERSIONS.txt,
      python/drivers/ (Chrome for Testing + ChromeDriver for win64)
"""
import os
import subprocess
import sys
import zipfile

KIT_PATHS = [
    "offline/installers",
    "offline/npm-cache",
    "offline/electron-cache",
    "offline/electron-builder-cache",
    "offline/KIT_VERSIONS.txt",
    "python/drivers",
]


def is_mac_only(rel: str) -> bool:
    parts = rel.split("/")
    # python/wheels/<file>.whl  (macOS arm64, Python 3.9) -- not python/wheels/windows/...
    return len(parts) == 3 and parts[:2] == ["python", "wheels"] and parts[2].endswith(".whl")


def main() -> int:
    root, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    tracked = subprocess.run(
        ["git", "-C", root, "ls-files", "-z"], check=True, capture_output=True
    ).stdout.decode().split("\0")
    files = {f for f in tracked if f and not is_mac_only(f) and os.path.isfile(os.path.join(root, f))}

    for kit in KIT_PATHS:
        full = os.path.join(root, kit)
        if not os.path.exists(full):
            print(f"ERROR: {kit} missing - run offline/prepare-offline-kit.sh first", file=sys.stderr)
            return 1
        if os.path.isfile(full):
            files.add(kit)
            continue
        for dirpath, _, names in os.walk(full):
            for n in names:
                files.add(os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/"))

    mac_markers = ("darwin", ".dmg", ".app/", "mac-arm64", "mac-x64")
    leaked = sorted(f for f in files if f.startswith(("offline/", "python/drivers/"))
                    and any(m in f.lower() for m in mac_markers))
    if leaked:
        print("ERROR: macOS files found in the Windows kit:", *leaked[:10], sep="\n  ", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".part"
    total = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for rel in sorted(files):
            full = os.path.join(root, rel)
            total += os.path.getsize(full)
            # Already-compressed archives/installers: store as-is (faster, no gain).
            stored = rel.lower().endswith((".zip", ".7z", ".gz", ".msi", ".exe", ".whl", ".tgz"))
            z.write(full, "VeraRecorder/" + rel,
                    compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
    os.replace(tmp, out)
    print(f"  {len(files)} files, {total / 1e6:.0f} MB uncompressed -> "
          f"{os.path.getsize(out) / 1e6:.0f} MB {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
