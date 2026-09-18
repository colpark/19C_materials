"""Pooled sibling-library loader (rev2.1 D2 re-entry). Rules: rev21/pool/POOL_RULES.md (frozen).

Builds, from env/raw/siblings (fetching missing MEAD members by HTTP range reads into
env/raw/siblings/mead/):
  env/pool/plates/<plate_id>.npz   Q, xrd, xrd_comp, elements, substrate, annealT_C
  env/pool/episodes.jsonl          one episode per (plate, electrolyte run, illumination)
  rev21/pool/pool_ledger.json      per-plate status, counts, drops, totals, notes, completeness

Usage:  env/.venv/bin/python bench/pool_loader.py [--offline]
"""
from __future__ import annotations
import io, json, os, re, sys, time, zipfile, urllib.request, urllib.parse, threading
import concurrent.futures as cf
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "env", "raw", "siblings")
MEAD = os.path.join(RAW, "mead")
CENSUS = os.path.join(ROOT, "discovery", "siblings", "census")
OUT = os.path.join(ROOT, "env", "pool")
LEDGER = os.path.join(ROOT, "rev21", "pool", "pool_ledger.json")
OFFLINE = "--offline" in sys.argv
UA = {"User-Agent": "curl/8"}

# ----------------------------------------------------------------------------------------------
# Fetch layer: CaltechDATA record listing / search, remote zip members by HTTP range read.
# Every network answer is cached under env/raw/siblings/mead so a rebuild is offline-reproducible.
# ----------------------------------------------------------------------------------------------
_INDEX_PATH = os.path.join(MEAD, "_index.json")
_lock = threading.Lock()
_index = None


def _idx():
    global _index
    if _index is None:
        os.makedirs(MEAD, exist_ok=True)
        _index = json.load(open(_INDEX_PATH)) if os.path.exists(_INDEX_PATH) else {}
    return _index


def _idx_save():
    with _lock:
        tmp = _INDEX_PATH + ".tmp"
        json.dump(_idx(), open(tmp, "w"), indent=0, sort_keys=True)
        os.replace(tmp, _INDEX_PATH)


def _get_json(url):
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90))
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 + 3 * attempt)


def record_files(rec):
    """[(key, size)] of a CaltechDATA record."""
    k = f"files:{rec}"
    if k not in _idx():
        if OFFLINE:
            raise RuntimeError(f"offline: no cached file list for {rec}")
        d = _get_json(f"https://data.caltech.edu/api/records/{rec}/files")
        with _lock:
            _idx()[k] = [[e["key"], e["size"]] for e in d["entries"]]
        _idx_save()
    return [tuple(x) for x in _idx()[k]]


def find_record(token):
    """CaltechDATA record whose file list holds a zip named <token>.copied-*.zip (MEAD naming).
    Returns (record, key) or None. The search is exact on the timestamp token."""
    k = f"search:{token}"
    if k not in _idx():
        if OFFLINE:
            raise RuntimeError(f"offline: no cached search for {token}")
        q = urllib.parse.urlencode({"q": f'"{token}"', "size": 25})
        d = _get_json(f"https://data.caltech.edu/api/records?{q}")
        hits = []
        for h in d["hits"]["hits"]:
            for key in (h.get("files", {}).get("entries", {}) or {}):
                if key.startswith(token + ".") and key.endswith(".zip"):
                    hits.append([h["id"], key])
        with _lock:
            _idx()[k] = hits
        _idx_save()
    hits = _idx()[k]
    return tuple(hits[0]) if hits else None


class _HttpFile(io.RawIOBase):
    def __init__(self, url):
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"Range": "bytes=0-0", **UA}), timeout=90)
        self.url = r.geturl()
        self.size = int(r.headers["Content-Range"].split("/")[1]); r.read()
        self.pos = 0

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b""
        end = min(self.size, self.pos + n) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}", **UA})
        for attempt in range(5):
            try:
                data = urllib.request.urlopen(req, timeout=180).read(); break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 + 3 * attempt)
        self.pos += len(data)
        return data

    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)


_zcache = threading.local()


def _remote_zip(rec, key):
    c = getattr(_zcache, "d", None)
    if c is None:
        c = _zcache.d = {}
    if (rec, key) not in c:
        url = f"https://data.caltech.edu/records/{rec}/files/{key}?download=1"
        c[(rec, key)] = zipfile.ZipFile(io.BufferedReader(_HttpFile(url), buffer_size=1 << 16))
    return c[(rec, key)]


def _local_zip_path(rec, key):
    """A zip already downloaded whole under env/raw/siblings (any subfolder), else None."""
    for sub in os.listdir(RAW):
        p = os.path.join(RAW, sub, key)
        if os.path.isfile(p):
            return p
        p = os.path.join(RAW, sub, "raw_sdc", key)
        if os.path.isfile(p):
            return p
    return None


def zip_names(rec, key):
    k = f"names:{rec}/{key}"
    if k not in _idx():
        lp = _local_zip_path(rec, key)
        if lp:
            names = zipfile.ZipFile(lp).namelist()
        else:
            if OFFLINE:
                raise RuntimeError(f"offline: no cached listing for {rec}/{key}")
            names = _remote_zip(rec, key).namelist()
        with _lock:
            _idx()[k] = names
        _idx_save()
    return _idx()[k]


def member(rec, key, name):
    """Bytes of one zip member, cached at env/raw/siblings/mead/<rec>/<key stem>/<name>."""
    p = os.path.join(MEAD, rec, key[:-4], name)
    if os.path.exists(p):
        return open(p, "rb").read()
    lp = _local_zip_path(rec, key)
    if lp:
        data = zipfile.ZipFile(lp).read(name)
    else:
        if OFFLINE:
            raise RuntimeError(f"offline: member not cached {rec}/{key}/{name}")
        data = _remote_zip(rec, key).read(name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".part"
    open(tmp, "wb").write(data)
    os.replace(tmp, p)
    return data


def members(rec, key, names, workers=8):
    """Fetch many members in parallel (each thread keeps its own remote zip handle)."""
    names = list(names)
    todo = [n for n in names if not os.path.exists(os.path.join(MEAD, rec, key[:-4], n))]
    if todo:
        with cf.ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda n: member(rec, key, n), todo))
    return {n: member(rec, key, n) for n in names}
