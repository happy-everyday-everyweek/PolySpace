#!/usr/bin/env python3
"""
Build Alpine Linux rootfs with Python and backend dependencies for Android.
Supports aarch64 and x86_64 architectures.
Runs on Windows without Docker/WSL.

Uses pip download to resolve and download all Python dependencies
including transitive dependencies for the target platform.
"""

import os
import sys
import tarfile
import io
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ALPINE_VERSION = "v3.21"
ALPINE_MIRROR = "https://dl-cdn.alpinelinux.org/alpine"

ASSETS_DIR = r"d:\PolySpace\android\app\src\main\assets"
BACKEND_DIR = r"d:\PolySpace\backend"

WANTED_APK_PACKAGES = [
    "python3",
    "py3-pip",
    "ca-certificates",
    "libssl3",
    "libcrypto3",
    "zlib",
    "nodejs-current",
    "npm",
    "pnpm",
]

MOBILE_PIP_PACKAGES = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "aiosqlite>=0.20",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "python-multipart>=0.0.9",
    "websockets>=12.0",
    "litellm>=1.50",
]

NODE_PROJECT_EXCLUDES = {
    "node_modules", ".git", ".next", ".nuxt", "dist", ".cache",
    ".turbo", "coverage", ".DS_Store", "tmp", ".env.local",
}


def _copy_node_project(src_dir, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)

    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in NODE_PROJECT_EXCLUDES]
        rel_root = os.path.relpath(root, src_dir)
        if rel_root == ".":
            target_root = dest_dir
        else:
            target_root = os.path.join(dest_dir, rel_root)
        os.makedirs(target_root, exist_ok=True)
        for f in files:
            if f in (".DS_Store",):
                continue
            src_file = os.path.join(root, f)
            dst_file = os.path.join(target_root, f)
            shutil.copy2(src_file, dst_file)


def download_file(url, dest=None, timeout=120):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "PolySpace-BuildScript/1.0")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if dest:
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
            return dest
        else:
            return resp.read()


def parse_apkindex(data):
    packages = {}
    current_pkg = {}

    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
        for member in tar.getmembers():
            if member.name in ("APKINDEX", "./APKINDEX"):
                f = tar.extractfile(member)
                content = f.read().decode("utf-8")

                for line in content.split("\n"):
                    if line.startswith("C:"):
                        if current_pkg.get("P"):
                            packages[current_pkg["P"]] = current_pkg
                        current_pkg = {}
                    elif ":" in line and line[1] == ":":
                        key = line[0]
                        val = line[2:]
                        if key == "P":
                            current_pkg["P"] = val
                        elif key == "V":
                            current_pkg["V"] = val
                        elif key == "A":
                            current_pkg["A"] = val
                        elif key == "D":
                            current_pkg["D"] = val.split() if val else []
                        elif key == "p":
                            current_pkg["p"] = val.split() if val else []
                        elif key == "S":
                            current_pkg["S"] = int(val) if val else 0
                    elif line == "":
                        if current_pkg.get("P"):
                            packages[current_pkg["P"]] = current_pkg
                        current_pkg = {}

                if current_pkg.get("P"):
                    packages[current_pkg["P"]] = current_pkg

    return packages


def resolve_dependencies(all_packages, wanted_names):
    needed = {}
    to_process = list(wanted_names)
    processed = set()

    while to_process:
        pkg_name = to_process.pop(0)
        if pkg_name in processed:
            continue
        processed.add(pkg_name)

        pkg = all_packages.get(pkg_name)
        if not pkg:
            print(f"    Warning: package '{pkg_name}' not found in index")
            continue

        needed[pkg_name] = pkg

        for dep in pkg.get("D", []):
            if dep.startswith("so:"):
                provider_found = False
                for name, p in all_packages.items():
                    provides = p.get("p", [])
                    for prov in provides:
                        if prov.startswith(dep[3:]) or prov == dep[3:]:
                            if name not in processed:
                                to_process.append(name)
                            provider_found = True
                            break
                    if provider_found:
                        break
                if not provider_found:
                    so_name = dep[3:].split("=")[0].split(".so")[0]
                    for name, p in all_packages.items():
                        if name.startswith(so_name) and name not in processed:
                            to_process.append(name)
                            break
            elif dep.startswith("cmd:"):
                cmd_name = dep[4:].split("=")[0]
                for name, p in all_packages.items():
                    provides = p.get("p", [])
                    for prov in provides:
                        if prov.startswith(f"cmd:{cmd_name}"):
                            if name not in processed:
                                to_process.append(name)
                            break
            elif dep.startswith("!"):
                continue
            else:
                dep_name = dep.split("=")[0].split(">")[0].split("<")[0].split("~")[0]
                if dep_name not in processed:
                    to_process.append(dep_name)

    return needed


def download_apk_package(pkg, arch, repo_type="main"):
    name = pkg["P"]
    version = pkg["V"]
    filename = f"{name}-{version}.apk"
    url = f"{ALPINE_MIRROR}/{ALPINE_VERSION}/{repo_type}/{arch}/{filename}"

    try:
        data = download_file(url, timeout=60)
        return data
    except Exception as e:
        if repo_type == "main":
            return download_apk_package(pkg, arch, "community")
        print(f"    Failed to download {filename}: {e}")
        return None


def extract_apk_to_rootfs(apk_data, rootfs_dir):
    try:
        with tarfile.open(fileobj=io.BytesIO(apk_data), mode='r:gz') as tar:
            for member in tar.getmembers():
                if member.name.startswith(".PKGINFO") or member.name.startswith(".pre-") or member.name.startswith(".post-"):
                    continue
                tar.extract(member, rootfs_dir)
    except tarfile.ReadError:
        try:
            with tarfile.open(fileobj=io.BytesIO(apk_data), mode='r') as tar:
                for member in tar.getmembers():
                    if member.name.startswith(".PKGINFO") or member.name.startswith(".pre-") or member.name.startswith(".post-"):
                        continue
                    tar.extract(member, rootfs_dir)
        except Exception as e:
            print(f"    Warning: Could not extract APK package: {e}")


C_EXTENSION_PACKAGES = [
    "pydantic-core",
    "sqlalchemy",
    "greenlet",
    "PyYAML",
    "websockets",
    "httptools",
    "uvloop",
    "watchfiles",
    "tiktoken",
    "aiohttp",
    "multidict",
    "yarl",
    "frozenlist",
    "propcache",
    "cchardet",
    "charset-normalizer",
    "MarkupSafe",
    "regex",
    "rpds-py",
    "jiter",
    "tokenizers",
    "hf-xet",
]


def pip_download_wheels(packages, target_dir, platform_tag, python_abi="cp311"):
    """Download wheels using pip for the target platform."""
    os.makedirs(target_dir, exist_ok=True)

    print("    Pass 1: Downloading pure Python wheels (dependency resolution)...")
    cmd_pure = [
        sys.executable, "-m", "pip", "download",
        "--dest", target_dir,
        "--only-binary=:all:",
    ] + packages
    try:
        result = subprocess.run(cmd_pure, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"    Pure Python download warnings: {result.stderr[-300:]}")
    except Exception as e:
        print(f"    Pure Python download error: {e}")

    pure_count = len([f for f in os.listdir(target_dir) if f.endswith(".whl")])
    print(f"    Downloaded {pure_count} pure Python wheels")

    print("    Pass 2: Downloading musllinux wheels for C extension packages...")
    musl_platform = f"musllinux_1_2_{platform_tag}"
    manylinux_platform = f"manylinux2014_{platform_tag}"

    cmd_musl = [
        sys.executable, "-m", "pip", "download",
        "--dest", target_dir,
        "--only-binary=:all:",
        "--no-deps",
        "--platform", musl_platform,
        "--platform", manylinux_platform,
        "--implementation", "cp",
        "--abi", python_abi,
        "--python-version", "3.11",
    ] + C_EXTENSION_PACKAGES
    try:
        result = subprocess.run(cmd_musl, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"    musllinux download warnings: {result.stderr[-300:]}")
    except Exception as e:
        print(f"    musllinux download error: {e}")

    total_count = len([f for f in os.listdir(target_dir) if f.endswith(".whl")])
    new_count = total_count - pure_count
    print(f"    Downloaded {new_count} musllinux wheels ({total_count} total)")

    print("    Pass 3: Removing Windows-only wheels...")
    removed = 0
    for f in os.listdir(target_dir):
        if f.endswith(".whl") and "win_" in f and "musllinux" not in f and "manylinux" not in f and "none-any" not in f:
            os.remove(os.path.join(target_dir, f))
            removed += 1
    final_count = len([f for f in os.listdir(target_dir) if f.endswith(".whl")])
    print(f"    Removed {removed} Windows wheels, {final_count} wheels remaining")
    return final_count > 0


def build_rootfs(android_abi, output_path):
    alpine_arch = "aarch64" if android_abi == "arm64-v8a" else "x86_64"
    pip_arch_tag = "aarch64" if android_abi == "arm64-v8a" else "x86_64"

    print(f"\n{'='*60}")
    print(f"Building rootfs for {android_abi} (Alpine arch: {alpine_arch})")
    print(f"{'='*60}")

    rootfs_dir = os.path.join("D:\\tmp", f"rootfs_{alpine_arch}")
    if os.path.exists(rootfs_dir):
        shutil.rmtree(rootfs_dir)
    os.makedirs(rootfs_dir, exist_ok=True)

    print("\n[1/7] Downloading Alpine package indexes...")
    try:
        main_index_data = download_file(
            f"{ALPINE_MIRROR}/{ALPINE_VERSION}/main/{alpine_arch}/APKINDEX.tar.gz"
        )
        community_index_data = download_file(
            f"{ALPINE_MIRROR}/{ALPINE_VERSION}/community/{alpine_arch}/APKINDEX.tar.gz"
        )
    except Exception as e:
        print(f"Failed to download package indexes: {e}")
        return False

    print("[2/7] Parsing package indexes...")
    main_packages = parse_apkindex(main_index_data)
    community_packages = parse_apkindex(community_index_data)
    all_packages = {**main_packages, **community_packages}
    print(f"    Found {len(all_packages)} packages in repositories")

    print("[3/7] Resolving dependencies...")
    needed = resolve_dependencies(all_packages, WANTED_APK_PACKAGES)
    print(f"    Need {len(needed)} packages total")

    print("[4/7] Downloading and installing APK packages...")
    for pkg_name, pkg in needed.items():
        version = pkg.get("V", "?")
        size_kb = pkg.get("S", 0) / 1024
        print(f"    Installing: {pkg_name}-{version} ({size_kb:.0f} KB)")

        repo = "community" if pkg_name in community_packages else "main"
        apk_data = download_apk_package(pkg, alpine_arch, repo)
        if apk_data:
            extract_apk_to_rootfs(apk_data, rootfs_dir)
        else:
            print(f"    WARNING: Failed to install {pkg_name}")

    print("[5/7] Downloading and pre-installing Python wheels...")
    wheels_download_dir = os.path.join("D:\\tmp", f"wheels_{alpine_arch}")
    if os.path.exists(wheels_download_dir):
        shutil.rmtree(wheels_download_dir)
    os.makedirs(wheels_download_dir, exist_ok=True)

    pip_download_wheels(
        MOBILE_PIP_PACKAGES,
        wheels_download_dir,
        pip_arch_tag,
    )

    site_packages_dir = os.path.join(rootfs_dir, "usr/lib/python3.11/site-packages")
    os.makedirs(site_packages_dir, exist_ok=True)

    print("    Pre-installing wheels into site-packages...")
    wheel_files = [f for f in os.listdir(wheels_download_dir) if f.endswith(".whl")]
    for i, whl in enumerate(wheel_files):
        whl_path = os.path.join(wheels_download_dir, whl)
        try:
            with zipfile.ZipFile(whl_path, 'r') as zf:
                zf.extractall(site_packages_dir)
            print(f"    [{i+1}/{len(wheel_files)}] Installed: {whl}")
        except Exception as e:
            print(f"    [{i+1}/{len(wheel_files)}] Failed to install {whl}: {e}")

    dist_info_dirs = [d for d in os.listdir(site_packages_dir) if d.endswith(".dist-info")]
    print(f"    Pre-installed {len(dist_info_dirs)} packages into site-packages")

    # Keep empty tmp/wheels directory as compatibility marker
    # (wheels are pre-installed into site-packages at build time, no need to copy .whl files here)
    wheels_dest = os.path.join(rootfs_dir, "tmp/wheels")
    os.makedirs(wheels_dest, exist_ok=True)

    wheel_count = len(dist_info_dirs)
    print(f"    {wheel_count} packages pre-installed (no runtime pip install needed)")

    print("[6/7] Setting up backend code and configuration...")
    for d in ["proc", "sys", "dev", "tmp", "run",
              "home/polyspace/backend", "home/polyspace/data",
              "home/polyspace/open-design", "home/polyspace/nocobase",
              "var/run", "var/log"]:
        os.makedirs(os.path.join(rootfs_dir, d), exist_ok=True)

    resolv_conf = os.path.join(rootfs_dir, "etc/resolv.conf")
    with open(resolv_conf, "w") as f:
        f.write("nameserver 8.8.8.8\nnameserver 8.8.4.4\n")

    hosts_file = os.path.join(rootfs_dir, "etc/hosts")
    with open(hosts_file, "w") as f:
        f.write("127.0.0.1 localhost\n")

    start_sh = os.path.join(rootfs_dir, "home/polyspace/start.sh")
    with open(start_sh, "w") as f:
        f.write("""#!/bin/sh
export POLYSPACE_DATA_DIR=/home/polyspace/data
export POLYSPACE_HOST=0.0.0.0
export POLYSPACE_PORT=8000
export PATH=/usr/bin:/usr/local/bin:/home/polyspace/.local/bin:$PATH
export HOME=/home/polyspace
export LD_LIBRARY_PATH=/usr/lib:/usr/local/lib
export PYTHONPATH=/home/polyspace/backend:$PYTHONPATH

# Open Design daemon configuration
export POLYSPACE_API_URL=http://127.0.0.1:8000
export OPEN_DESIGN_PORT=3838
export OPEN_DESIGN_HOST=127.0.0.1

# NocoBase configuration
export NOCOBASE_PORT=13000
export NOCOBASE_HOST=127.0.0.1

# Install Node.js dependencies on first boot (if not already installed)
if [ -d /home/polyspace/open-design ] && [ ! -d /home/polyspace/open-design/node_modules ]; then
    echo "Installing open-design dependencies..."
    cd /home/polyspace/open-design
    pnpm install --frozen-lockfile 2>/dev/null || pnpm install 2>/dev/null || npm install 2>/dev/null || true
    echo "Building open-design..."
    pnpm run build 2>/dev/null || npm run build 2>/dev/null || true
    cd /home/polyspace
fi

if [ -d /home/polyspace/nocobase ] && [ ! -d /home/polyspace/nocobase/node_modules ]; then
    echo "Installing nocobase dependencies..."
    cd /home/polyspace/nocobase
    npm install 2>/dev/null || yarn install 2>/dev/null || true
    cd /home/polyspace
fi

# Start PolySpace backend (blocks until exit)
cd /home/polyspace/backend
exec /usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
""")

    if os.path.exists(BACKEND_DIR):
        backend_dest = os.path.join(rootfs_dir, "home/polyspace/backend")
        app_src = os.path.join(BACKEND_DIR, "app")
        if os.path.exists(app_src):
            if os.path.exists(os.path.join(backend_dest, "app")):
                shutil.rmtree(os.path.join(backend_dest, "app"))
            shutil.copytree(app_src, os.path.join(backend_dest, "app"))

        pyproject = os.path.join(BACKEND_DIR, "pyproject.toml")
        if os.path.exists(pyproject):
            shutil.copy2(pyproject, backend_dest)

    open_design_src = os.path.join(os.path.dirname(BACKEND_DIR), "open-design-main")
    open_design_dest = os.path.join(rootfs_dir, "home/polyspace/open-design")
    if os.path.isdir(open_design_src):
        print("    Copying open-design project...")
        _copy_node_project(open_design_src, open_design_dest)

    nocobase_src = os.path.join(os.path.dirname(BACKEND_DIR), "nocobase")
    nocobase_dest = os.path.join(rootfs_dir, "home/polyspace/nocobase")
    if os.path.isdir(nocobase_src):
        print("    Copying nocobase project...")
        _copy_node_project(nocobase_src, nocobase_dest)

    print("[7/7] Creating tarball...")
    print(f"    Output: {output_path}")
    with tarfile.open(output_path, "w:gz", compresslevel=6) as tar:
        tar.add(rootfs_dir, arcname=".")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"    Rootfs size: {size_mb:.2f} MB")

    shutil.rmtree(rootfs_dir)
    if os.path.exists(wheels_download_dir):
        shutil.rmtree(wheels_download_dir)

    return True


def main():
    print("PolySpace Android RootFS Builder")
    print("=" * 40)

    os.makedirs(ASSETS_DIR, exist_ok=True)

    aarch64_output = os.path.join(ASSETS_DIR, "alpine-rootfs-aarch64.tar.gz")
    x86_64_output = os.path.join(ASSETS_DIR, "alpine-rootfs-x86_64.tar.gz")

    if len(sys.argv) > 1:
        arch = sys.argv[1]
        if arch == "aarch64":
            build_rootfs("arm64-v8a", aarch64_output)
        elif arch == "x86_64":
            build_rootfs("x86_64", x86_64_output)
        elif arch == "both":
            build_rootfs("arm64-v8a", aarch64_output)
            build_rootfs("x86_64", x86_64_output)
        else:
            print(f"Unknown arch: {arch}. Use aarch64, x86_64, or both")
            sys.exit(1)
    else:
        build_rootfs("arm64-v8a", aarch64_output)
        build_rootfs("x86_64", x86_64_output)

    print("\n" + "=" * 40)
    print("Build complete!")
    for f in [aarch64_output, x86_64_output]:
        if os.path.exists(f):
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"  {os.path.basename(f)}: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
