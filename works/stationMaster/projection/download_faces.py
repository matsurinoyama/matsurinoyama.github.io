#!/usr/bin/env python3
"""
Download new/updated face images from the Heroku app's `/faces` JSON endpoint.
This script downloads only files that are missing locally (or whose size differs).
Files are saved into the repository-level `faces/` folder (works/stationMaster/faces).
Usage: python3 download_faces.py
"""
import os
import shutil
import zipfile
from urllib.request import urlopen, Request

FACES_INDEX_URL = "https://eiden.03080.jp/faces"
# Place downloaded faces in the repository-level faces/ folder (works/stationMaster/faces)
BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'faces'))

os.makedirs(OUT_DIR, exist_ok=True)

def fetch_json(url, timeout=20):
    try:
        import requests
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        # fallback to urllib
        from urllib.request import urlopen, Request
        req = Request(url, headers={'User-Agent': 'python-urllib/3'})
        with urlopen(req, timeout=timeout) as r:
            import json
            return json.load(r)

os.makedirs(OUT_DIR, exist_ok=True)

def download_file(url, dest_path, timeout=60):
    tmp = dest_path + '.tmp'
    try:
        import requests
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(tmp, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception:
        # fallback to urllib
        from urllib.request import urlopen, Request
        req = Request(url, headers={'User-Agent': 'python-urllib/3'})
        with urlopen(req, timeout=timeout) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f)
    os.replace(tmp, dest_path)


def main():
    print('Querying index:', FACES_INDEX_URL)
    try:
        items = fetch_json(FACES_INDEX_URL)
    except Exception as e:
        print('Failed to fetch index:', e)
        return

    if not isinstance(items, list):
        print('Index response is not a list; aborting')
        return

    downloaded = 0
    for it in items:
        # item expected to contain 'filename' and 'url'
        fn = it.get('filename') if isinstance(it, dict) else None
        url = it.get('url') if isinstance(it, dict) else None
        if not fn or not url:
            continue
        dest = os.path.join(OUT_DIR, fn)
        # download if missing or size differs
        need = False
        if not os.path.exists(dest):
            need = True
        else:
            try:
                import requests
                head = requests.head(url, allow_redirects=True, timeout=10)
                remote_len = int(head.headers.get('Content-Length') or 0)
                local_len = os.path.getsize(dest)
                if remote_len != 0 and remote_len != local_len:
                    need = True
            except Exception:
                # conservative: skip size check if head fails
                pass

        if need:
            print('Downloading', fn)
            try:
                download_file(url, dest)
                downloaded += 1
            except Exception as e:
                print('Failed to download', fn, e)

    print('Done. downloaded=', downloaded)

if __name__ == '__main__':
    print(os.getcwd())
    print(os.listdir('.')[:50])
    main()
