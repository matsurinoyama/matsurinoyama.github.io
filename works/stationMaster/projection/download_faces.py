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
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        req = Request(url, headers={'User-Agent': 'python-urllib/3'})
        with urlopen(req, timeout=timeout) as r:
            import json
            return json.load(r)


def download_file_requests(session, url, dest_path, timeout=60, retries=2):
    tmp = dest_path + '.tmp'
    for attempt in range(retries + 1):
        try:
            with session.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                with open(tmp, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            os.replace(tmp, dest_path)
            return True
        except Exception as e:
            last_err = e
    print('Failed to download (requests) ', url, last_err)
    return False


def download_file_urllib(url, dest_path, timeout=60):
    tmp = dest_path + '.tmp'
    req = Request(url, headers={'User-Agent': 'python-urllib/3'})
    with urlopen(req, timeout=timeout) as r, open(tmp, 'wb') as f:
        shutil.copyfileobj(r, f)
    os.replace(tmp, dest_path)


def needs_download(session, url, dest):
    if not os.path.exists(dest):
        return True
    try:
        head = session.head(url, allow_redirects=True, timeout=10)
        remote_len = int(head.headers.get('Content-Length') or 0)
        local_len = os.path.getsize(dest)
        if remote_len != 0 and remote_len != local_len:
            return True
    except Exception:
        return False
    return False


def get_next_available_number(directory):
    """Find the next available aligned_N number in the directory."""
    max_num = 0
    if os.path.exists(directory):
        for fn in os.listdir(directory):
            if fn.lower().startswith('aligned_'):
                try:
                    # Extract number from aligned_N.ext
                    base = os.path.splitext(fn)[0]
                    num_str = base.split('_')[1]
                    num = int(num_str)
                    max_num = max(max_num, num)
                except (ValueError, IndexError):
                    continue
    return max_num + 1


def get_local_filename(original_fn, directory):
    """
    If a file with the same name exists locally, generate a new sequential name.
    Otherwise return the original filename.
    """
    dest = os.path.join(directory, original_fn)
    if not os.path.exists(dest):
        return original_fn
    
    # File exists, need to generate new sequential name
    ext = os.path.splitext(original_fn)[1]  # e.g., .jpg, .jpeg, .png
    next_num = get_next_available_number(directory)
    new_fn = f"aligned_{next_num}{ext}"
    print(f"File {original_fn} already exists locally, renaming to {new_fn}")
    return new_fn


def main(workers=4):
    print('Querying index:', FACES_INDEX_URL)
    try:
        items = fetch_json(FACES_INDEX_URL)
    except Exception as e:
        print('Failed to fetch index:', e)
        return

    if not isinstance(items, list):
        print('Index response is not a list; aborting')
        return

    tasks = []
    for it in items:
        fn = it.get('filename') if isinstance(it, dict) else None
        url = it.get('url') if isinstance(it, dict) else None
        if not fn or not url:
            continue
        # Check if file exists and get appropriate local filename
        local_fn = get_local_filename(fn, OUT_DIR)
        dest = os.path.join(OUT_DIR, local_fn)
        tasks.append((local_fn, url, dest))

    # Try parallel downloads with requests if available
    try:
        import requests
        session = requests.Session()
        downloaded = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {}
            for fn, url, dest in tasks:
                # Always download since we've already determined the correct filename
                futures[ex.submit(download_file_requests, session, url, dest)] = fn
            for fut in as_completed(futures):
                fn = futures[fut]
                try:
                    ok = fut.result()
                    if ok:
                        print('Downloaded', fn)
                        downloaded += 1
                    else:
                        print('Failed', fn)
                except Exception as e:
                    print('Exception downloading', fn, e)
        print('Done. downloaded=', downloaded)
        return
    except Exception:
        # fallback to urllib sequential downloader
        pass

    # urllib fallback (sequential)
    downloaded = 0
    for fn, url, dest in tasks:
        # Always download since we've already determined the correct filename
        print('Downloading', fn)
        try:
            download_file_urllib(url, dest)
            downloaded += 1
        except Exception as e:
            print('Failed to download', fn, e)
    print('Done. downloaded=', downloaded)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=6, help='number of parallel download workers')
    args = parser.parse_args()
    main(workers=args.workers)
