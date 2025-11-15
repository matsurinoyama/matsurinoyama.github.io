#!/usr/bin/env python3
"""
Download new/updated face images from the Heroku app's `/faces` JSON endpoint.
This script downloads only files that are missing locally (or whose size differs).
Files are saved into the repository-level `faces/` folder (works/stationMaster/faces).
Usage: python3 download_faces.py
"""
import os
import shutil
import json
from urllib.request import urlopen, Request
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

FACES_INDEX_URL = "https://eiden.03080.jp/faces"
# Place downloaded faces in the repository-level faces/ folder (works/stationMaster/faces)
BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'faces'))
MANIFEST_PATH = os.path.join(OUT_DIR, '.faces_manifest.json')

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
    last_err = None
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
        # If HEAD fails, assume not changed to avoid churn
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


def load_manifest():
    try:
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_manifest(data):
    try:
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print('Warning: could not save manifest:', e)


def get_remote_meta(session, url):
    try:
        head = session.head(url, allow_redirects=True, timeout=10)
        length = int(head.headers.get('Content-Length') or 0)
        etag = head.headers.get('ETag') or head.headers.get('Etag') or head.headers.get('etag')
        return length, etag
    except Exception:
        return 0, None


def main(workers=4, append_new=False):
    print('Querying index:', FACES_INDEX_URL)
    try:
        items = fetch_json(FACES_INDEX_URL)
    except Exception as e:
        print('Failed to fetch index:', e)
        return

    if not isinstance(items, list):
        print('Index response is not a list; aborting')
        return

    # Try parallel downloads with requests if available
    try:
        import requests
        session = requests.Session()

        manifest = load_manifest()
        tasks = []  # (fn_to_report, url, dest_path)
        post_update = []  # (remote_fn, dest_basename, remote_len, remote_etag)
        for it in items:
            fn = it.get('filename') if isinstance(it, dict) else None
            url = it.get('url') if isinstance(it, dict) else None
            if not fn or not url:
                continue

            dest_canonical = os.path.join(OUT_DIR, fn)
            ext = os.path.splitext(fn)[1]
            remote_len, remote_etag = get_remote_meta(session, url)
            rec = manifest.get(fn, {})

            local_exists = os.path.exists(dest_canonical)
            local_len = os.path.getsize(dest_canonical) if local_exists else -1
            # If file is in manifest, only trust ETag/length (ignore mtime changes from reads)
            if rec:
                etag_changed = (remote_etag is not None and rec.get('etag') != remote_etag)
                length_changed = (remote_len != 0 and rec.get('length', -1) != remote_len)
            else:
                # New entry: compare against local file if present
                etag_changed = False
                length_changed = (remote_len != 0 and local_exists and remote_len != local_len)
            is_new = not local_exists
            is_changed = (etag_changed or length_changed)

            if is_new:
                tasks.append((fn, url, dest_canonical))
                post_update.append((fn, os.path.basename(dest_canonical), remote_len, remote_etag))
            elif is_changed:
                if append_new:
                    new_name = f"aligned_{get_next_available_number(OUT_DIR)}{ext}"
                    new_path = os.path.join(OUT_DIR, new_name)
                    tasks.append((new_name, url, new_path))
                    post_update.append((fn, new_name, remote_len, remote_etag))
                    print(f"Changed {fn} -> saving as new {new_name}")
                else:
                    archive_name = f"aligned_{get_next_available_number(OUT_DIR)}{ext}"
                    archive_path = os.path.join(OUT_DIR, archive_name)
                    try:
                        os.rename(dest_canonical, archive_path)
                        print(f"Existing {fn} differs, archived to {archive_name}")
                    except Exception as e:
                        print(f"Warning: could not archive {fn} -> {archive_name}: {e}")
                    tasks.append((fn, url, dest_canonical))
                    post_update.append((fn, os.path.basename(dest_canonical), remote_len, remote_etag))
            else:
                print('Up-to-date', fn)

        downloaded = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {}
            for fn, url, dest in tasks:
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
        if downloaded > 0 and post_update:
            for remote_fn, saved_as, rlen, retag in post_update:
                manifest[remote_fn] = {
                    'saved_as': saved_as,
                    'length': rlen,
                    'etag': retag,
                }
            save_manifest(manifest)
        return
    except Exception:
        # fallback to urllib sequential downloader
        pass

    # urllib fallback (sequential)
    downloaded = 0
    for it in items:
        fn = it.get('filename') if isinstance(it, dict) else None
        url = it.get('url') if isinstance(it, dict) else None
        if not fn or not url:
            continue
        dest = os.path.join(OUT_DIR, fn)
        if os.path.exists(dest):
            print('Up-to-date (fallback)', fn)
            continue
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
    parser.add_argument('--append-new', action='store_true', help='when same-named remote file changes, save as next aligned_N instead of replacing canonical')
    args = parser.parse_args()
    main(workers=args.workers, append_new=args.append_new)
