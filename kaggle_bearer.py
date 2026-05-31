"""Minimal Kaggle client using Bearer auth — for the new KGAT_ tokens.

Kaggle's new KGAT_ API tokens authenticate via `Authorization: Bearer <token>`,
NOT the legacy Basic auth (username:key) that kaggle.json + the kaggle CLI use.
This client speaks Bearer so we can download datasets + competition data with a
KGAT_ token. Reads the token from ~/.kaggle/kaggle.json ("key" field).

Usage:
    python3 kaggle_bearer.py whoami
    python3 kaggle_bearer.py comp-files <competition-slug>
    python3 kaggle_bearer.py dataset <owner>/<dataset-slug> ./out
    python3 kaggle_bearer.py comp-download <competition-slug> ./comp_data
"""
import json, os, sys, urllib.request, urllib.error, zipfile, io

API = "https://www.kaggle.com/api/v1"


def _token() -> str:
    p = os.path.expanduser("~/.kaggle/kaggle.json")
    return json.load(open(p))["key"]


def _req(path: str, raw: bool = False):
    req = urllib.request.Request(API + path)
    req.add_header("Authorization", "Bearer " + _token())
    resp = urllib.request.urlopen(req, timeout=120)
    data = resp.read()
    return data if raw else json.loads(data)


def whoami():
    # Authenticated probe — competitions/list 200 means the token is good.
    try:
        _req("/competitions/list?page=1", raw=True)
        print("✅ Bearer auth OK")
        return True
    except urllib.error.HTTPError as e:
        print(f"❌ {e.code} {e.reason}")
        return False


def comp_files(comp: str):
    info = _req(f"/competitions/data/list/{comp}")
    files = info if isinstance(info, list) else info.get("files", info)
    print(f"=== {comp}: {len(files) if hasattr(files,'__len__') else '?'} files ===")
    for f in (files if isinstance(files, list) else [])[:50]:
        name = f.get("name") or f.get("ref") or f
        size = f.get("totalBytes") or f.get("size") or ""
        print(f"  {name}  {size}")


def _download_zip(path: str, dest: str, label: str):
    os.makedirs(dest, exist_ok=True)
    url = API + path
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + _token())
    print(f"[dl] {label} …", flush=True)
    with urllib.request.urlopen(req, timeout=600) as r:
        blob = r.read()
    print(f"[dl] received {len(blob)/1e6:.1f} MB", flush=True)
    # Response is a zip (datasets) or may be a single file. Try unzip; else save raw.
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            z.extractall(dest)
            print(f"[dl] extracted {len(z.namelist())} files → {dest}")
    except zipfile.BadZipFile:
        out = os.path.join(dest, label.replace("/", "_") + ".bin")
        open(out, "wb").write(blob)
        print(f"[dl] not a zip; saved raw → {out}")


def dataset(ref: str, dest: str):
    owner, slug = ref.split("/", 1)
    _download_zip(f"/datasets/download/{owner}/{slug}", dest, f"dataset {ref}")


def comp_download(comp: str, dest: str):
    _download_zip(f"/competitions/data/download-all/{comp}", dest, f"competition {comp}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "whoami"
    if cmd == "whoami":
        sys.exit(0 if whoami() else 1)
    elif cmd == "comp-files":
        comp_files(sys.argv[2])
    elif cmd == "dataset":
        dataset(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "./out")
    elif cmd == "comp-download":
        comp_download(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "./comp_data")
    else:
        print(f"unknown command: {cmd}")
        sys.exit(2)
