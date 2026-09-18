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


def find_in_records(token, records):
    """(record, key) of a zip named <token>.copied-*.zip among the file lists of `records`."""
    for rec in sorted(set(records)):
        for key, _ in record_files(rec):
            if key.startswith(token + ".copied") and key.endswith(".zip"):
                return rec, key
    return None


def search_titles(q, size=100):
    """CaltechDATA free-text search; returns [(record, title, [file keys])]. Cached."""
    k = f"title_search:{q}"
    if k not in _idx():
        if OFFLINE:
            raise RuntimeError(f"offline: no cached title search {q}")
        out, page = [], 1
        while True:
            qs = urllib.parse.urlencode({"q": q, "size": size, "page": page})
            d = _get_json(f"https://data.caltech.edu/api/records?{qs}")
            for h in d["hits"]["hits"]:
                out.append([h["id"], h["metadata"]["title"], list((h.get("files", {}).get("entries", {}) or {}))])
            if len(out) >= d["hits"]["total"] or not d["hits"]["hits"] or page >= 20:
                break
            page += 1
        with _lock:
            _idx()[k] = out
        _idx_save()
    return _idx()[k]


# ----------------------------------------------------------------------------------------------
# MEAD text formats
# ----------------------------------------------------------------------------------------------
def parse_ana(txt):
    """MEAD .ana/.exp/.rcp: 4-space indented `key: value` tree -> nested dicts (leaves are strings,
    insertion order kept)."""
    root = {}
    stack = [(-1, root)]
    for raw in txt.replace("\r", "").split("\n"):
        if not raw.strip() or ":" not in raw:
            continue
        ind = len(raw) - len(raw.lstrip(" "))
        k, v = raw.strip().split(":", 1)
        v = v.strip()
        while stack[-1][0] >= ind:
            stack.pop()
        if v == "":
            d = {}
            stack[-1][1][k] = d
            stack.append((ind, d))
        else:
            stack[-1][1][k] = v
    return root


def read_fom_csv(data):
    """MEAD csv_fom_file: YAML-ish header, table starts at the `sample_no` line."""
    lines = data.decode("utf8", "replace").replace("\r", "").split("\n")
    h = [i for i, l in enumerate(lines) if l.startswith("sample_no")]
    if not h:
        raise ValueError("no sample_no header")
    return pd.read_csv(io.StringIO("\n".join(lines[h[0]:])))


def zip_ana(rec, key):
    names = zip_names(rec, key)
    anas = [n for n in names if n.endswith(".ana")]
    if not anas:
        return None, names
    return parse_ana(member(rec, key, anas[0]).decode("utf8", "replace")), names


def _subanas(d):
    return [(k, v) for k, v in d.items() if re.fullmatch(r"ana__\d+", k) and isinstance(v, dict)]


def _walk_files(node, path=()):
    """Yield (path, filename, value) for every `file: kind;...` leaf below node."""
    for k, v in node.items():
        if isinstance(v, dict):
            yield from _walk_files(v, path + (k,))
        elif ";" in v:
            yield path, k, v


# ----------------------------------------------------------------------------------------------
# Platemap 0057-04-1110 (sample_no -> x, y mm). Verified per plate in the ledger.
# ----------------------------------------------------------------------------------------------
_PM = None


def platemap():
    global _PM
    if _PM is None:
        zp = os.path.join(RAW, "tg041-j4g80", "AcidOER-MnSbSnTiCo.zip")
        txt = zipfile.ZipFile(zp).read("data/XRF/0057-04-1110-mp.txt").decode()
        df = pd.read_csv(io.StringIO(txt), comment="%", header=None, skipinitialspace=True)
        _PM = {int(r[0]): (float(r[1]), float(r[2])) for r in df.itertuples(index=False)}
    return _PM


def positions(samples):
    pm = platemap()
    return np.array([pm.get(int(s), (np.nan, np.nan)) for s in samples], float).reshape(-1, 2)


# ----------------------------------------------------------------------------------------------
# Scope: the ADMIT library entries of discovery/siblings/sibling_ledger.json
# ----------------------------------------------------------------------------------------------
def census():
    c = dict(
        xrd=json.load(open(os.path.join(CENSUS, "xrd_ana_census.json"))),
        eche=json.load(open(os.path.join(CENSUS, "eche_ana_census.json"))),
        xrf=json.load(open(os.path.join(CENSUS, "xrf_census.json"))),
        plates=pd.read_csv(os.path.join(CENSUS, "mead_plates_final.csv"), dtype={"plate": str}),
        bundles={},
    )
    bdir = os.path.join(CENSUS, "bundles")
    for f in sorted(os.listdir(bdir)):
        b = json.load(open(os.path.join(bdir, f)))
        c["bundles"][b["record"]] = b
    return c


CURATED = {
    # plate 3594: q9zpw-g8s64 4-LED EQE (SLF9) replaces the MEAD photocurrent of the same experiment
    "3594": dict(library="q9zpw-g8s64 + MEAD 7qy17-9az58", experiment="20170802.122251",
                 eqe_file=os.path.join(RAW, "q9zpw-g8s64", "data", "Fig3", "SLF9_EQE_comp.csv"),
                 eqe_cols={387: "eqe387_pct", 455: "eqe455_pct", 516: "eqe516_pct", 602: "eqe602_pct"},
                 sample_col="Sample", plate_col="plate", invalid=None, substrate="FTO",
                 comp_cols={"V": "V", "Cr": "Cr", "Fe": "Fe"}),
    # plate 3557: 0hj2v-qwv46 4-LED EQE; XRD from ehp06-pcf04 .udi
    "3557": dict(library="0hj2v-qwv46 + ehp06-pcf04", experiment="20170802.130408",
                 eqe_file=os.path.join(RAW, "0hj2v-qwv46", "Fig2_3_4_eqe_scatterplot.csv"),
                 eqe_cols={387: "EQE_pct_387", 455: "EQE_pct_455", 516: "EQE_pct_516", 602: "EQE_pct_602"},
                 sample_col="Sample", plate_col="plate", invalid=-9.0, substrate="",
                 comp_cols={"Ca": "elX", "Cu": "Cu", "V": "V"},
                 udi=os.path.join(RAW, "ehp06-pcf04", "XRD_Dataset_CuCaV_ana__7_3557.udi")),
}
# dekcc-2tb35 plates are MEAD 3928/3930/3933; FTO substrate and 550 C anneal from npj Comput Mater 2022 Methods
SUBSTRATE = {"3594": "FTO", "3928": "FTO", "3930": "FTO", "3933": "FTO"}
TOL_DIST = 0.05
MIN_CAND = 15
V_TARGET = 1.23      # V vs RHE, the base-environment CA bias; used only to pick among same-LED CA techniques


def base_plates():
    p = os.path.join(ROOT, "env", "raw", "antimonate", "source_data_v2", "XSbO_plates_xrd_udi.csv")
    return set(pd.read_csv(p)["plate_id"].astype(int).astype(str))


def admit_plates(c):
    df = c["plates"]
    out = {}
    for _, r in df[df["status"] == "ADMIT"].iterrows():
        T = r["T"]
        out[r["plate"]] = dict(cations=r["cations"].split("-"), annealT_C=int(T) if pd.notna(T) else -1,
                               census=r.to_dict())
    out["3557"] = dict(cations=["Ca", "Cu", "V"], annealT_C=-1, census=None)
    return out


def plate_records(c, plate):
    """Every CaltechDATA record the census ties to this plate (analysis records and bundles)."""
    recs = set()
    for r in c["eche"] + c["xrd"] + c["xrf"]:
        for a in r.get("anas", []) + r.get("zips", []):
            if plate in str(a.get("plate_ids") or "").split(","):
                recs.add(r["record"])
    row = c["plates"][c["plates"]["plate"] == plate]
    for _, r in row.iterrows():
        for f in ("photo_recs", "xrf_rec", "xrd_recs"):
            for x in str(r[f]).split(";"):
                if x and x != "nan":
                    recs.add(x.split(":")[0])
    for rec, b in c["bundles"].items():
        if any(plate == str(z.get("plate_ids", "")) for z in b.get("zips", [])) or rec in recs:
            recs.add(rec)
    return recs


# ----------------------------------------------------------------------------------------------
# XRF -> cation fractions at XRF samples
# ----------------------------------------------------------------------------------------------
LINE_ORDER = {"K": 0, "L": 1, "M": 2}


def _pick_lines(cols, cations, suffix):
    """cation -> column `<El>.<line><suffix>`, highest-energy line (K over L over M) whose values
    are not all zero. Returns None if a cation has no usable line."""
    out = {}
    for el in cations:
        opts = []
        for col in cols.columns:
            m = re.fullmatch(rf"{el}\.([KLM])" + re.escape(suffix), col)
            if m and np.nanmax(np.abs(cols[col].to_numpy(float))) > 0:
                opts.append((LINE_ORDER[m.group(1)], col))
        if not opts:
            return None
        out[el] = sorted(opts)[0][1]
    return out


_RASTER = None


def raster_map(c):
    """MEAD renumbered the 1521-point XRF raster of plate 3059 from raster index (1..1521, analysis
    20160520.162518) to platemap sample numbers (analysis 20190820.172334); rows are identical
    (CPS and stage columns). Returns (index->sample dict, stage raster relative to first point)."""
    global _RASTER
    if _RASTER is None:
        a = xrf_table(c, "3059", "20160520.162518", "581m6-kkk11", "ana__1")
        b = xrf_table(c, "3059", "20190820.172334", "581m6-kkk11", "ana__1")
        cps = [x for x in a.columns if x.endswith(".CPS")]
        assert (a[cps].to_numpy() == b[cps].to_numpy()).all()
        assert (a[["StagX", "StagY"]].to_numpy() == b[["StagX", "StagY"]].to_numpy()).all()
        m = dict(zip(a["sample_no"].astype(int), b["sample_no"].astype(int)))
        st = a[["StagX", "StagY"]].to_numpy(float)
        _RASTER = (m, st - st[0])
    return _RASTER


def _xrf_anas(c, plate):
    out = []
    for r in c["xrf"]:
        for a in r["anas"]:
            if plate in str(a["plate_ids"] or "").split(","):
                out.append((a["key"].split(".copied")[0], r["record"], a["key"]))
    return sorted(set(out))


def xrf_table(c, plate, ana_name, rec=None, sub=None):
    for name, r, key in _xrf_anas(c, plate):
        if name == ana_name and (rec is None or r == rec):
            d, names = zip_ana(r, key)
            for k, v in _subanas(d):
                if sub and k != sub:
                    continue
                for _, fn, val in _walk_files(v):
                    if val.startswith("csv_fom_file"):
                        df = read_fom_csv(member(r, key, fn))
                        return df[df["plate_id"].astype(str) == plate].reset_index(drop=True)
    raise KeyError((plate, ana_name, rec, sub))


def load_xrf(c, plate, cations, notes):
    """Rule: among the plate's XRF analyses, a standards-based nmol FOM (Analysis__Process_XRFS_Stds)
    that quantifies every plate cation is preferred over the EDAX FP AtPerc FOM; the latest analysis
    of the preferred kind wins. Per cation the highest-energy line with nonzero values is used
    (K over L over M). Fractions = chosen-line amounts / their sum over plate cations (negative
    amounts clipped to 0)."""
    cands, stage = [], {}
    for name, rec, key in _xrf_anas(c, plate):
        d, names = zip_ana(rec, key)
        if d is None:
            continue
        for k, v in _subanas(d):
            for _, fn, val in _walk_files(v):
                if not val.startswith("csv_fom_file"):
                    continue
                df = read_fom_csv(member(rec, key, fn))
                df = df[df["plate_id"].astype(str) == plate].reset_index(drop=True)
                if {"StagX", "StagY"} <= set(df.columns):
                    stage[(rec, name)] = df.drop_duplicates("sample_no").set_index("sample_no")[["StagX", "StagY"]]
                for kind, suffix in (("nmol", ".nmol"), ("AtPerc", ".AtPerc")):
                    lines = _pick_lines(df, cations, suffix)
                    if lines:
                        cands.append(dict(kind=kind, name=name, rec=rec, key=key, fom=fn, lines=lines, df=df))
    if not cands:
        return None
    cands.sort(key=lambda x: x["name"], reverse=True)          # latest analysis first
    cands.sort(key=lambda x: x["kind"] != "nmol")              # stable: nmol kind first
    best = cands[0]
    df = best["df"].drop_duplicates("sample_no", keep="first")
    A = np.clip(df[[best["lines"][el] for el in cations]].to_numpy(float), 0, None)
    tot = A.sum(1)
    ok = np.isfinite(tot) & (tot > 0)
    F = A[ok] / tot[ok, None]
    smp = df["sample_no"].astype(int).to_numpy()[ok]
    info = dict(analysis=best["name"], record=best["rec"], fom_file=best["fom"], kind=best["kind"],
                lines=best["lines"], n_rows=int(len(df)), n_used=int(ok.sum()),
                n_candidates=len(cands), numbering="platemap")
    # sample numbering: platemap sample numbers, or raster indices 1..N (checked against 3059)
    if smp.max() <= len(df) and set(smp) <= set(range(1, len(df) + 1)) and len(df) == 1521:
        m, ref = raster_map(c)
        st = stage[(best["rec"], best["name"])].loc[smp].to_numpy(float)
        idx = smp - 1
        dev = float(np.abs((st - st[0]) - ref[idx] + ref[idx[0]]).max())
        info.update(numbering="raster_index->platemap via 3059 renumbering", raster_max_dev_mm=round(dev, 3))
        if dev > 2.0:
            notes.append(f"XRF {best['name']}: raster deviates {dev:.2f} mm from the 3059 raster (>2 mm spot); composition not positioned")
            return None
        smp = np.array([m[int(s)] for s in smp])
    xy = positions(smp)
    info["platemap_missing"] = int(np.isnan(xy[:, 0]).sum())
    keep = ~np.isnan(xy[:, 0])
    return dict(samples=smp[keep], xy=xy[keep], F=F[keep], info=info)


XRF_SPOT_RADIUS_MM = 1.0   # EDAX XRF rcp spot_size "2000 um-Spot": each XRF value covers a 1 mm radius


class CompInterp:
    """Platemap x,y interpolation of XRF cation fractions. XRF on one line (perpendicular std < 1 mm):
    1D linear interpolation along the line (MEAD `platemap_xy_line` convention). Otherwise 2D linear
    (Delaunay) interpolation. No extrapolation: a target beyond the XRF extent by more than the XRF
    spot radius (1 mm) gets NaN; a target within the spot radius of the extent takes the value at the
    nearest point of the extent (it lies inside the footprint of the edge measurement)."""

    def __init__(self, xy, F):
        from scipy.interpolate import LinearNDInterpolator
        from scipy.spatial import ConvexHull
        self.mu = xy.mean(0)
        _, S, Vt = np.linalg.svd(xy - self.mu, full_matrices=False)
        self.perp_sd = float(S[1] / np.sqrt(len(xy))) if len(S) > 1 else 0.0
        self.line = self.perp_sd < 1.0
        self.Vt = Vt
        if self.line:
            t = (xy - self.mu) @ Vt[0]
            o = np.argsort(t, kind="stable")
            self.t, self.F = t[o], F[o]
        else:
            self.f = LinearNDInterpolator(xy, F)
            h = ConvexHull(xy)
            self.edges = [(xy[a], xy[b]) for a, b in h.simplices]
            self.centroid = xy[h.vertices].mean(0)
        self.n_clamped = 0

    def _project_to_hull(self, p):
        best = (np.inf, None)
        for a, b in self.edges:
            ab = b - a
            u = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
            q = a + u * ab
            dd = np.hypot(*(p - q))
            if dd < best[0]:
                best = (dd, q)
        return best

    def __call__(self, xy):
        xy = np.atleast_2d(np.asarray(xy, float))
        clamped = np.zeros(len(xy), bool)
        if self.line:
            t = (xy - self.mu) @ self.Vt[0]
            lo, hi = self.t[0], self.t[-1]
            far = (t < lo - XRF_SPOT_RADIUS_MM) | (t > hi + XRF_SPOT_RADIUS_MM)
            clamped = ~far & ((t < lo) | (t > hi))
            tc = np.clip(t, lo, hi)
            out = np.stack([np.interp(tc, self.t, self.F[:, j]) for j in range(self.F.shape[1])], 1)
            out[far] = np.nan
            perp = np.abs((xy - self.mu) @ self.Vt[1])
        else:
            out = self.f(xy)
            perp = np.zeros(len(xy))
            for i in np.where(np.isnan(out).any(1) & ~np.isnan(xy[:, 0]))[0]:
                dd, q = self._project_to_hull(xy[i])
                if dd <= XRF_SPOT_RADIUS_MM:
                    q = q + 1e-6 * (self.centroid - q)
                    out[i] = self.f(q[None])[0]
                    clamped[i] = not np.isnan(out[i]).any()
        out[np.isnan(xy[:, 0])] = np.nan
        with np.errstate(invalid="ignore"):
            out = out / out.sum(1, keepdims=True)
        self.last_clamped = clamped
        return out, perp


# ----------------------------------------------------------------------------------------------
# XRD: 1D integrated patterns
# ----------------------------------------------------------------------------------------------
def _xrd_anas(c, plate):
    out = []
    for r in c["xrd"]:
        for z in r["zips"]:
            if str(z.get("plate_ids")) == plate and z.get("analysis_type") in ("xrds", "ssrl"):
                out.append((z["key"].split(".copied")[0], r["record"], z["key"]))
    for rec, b in c["bundles"].items():
        for z in b.get("xrd_ana", []):
            if plate in z.get("desc", "").split("plate_id ")[-1].split(","):
                out.append((z["key"].split(".copied")[0], rec, z["key"]))
    return sorted(set(out))


def _pattern_sets(d):
    """For one XRD .ana: {subana: {sample: [(runint, file, qcol, icol)]}} for raw 1D pattern files,
    and the merge sub-analyses. Raw = intensity column 'intensity.counts' (not background-processed)."""
    raw, merged = {}, {}
    for k, v in _subanas(d):
        name = v.get("name", "")
        for path, fn, val in _walk_files(v):
            parts = val.split(";")
            if "pattern" not in parts[0]:
                continue
            cols = parts[1].split(",")
            run = next((int(p.split("__")[1]) for p in path if p.startswith("files_run__")), 0)
            smp = int(parts[-1])
            if cols[-1] == "intensity.counts" and cols[0] == "q.nm":
                raw.setdefault(k, {}).setdefault(smp, []).append((run, fn, cols[0], cols[-1]))
            elif cols[-1] == "intensity.counts_processed" and cols[0] == "q.nm_processed":
                raw.setdefault(k + ":processed", {}).setdefault(smp, []).append((run, fn, cols[0], cols[-1]))
            elif name == "Analysis__Resamp_Merge_Patterns" and cols == ["q.nm_resampled", "intensity.counts_resampled"]:
                prm = v.get("parameters", {})
                if "," in prm.get("pattern_fn_search_str", "") and prm.get("intensity_key") == "intensity.counts":
                    merged.setdefault(k, {}).setdefault(smp, []).append((run, fn, cols[0], cols[-1]))
    return raw, merged


def choose_xrd(c, plate, notes):
    """Rule: per plate one XRD analysis, the one with the most samples carrying a raw 1D pattern
    (tie: earliest analysis). Within it, the raw integrated patterns ('q.nm','intensity.counts');
    when a sample has several detector frames, the Resamp_Merge_Patterns sub-analysis that merges
    all frames of the raw patterns. Duplicate samples: first by run index, then listing order."""
    best = None
    tried = []
    for name, rec, key in _xrd_anas(c, plate):
        d, names = zip_ana(rec, key)
        if d is None:
            tried.append(dict(analysis=name, record=rec, n1d=0, note="no .ana"))
            continue
        raw, merged = _pattern_sets(d)
        use = None
        # raw (unprocessed) patterns first; background-processed 1D patterns only when no raw 1D exists
        for k, smps in sorted(raw.items(), key=lambda kv: (kv[0].endswith(":processed"), -len(kv[1]))):
            multi = any(len(v) > 1 and len({f for _, f, _, _ in v}) > 1 and
                        len({r for r, _, _, _ in v}) == 1 for v in smps.values())
            if multi:
                if merged and not k.endswith(":processed"):
                    mk = max(merged, key=lambda z: len(merged[z]))
                    use = (mk, merged[mk], "merged frames (raw)")
                    break
                continue
            use = (k.split(":")[0], smps, "processed 1D (no raw 1D in analysis)" if k.endswith(":processed") else "raw 1D")
            break
        n1d = len(use[1]) if use else 0
        tried.append(dict(analysis=name, record=rec, n1d=n1d, subana=use[0] if use else None,
                          kind=use[2] if use else None))
        if use and (best is None or n1d > best["n1d"]):
            best = dict(analysis=name, record=rec, key=key, n1d=n1d, subana=use[0], files=use[1], kind=use[2])
    return best, tried


def load_xrd_mead(best):
    files = {}
    for smp, lst in best["files"].items():
        run, fn, qc, ic = sorted(lst, key=lambda x: x[0])[0]
        files[smp] = (fn, qc, ic)
    data = members(best["record"], best["key"], [f for f, _, _ in files.values()])
    pats = {}
    for smp, (fn, qc, ic) in files.items():
        df = pd.read_csv(io.BytesIO(data[fn]))
        q, y = df[qc].to_numpy(float), df[ic].to_numpy(float)
        o = np.argsort(q, kind="stable")
        pats[smp] = (q[o], y[o])
    return pats


def common_grid(pats):
    """Identical grids are kept. Otherwise Q = grid of the pattern with most points, restricted to
    the q-range covered by every pattern; others linearly interpolated onto it."""
    smps = sorted(pats)
    grids = [pats[s][0] for s in smps]
    same = all(len(g) == len(grids[0]) and np.allclose(g, grids[0], rtol=0, atol=1e-9) for g in grids)
    if same:
        return grids[0], np.stack([pats[s][1] for s in smps]), smps, "identical grids"
    lo = max(g[0] for g in grids)
    hi = min(g[-1] for g in grids)
    ref = max(grids, key=len)
    Q = ref[(ref >= lo - 1e-12) & (ref <= hi + 1e-12)]
    X = np.stack([np.interp(Q, pats[s][0], pats[s][1]) for s in smps])
    return Q, X, smps, f"grids differ; common range [{lo:.4f}, {hi:.4f}] nm^-1 on the {len(ref)}-point grid, linear interp"


# ----------------------------------------------------------------------------------------------
# Photoelectrochemistry: MEAD eche analyses -> per-run conditions from the experiment's .rcp data
# ----------------------------------------------------------------------------------------------
def _eche_anas(c, plate):
    out = []
    for r in c["eche"]:
        for a in r["anas"]:
            if plate in str(a["plate_ids"] or "").split(",") and a.get("experiment_path"):
                if any("photo" in f[0] for f in a["foms"]):
                    exp = a["experiment_path"].rsplit("/", 1)[1].split(".copied")[0]
                    out.append(dict(name=a["key"].split(".copied")[0], record=r["record"], key=a["key"], exp=exp))
    return sorted(out, key=lambda x: x["name"])


def iphoto_subanas(d):
    """[(subana, technique, fom file, {runint: [samples]})] for Analysis__Iphoto sub-analyses."""
    out = []
    for k, v in _subanas(d):
        if v.get("name") != "Analysis__Iphoto" or "technique" not in v:
            continue
        fom = [fn for _, fn, val in _walk_files(v) if val.startswith("csv_fom_file") and "I.A_photo" in val]
        if not fom:
            continue
        runs = {}
        for path, fn, val in _walk_files(v):
            m = [p for p in path if p.startswith("files_run__")]
            if m and "Sample" in fn:
                runs.setdefault(int(m[0].split("__")[1]), set()).add(int(val.split(";")[-1]))
        out.append((k, v["technique"], fom[0], runs))
    return out


def exp_runs_from_exp(c, plate, exp, notes):
    """{runint: rcp-parameter dict} from the experiment's .exp (which embeds each run's .rcp)."""
    rk = find_in_records(exp, plate_records(c, plate))
    if rk is None and not exp.endswith(".done"):
        rk = find_record(exp)
    if rk is None:
        return None, None
    exps = [n for n in zip_names(*rk) if n.endswith(".exp")]
    if not exps:
        return None, None
    d = parse_ana(member(*rk, exps[0]).decode("utf8", "replace"))
    runs = {}
    for k, v in d.items():
        if k.startswith("run__") and isinstance(v, dict) and isinstance(v.get("parameters"), dict):
            runs[int(k.split("__")[1])] = dict(v["parameters"], run_name=v.get("name"))
    return runs, dict(record=rk[0], key=rk[1], via="exp")


def exp_runs_by_scan(plate, exp, technique, run_samples, notes):
    """When the .exp is not deposited: find the run records (CaltechDATA 'Electrochemistry
    measurements ... from Run <name>') within +-7 days of the experiment date whose .rcp has this
    plate_id, and map each analysis runint to the run whose <technique> sample files are exactly the
    runint's sample set. Unmapped runints stay unknown."""
    import datetime as dt
    d0 = dt.datetime.strptime(exp[:8], "%Y%m%d")
    cands = []
    for k in range(-7, 8):
        day = (d0 + dt.timedelta(days=k)).strftime("%Y%m%d")
        for rec, title, keys in search_titles(day):
            if "Electrochemistry measurements" in title and "from Run" in title:
                for key in keys:
                    if key.startswith(day) and key.endswith(".zip"):
                        cands.append((rec, key))
    found = {}
    for rec, key in sorted(set(cands)):
        try:
            names = zip_names(rec, key)
        except Exception as e:
            notes.append(f"run scan {rec}/{key}: {e}")
            continue
        rcps = [n for n in names if n.endswith(".rcp")]
        if not rcps:
            continue
        p = parse_ana(member(rec, key, rcps[0]).decode("utf8", "replace"))
        if str(p.get("plate_id")) != plate:
            continue
        smp = {int(m.group(1)) for n in names for m in [re.match(rf"Sample(\d+)_.*_{technique}\.txt$", n)] if m}
        for ri, s in run_samples.items():
            if s and s == smp:
                found.setdefault(ri, []).append(dict(p, run_name=key.split(".copied")[0], run_record=rec))
    runs = {ri: v[0] for ri, v in found.items() if len(v) == 1}
    return runs, dict(via="run scan", n_candidates=len(set(cands)), mapped=sorted(runs), ambiguous=sorted(ri for ri, v in found.items() if len(v) > 1))


def led_of(params, technique):
    """LED wavelength (nm) and source for a technique of a run, from the run's rcp parameters:
    echem_params__<tech>.toggle_value indexes toggle_value_illumination / illumination_wavelength.
    Returns (nm, source, None) or (None, None, reason)."""
    ep = params.get(f"echem_params__{technique}")
    if not isinstance(ep, dict) or "toggle_value" not in ep:
        return None, None, f"no echem_params__{technique}"
    tv = ep["toggle_value"].strip()
    if tv in ("0", ""):
        return None, None, f"{technique} toggle_value 0 (dark)"
    wl = [w.strip() for w in str(params.get("illumination_wavelength", "")).split(",") if w.strip()]
    src = [w.strip() for w in str(params.get("illumination_source", "")).split(",")]
    tvi = [w.strip() for w in str(params.get("toggle_value_illumination", "")).split(",") if w.strip()]
    if not wl:
        return None, None, "no illumination_wavelength"
    if tvi:
        if tv not in tvi or len(tvi) != len(wl):
            return None, None, f"toggle {tv} not mappable to wavelengths {wl} via {tvi}"
        i = tvi.index(tv)
    elif len(wl) == 1:
        i = 0
    else:
        return None, None, f"several wavelengths {wl} and no toggle_value_illumination"
    try:
        nm = float(wl[i])
    except ValueError:
        return None, None, f"wavelength '{wl[i]}' not numeric"
    return nm, (src[i] if i < len(src) else (src[0] if src else "")), None


def rcp_summary(p, T):
    keys = ("solution_description", "original_solution_description", "electrolyte", "solution_ph", "illumination_wavelength",
            "illumination_source", "illumination_intensity", "toggle_value_illumination", "reference_vrhe", "platemap_file_path")
    out = {k: p.get(k) for k in keys if k in p}
    ep = p.get(f"echem_params__{T}")
    if isinstance(ep, dict):
        out[f"echem_params__{T}"] = {k: ep[k] for k in ("toggle_value", "potential_vref", "init_potential_vref") if k in ep}
    return out


def cond_key(params):
    """(electrolyte label, pH, full condition). Label = rcp original_solution_description (as entered at
    measurement; it keeps the 0.01 M sulfite that the normalised solution_description sometimes drops,
    cf. q9zpw SLF9), else solution_description. Grouping uses all electrolyte fields."""
    orig = str(params.get("original_solution_description", "") or "").strip()
    desc = str(params.get("solution_description", "") or "").strip()
    return (orig or desc, str(params.get("solution_ph", "")).strip(),
            "|".join([desc, orig, str(params.get("electrolyte", "")).strip()]))


def bias_rhe(params, technique):
    ep = params.get(f"echem_params__{technique}", {})
    try:
        return float(ep["potential_vref"]) - float(params["reference_vrhe"])
    except (KeyError, TypeError, ValueError):
        return None


def udi_xrd(path):
    sys.path.insert(0, ROOT)
    from bench.data import parse_udi
    meta, arr = parse_udi(path)
    n = int(meta["N"])
    smp = [int(float(s)) for s in np.array(arr["sample_no"])[:n]]
    pats = {}
    for i, s in enumerate(smp):
        if s not in pats:                       # duplicate samples: keep the first
            pats[s] = (arr["Q"], arr[f"I{i+1}"])
    els = meta["Elements"].split(",") if "Elements" in meta else list(arr["Elements"])
    comps = {el: arr[el][:n] for el in els}
    return pats, smp, comps, meta


# ----------------------------------------------------------------------------------------------
# Episode assembly
# ----------------------------------------------------------------------------------------------
def tech_pref(tech, bias):
    """CA (fixed bias) before CV; among CA the bias closest to 1.23 V vs RHE; then technique number."""
    is_ca = tech.upper().startswith("CA")
    num = int(re.sub(r"\D", "", tech) or 0)
    return (not is_ca, abs(bias - V_TARGET) if (is_ca and bias is not None) else 9.0, num)


class Plate:
    def __init__(self, plate, cations, interp, xrd_comp):
        self.plate, self.cations, self.interp, self.xrd_comp = plate, cations, interp, xrd_comp

    def candidates(self, samples, merits, invalid=None):
        """Apply, in order: duplicate sample (keep first) -> invalid merit -> composition (platemap
        interpolation of XRF) -> nearest XRD within 0.05. Returns kept rows and drop counts."""
        drops = {}

        def drop(k, n=1):
            if n:
                drops[k] = drops.get(k, 0) + int(n)
        seen, rows = set(), []
        for s, m in zip(samples, merits):
            s = int(s)
            if s in seen:
                drop("duplicate_sample"); continue
            seen.add(s)
            rows.append((s, float(m) if m is not None and not (isinstance(m, str)) else np.nan))
        ok = [(s, m) for s, m in rows if np.isfinite(m) and not (invalid is not None and m == invalid)]
        drop("merit_invalid", len(rows) - len(ok))
        if not ok:
            return [], drops, {}
        smp = np.array([s for s, _ in ok]); mer = np.array([m for _, m in ok])
        xy = positions(smp)
        comp, perp = self.interp(xy)
        clamped = self.interp.last_clamped
        nopos = np.isnan(xy[:, 0])
        drop("no_platemap_position", nopos.sum())
        nocomp = ~nopos & np.isnan(comp).any(1)
        drop("outside_xrf_extent", nocomp.sum())
        good = ~np.isnan(comp).any(1)
        smp, mer, comp, perp, clamped = smp[good], mer[good], comp[good], perp[good], clamped[good]
        if not len(smp):
            return [], drops, {}
        D = 0.5 * np.abs(comp[:, None, :] - self.xrd_comp[None, :, :]).sum(-1)
        j = D.argmin(1)
        d = D[np.arange(len(j)), j]
        far = d > TOL_DIST
        drop("xrd_dist_gt_0.05", far.sum())
        keep = ~far
        out = [dict(sample=int(s), merit=float(m), comp=[round(float(x), 6) for x in cc], nearest=int(jj),
                    dist=round(float(dd), 6)) for s, m, cc, jj, dd in zip(smp[keep], mer[keep], comp[keep], j[keep], d[keep])]
        # renormalise the rounded composition so it sums to 1 exactly within 1e-6
        for r in out:
            t = sum(r["comp"]); r["comp"] = [round(x / t, 6) for x in r["comp"]]
        geo = dict(max_perp_offset_mm=round(float(perp[keep].max()), 2) if keep.any() else None,
                   n_within_xrf_spot_of_edge=int(clamped[keep].sum()))
        return out, drops, geo


def mead_interp_crosscheck(c, plate, cations, interp):
    """Diagnostic: compare our XRF interpolation with MEAD's own FOM_Interp_Merge_Ana compositions
    (interp_is_comp=1) found in the plate's eche analyses; one entry per MEAD XRF source analysis."""
    out, seen = [], set()
    for a in _eche_anas(c, plate):
        try:
            d, _ = zip_ana(a["record"], a["key"])
        except Exception:
            continue
        for k, v in _subanas(d or {}):
            prm = v.get("parameters", {})
            if "Interp" not in v.get("name", "") or prm.get("interp_is_comp") != "1":
                continue
            aux = prm.get("aux_ana_path", "")
            if aux in seen:
                continue
            fom = [fn for _, fn, val in _walk_files(v) if val.startswith("csv_fom_file")]
            if not fom:
                continue
            df = read_fom_csv(member(a["record"], a["key"], fom[0]))
            df = df[df["plate_id"].astype(str) == plate]
            lines = _pick_lines(df, cations, ".AtFrac") if len(df) else None
            if not lines:
                continue
            seen.add(aux)
            M = df[[lines[el] for el in cations]].to_numpy(float)
            M = M / M.sum(1, keepdims=True)
            ours, _ = interp(positions(df["sample_no"].to_numpy()))
            dd = 0.5 * np.abs(M - ours).sum(1)
            ok = np.isfinite(dd)
            out.append(dict(mead_analysis=a["name"], aux_xrf=aux.rsplit("/", 1)[-1].split(".copied")[0],
                            interp_keys=prm.get("interp_keys"), n=int(len(dd)), n_ours_nan=int((~ok).sum()),
                            median_half_L1=round(float(np.median(dd[ok])), 4) if ok.any() else None,
                            max_half_L1=round(float(dd[ok].max()), 4) if ok.any() else None))
    return out


def build_plate(c, plate, meta, base, log):
    cations = sorted(meta["cations"])
    chem = "-".join(cations)
    lib = CURATED.get(plate, {}).get("library", f"MEAD plate {plate}")
    if plate in ("3928", "3930", "3933"):
        lib += " (= dekcc-2tb35 plate; merits from MEAD)"
    P = dict(plate_id=plate, chem=chem, library=lib,
             status=None, rule=None, n_xrd=0, n_merit=0, episodes=[], excluded_episodes=[], drops={},
             sources={}, notes=[])
    if plate in base:
        P.update(status="EXCLUDED", rule="P-E1", reason="plate is in the base environment")
        return P, None, []
    # --- composition source
    xrf = load_xrf(c, plate, cations, P["notes"])
    if xrf is None:
        P.update(status="EXCLUDED", rule="P-E3", reason="no XRF composition for all plate cations")
        return P, None, []
    P["sources"]["xrf"] = xrf["info"]
    interp = CompInterp(xrf["xy"], xrf["F"])
    P["sources"]["xrf"].update(geometry="line (1D along XRF line)" if interp.line else "2D (Delaunay linear)",
                               perp_sd_mm=round(interp.perp_sd, 3),
                               mead_interp_crosscheck=mead_interp_crosscheck(c, plate, cations, interp))
    # --- XRD
    if plate == "3557":
        pats, _, udi_comp, _ = udi_xrd(CURATED[plate]["udi"])
        P["sources"]["xrd"] = dict(source="ehp06-pcf04 XRD_Dataset_CuCaV_ana__7_3557.udi", n1d=len(pats),
                                   kind="udi integrated counts (first detector frame, as deposited)")
    else:
        best, tried = choose_xrd(c, plate, P["notes"])
        P["sources"]["xrd_candidates"] = tried
        if best is None:
            census_row = meta.get("census") or {}
            if census_row and int(census_row.get("xrd_raw_only") or 0) > 0:
                P.update(status="EXCLUDED", rule="P-E2", reason="XRD only as 2D frames")
            else:
                P.update(status="EXCLUDED", rule="P-I1", reason="no 1D XRD pattern found")
            return P, None, []
        pats = load_xrd_mead(best)
        P["sources"]["xrd"] = {k: best[k] for k in ("analysis", "record", "subana", "kind", "n1d")}
    Q, X, xsmp, gridnote = common_grid(pats)
    P["sources"]["xrd"]["grid"] = gridnote
    xcomp, _ = interp(positions(xsmp))
    okx = ~np.isnan(xcomp).any(1)
    P["sources"]["xrd"]["n_within_xrf_spot_of_edge"] = int(interp.last_clamped[okx].sum())
    P["drops"]["xrd_no_composition"] = int((~okx).sum())
    Q, X, xsmp, xcomp = Q, X[okx], [s for s, o in zip(xsmp, okx) if o], xcomp[okx]
    P["n_xrd"] = int(len(xsmp))
    if plate == "3557":
        uc = np.stack([np.asarray(udi_comp[el], float) for el in cations], 1)
        usmp = [int(float(s)) for s in udi_xrd(CURATED[plate]["udi"])[1]]
        first = {s: i for i, s in reversed(list(enumerate(usmp)))}
        uu = np.stack([uc[first[s]] for s in xsmp]); uu = uu / uu.sum(1, keepdims=True)
        P["notes"].append(f"XRD composition cross-check vs .udi Ca/Cu/V: median {np.median(0.5*np.abs(uu-xcomp).sum(1)):.4f}, max {np.max(0.5*np.abs(uu-xcomp).sum(1)):.4f} (0.5*L1)")
    if P["n_xrd"] == 0:
        P.update(status="EXCLUDED", rule="P-I3", reason="no XRD pattern inside the XRF extent")
        return P, None, []
    plate_obj = Plate(plate, cations, interp, xcomp)
    npz = dict(Q=np.asarray(Q, float), xrd=np.asarray(X, float), xrd_comp=np.asarray(xcomp, float),
               elements=np.array(cations), xrd_sample=np.array(xsmp, int),
               substrate=np.array(SUBSTRATE.get(plate, CURATED.get(plate, {}).get("substrate", ""))),
               annealT_C=np.array(int(meta["annealT_C"])))
    eps = build_episodes(c, plate, cations, chem, plate_obj, P, log)
    return P, npz, eps


def _episode(plate, chem, cations, eid, rows, merit_name, led, src, cond, sources):
    return dict(episode_id=eid, plate_id=plate, chem=chem, elements=cations,
                comp=[r["comp"] for r in rows], merit=[r["merit"] for r in rows], merit_name=merit_name,
                illum=dict(led_nm=led, source=src), ph=float(cond[1]) if _isnum(cond[1]) else cond[1],
                electrolyte=cond[0], nearest_xrd=[r["nearest"] for r in rows], xrd_dist=[r["dist"] for r in rows],
                sample_no=[r["sample"] for r in rows], source_records=sources)


def _isnum(x):
    try:
        float(x); return True
    except (TypeError, ValueError):
        return False


def build_episodes(c, plate, cations, chem, PL, P, log):
    eps = []
    anas = _eche_anas(c, plate)
    by_exp = {}
    for a in anas:
        by_exp.setdefault(a["exp"], []).append(a)
    cur = CURATED.get(plate)
    merit_samples = set()
    for exp in sorted(by_exp):
        alist = sorted(by_exp[exp], key=lambda a: a["name"])
        tech = {}
        for a in alist:                                   # later analyses overwrite: latest wins
            d, _ = zip_ana(a["record"], a["key"])
            if d is None:
                continue
            for sub, T, fom, runs in iphoto_subanas(d):
                tech[T] = dict(ana=a, sub=sub, fom=fom, runs=runs)
        if not tech:
            continue
        for T, t in tech.items():
            df = read_fom_csv(member(t["ana"]["record"], t["ana"]["key"], t["fom"]))
            df = df[df["plate_id"].astype(str) == plate].reset_index(drop=True)
            t["df"] = df
            merit_samples |= set(df["sample_no"].astype(int))
        base_src = lambda T: dict(kind="MEAD eche analysis", record=tech[T]["ana"]["record"],
                                  analysis=tech[T]["ana"]["name"], subana=tech[T]["sub"], fom_file=tech[T]["fom"],
                                  technique=T, experiment=exp)
        nmax = max(t["df"]["sample_no"].nunique() for t in tech.values())
        if nmax < MIN_CAND and not (cur and exp == cur["experiment"]):
            for T in sorted(tech):
                P["excluded_episodes"].append(dict(episode_id=f"{plate}_{exp}_{T}", rule="P-I4",
                    reason=f"pre-check: {tech[T]['df']['sample_no'].nunique()} merit samples in the whole run (<{MIN_CAND}); conditions not resolved",
                    source=base_src(T)))
            continue
        runs, how = exp_runs_from_exp(c, plate, exp, P["notes"])
        if runs is None:
            runs = {}
            how = dict(via="run scan", per_technique={})
            for T in sorted(tech):
                r, h = exp_runs_by_scan(plate, exp, T, tech[T]["runs"], P["notes"])
                for ri, p in r.items():
                    runs.setdefault(ri, {}).update({f"__{T}": p})
                how["per_technique"][T] = h
        # per technique, per row: (led, cond)
        groups = {}
        for T in sorted(tech):
            df = tech[T]["df"]
            unknown = []
            for i, row in df.iterrows():
                ri = int(row["runint"])
                p = runs.get(ri)
                if p is not None and f"__{T}" in p:
                    p = p[f"__{T}"]
                elif p is not None and "run_name" not in p:
                    p = None
                if p is None:
                    unknown.append((i, f"run {ri}: .rcp parameters not found"))
                    continue
                led, src, why = led_of(p, T)
                if why:
                    unknown.append((i, f"run {ri}: {why}"))
                    continue
                g = groups.setdefault((led, cond_key(p)), {}).setdefault(T, dict(rows=[], src=src, runs=set(), bias=bias_rhe(p, T),
                                                                               rcp=rcp_summary(p, T)))
                g["rows"].append(i); g["runs"].add(p.get("run_name"))
            if unknown:
                reasons = sorted({w for _, w in unknown})
                P["excluded_episodes"].append(dict(episode_id=f"{plate}_{exp}_{T}_unknown", rule="P-I2",
                    reason="illumination/electrolyte not readable: " + "; ".join(reasons)[:400],
                    n_rows=len(unknown), source=dict(base_src(T), condition_lookup=how)))
        # curated EQE replaces the photocurrent of the same experiment
        if cur and exp == cur["experiment"]:
            eps += curated_episodes(plate, chem, cations, PL, P, cur, exp, groups, how)
            continue
        led_count = {}
        for (led, cond) in groups:
            led_count[led] = led_count.get(led, 0) + 1
        for (led, cond), tg in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            Tsel = min(tg, key=lambda T: tech_pref(T, tg[T]["bias"]))
            g = tg[Tsel]
            eid = f"{plate}_{exp}_{int(round(led))}nm"
            if led_count[led] > 1:
                eid += "_" + re.sub(r"[^A-Za-z0-9]+", "", cond[0])[:12] + f"pH{cond[1]}"
            df = tech[Tsel]["df"].loc[g["rows"]]
            rows, drops, geo = PL.candidates(df["sample_no"].to_numpy(), df["I.A_photo"].to_numpy(float))
            src = dict(base_src(Tsel), runs=sorted(x for x in g["runs"] if x), bias_V_RHE=None if g["bias"] is None else round(g["bias"], 4),
                       rcp=g["rcp"],
                       condition_lookup=how if isinstance(how, dict) and how.get("via") == "exp" else "run scan",
                       techniques_same_condition_not_selected=sorted(set(tg) - {Tsel}), **geo)
            rec = dict(episode_id=eid, n_raw=int(len(df)), n_candidates=len(rows), drops=drops, source=src)
            if len(rows) < MIN_CAND:
                P["excluded_episodes"].append(dict(rec, rule="P-I4", reason=f"{len(rows)} candidates after drops (<{MIN_CAND})"))
                continue
            P["episodes"].append(rec)
            eps.append(_episode(plate, chem, cations, eid, rows, "photocurrent_A", led, g["src"], cond, [src]))
    P["n_merit"] = len(merit_samples)
    return eps


def curated_episodes(plate, chem, cations, PL, P, cur, exp, groups, how):
    """EQE episodes from a curated deposit derived from MEAD experiment `exp`. LED from the column
    name, checked against the experiment's rcp; electrolyte/pH from the rcp and required unique."""
    eps = []
    df = pd.read_csv(cur["eqe_file"])
    df = df[df[cur["plate_col"]].astype(str) == plate].reset_index(drop=True)
    P["notes"].append(f"experiment {exp}: MEAD photocurrent groups (LED nm, technique) superseded by {cur['library']} EQE: "
                      + str(sorted((led, sorted(tg)) for (led, cond), tg in groups.items())))
    # composition cross-check against the deposit's own (XRF-interpolated) compositions
    comp_dep = df[[cur["comp_cols"][el] for el in cations]].to_numpy(float)
    comp_dep = comp_dep / comp_dep.sum(1, keepdims=True)
    ours, _ = PL.interp(positions(df[cur["sample_col"]].to_numpy()))
    dd = 0.5 * np.abs(ours - comp_dep).sum(1)
    P["notes"].append(f"{cur['library']}: merit composition cross-check vs deposit columns: median {np.nanmedian(dd):.4f}, max {np.nanmax(dd):.4f} (0.5*L1)")
    for led, col in sorted(cur["eqe_cols"].items()):
        eid = f"{plate}_{exp}_{led}nm"
        cands = [(cond, tg) for (l, cond), tg in groups.items() if abs(l - led) < 0.5]
        srcrec = dict(kind="curated EQE", library=cur["library"], file=os.path.relpath(cur["eqe_file"], ROOT),
                      column=col, experiment=exp, condition_lookup=how if isinstance(how, dict) and how.get("via") == "exp" else "run scan")
        if len(cands) != 1:
            P["excluded_episodes"].append(dict(episode_id=eid, rule="P-I2", source=srcrec,
                reason=f"LED {led} nm maps to {len(cands)} electrolyte conditions in experiment {exp} rcp data"))
            continue
        cond, tg = cands[0]
        srcs = sorted({g["src"] for g in tg.values()})
        srcrec["rcp"] = next(iter(tg.values()))["rcp"]
        rows, drops, geo = PL.candidates(df[cur["sample_col"]].to_numpy(), df[col].to_numpy(float), invalid=cur["invalid"])
        srcrec.update(geo, mead_techniques_at_this_led=sorted(tg))
        rec = dict(episode_id=eid, n_raw=int(len(df)), n_candidates=len(rows), drops=drops, source=srcrec,
                   note="replaces the MEAD photocurrent episode of the same experiment and LED")
        if len(rows) < MIN_CAND:
            P["excluded_episodes"].append(dict(rec, rule="P-I4", reason=f"{len(rows)} candidates after drops (<{MIN_CAND})"))
            continue
        P["episodes"].append(rec)
        eps.append(_episode(plate, chem, cations, eid, rows, "EQE_pct", float(led), srcs[0] if len(srcs) == 1 else ",".join(srcs), cond, [srcrec]))
    return eps


# ----------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------
def main():
    t0 = time.time()
    c = census()
    base = base_plates()
    plates = admit_plates(c)
    os.makedirs(os.path.join(OUT, "plates"), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, "plates")):
        if f.endswith(".npz"):
            os.remove(os.path.join(OUT, "plates", f))
    ledger_plates, all_eps, log = [], [], []
    for plate in sorted(plates, key=int):
        print(f"[{time.time()-t0:6.0f}s] plate {plate} {'-'.join(sorted(plates[plate]['cations']))}", flush=True)
        try:
            P, npz, eps = build_plate(c, plate, plates[plate], base, log)
        except Exception as e:
            import traceback
            traceback.print_exc()
            P = dict(plate_id=plate, chem="-".join(sorted(plates[plate]["cations"])), status="EXCLUDED",
                     rule="NOT_PROCESSED", reason=f"loader error: {type(e).__name__}: {e}", episodes=[], excluded_episodes=[])
            npz, eps = None, []
        if P["status"] is None:
            if eps:
                P["status"], P["rule"] = "ADMITTED", None
            else:
                rules = sorted({e["rule"] for e in P["excluded_episodes"]})
                P["status"], P["rule"] = "EXCLUDED", ",".join(rules) if rules else "P-I1"
                P["reason"] = "no episode passes: " + ", ".join(rules) if rules else "no photoelectrochemical merit found"
        if P["status"] == "ADMITTED":
            np.savez(os.path.join(OUT, "plates", f"{plate}.npz"), **npz)
            all_eps += eps
        P["n_episodes"] = len(P.get("episodes", []))
        tot = {}
        for e in P.get("episodes", []):
            for k, v in e["drops"].items():
                tot[k] = tot.get(k, 0) + v
        P["drops_admitted_episodes_total"] = tot
        ledger_plates.append(P)
    with open(os.path.join(OUT, "episodes.jsonl"), "w") as f:
        for e in all_eps:
            f.write(json.dumps(e) + "\n")
    write_ledger(c, plates, ledger_plates, all_eps, base)
    print(f"done in {time.time()-t0:.0f}s: {sum(p['status']=='ADMITTED' for p in ledger_plates)} plates, {len(all_eps)} episodes")


def write_ledger(c, plates, ledger_plates, all_eps, base):
    chems = {}
    for e in all_eps:
        chems[e["chem"]] = chems.get(e["chem"], 0) + 1
    df = c["plates"]
    others = []
    for _, r in df.iterrows():
        if r["status"] == "ADMIT_NEEDS_XRF":
            others.append(dict(plate_id=r["plate"], chem=r["cations"], status="EXCLUDED", rule="P-E3",
                               reason="census class ADMIT_NEEDS_XRF (no XRF composition analysis in MEAD)", processed=False))
        elif r["status"] == "PARTIAL" and int(r["n_xrd"]) == 0 and int(r["xrd_raw_only"]) > 0:
            others.append(dict(plate_id=r["plate"], chem=r["cations"], status="EXCLUDED", rule="P-E2",
                               reason="XRD only as 2D Bruker .gfrm frames", processed=False))
    others.append(dict(plate_id="2283", chem="Ni-Sb", library="bfap4-h2m21", status="EXCLUDED", rule="P-E1",
                       reason="plate 2283 is in the base environment (42gwd)", processed=False))
    others.append(dict(plate_id="3932", chem="Bi-V", library="dekcc-2tb35", status="EXCLUDED", rule="P-I1",
                       reason="13 photocurrent points and no XRD analysis (ADMIT entry lists it as not usable)", processed=False))
    notes = [
        "Scope: the 36 ADMIT library entries of discovery/siblings/sibling_ledger.json = 33 MEAD plates (mead_plates_final.csv status ADMIT) + q9zpw (plate 3594, also MEAD) + 0hj2v/ehp06 (plate 3557) + dekcc (plates 3928/3930/3933, also MEAD). One plate = one npz; sources that describe the same plate are merged per plate.",
        "Platemap: every sample number is resolved with 0057-04-1110-mp.txt (tg041 zip). Verified: q9zpw/0hj2v x,y columns and the ehp06 .udi X,Y equal the platemap positions; XRF stage coordinates follow the platemap (mirror in x) on every plate with platemap-numbered XRF.",
        "XRF raster numbering: plates 3046, 3050, 3051, 3199 carry XRF sample numbers 1..1521 (raster index, not platemap). MEAD renumbered the identical raster for plate 3059 (analysis 20160520.162518 -> 20190820.172334, identical CPS and stage columns); that index->platemap-sample map is applied when the plate's stage raster matches 3059's within 2 mm (XRF spot size); the deviation is recorded per plate (raster_max_dev_mm).",
        "Composition (P-I3): XRF FOM choice = standards-based nmol FOM (Analysis__Process_XRFS_Stds) over EDAX FP AtPerc, latest analysis first; one line per cation, K over L over M among lines with nonzero values (this reproduces MEAD's own Bi.L choice); fractions = amounts / sum over plate cations, negatives clipped to 0. Interpolation: XRF on one line (perpendicular std < 1 mm) -> 1D linear along the line (MEAD platemap_xy_line convention; the perpendicular offset of each episode's points is recorded as max_perp_offset_mm); else 2D Delaunay linear. No extrapolation: points outside the XRF extent are dropped (outside_xrf_extent). XRD compositions use the same interpolation; XRD patterns outside the extent are dropped (xrd_no_composition).",
        "XRD choice: per plate the analysis with most samples carrying a raw 1D pattern (tie: earliest); raw integrated counts (q.nm, intensity.counts), merged detector frames (Resamp_Merge_Patterns of raw frames) for multi-frame lab XRD. Plate 3557 uses the ehp06 .udi (first frame, as deposited). Q grid: identical grids kept; else the longest grid restricted to the common q-range with linear interpolation (noted per plate).",
        "Episode (P-I2): run = MEAD eche experiment (runs of one experiment pooled when their rcp electrolyte/pH/LED agree; split otherwise). For each experiment the latest analysis carrying an Analysis__Iphoto FOM for a technique is used. LED per technique from the run rcp: echem_params__<tech>.toggle_value indexes toggle_value_illumination/illumination_wavelength; toggle 0 = dark, excluded. Among techniques with the same LED and electrolyte in one experiment: CA before CV, CA bias closest to 1.23 V vs RHE (potential_vref - reference_vrhe), then lowest technique number; unselected techniques are listed in source_records. Merit = I.A_photo (A). electrolyte = rcp solution_description, ph = rcp solution_ph.",
        "Conditions: read from the experiment .exp (which embeds each run's .rcp) found in the plate's CaltechDATA records or by CaltechDATA search. When no .exp is deposited, run records within +-7 days are scanned; a runint is mapped to a run only if the run's .rcp has the plate_id and its <technique> sample files equal the analysis runint's sample set. Rows without a readable condition are EXCLUDED under P-I2 (never guessed).",
        "Curated EQE: plate 3594 (q9zpw SLF9_EQE_comp.csv, eqe*_pct columns) and plate 3557 (0hj2v Fig2_3_4_eqe_scatterplot.csv, EQE_pct_* columns, -9 = invalid) are derived from MEAD experiments 20170802.122251 and 20170802.130408; their EQE episodes replace the MEAD photocurrent episodes of those experiments (no duplicate episodes). LED = column wavelength, checked against the experiment rcp; electrolyte/pH from the rcp.",
        "dekcc-2tb35 (Bi-Cu-V/Bi-Cu/Cu-V): its I_illdiff at 15 CV potentials has no pre-declared single potential and comes from the same MEAD plates 3928/3930/3933; merits are taken from the MEAD Iphoto FOMs of those plates instead.",
        "Candidate drops, in order: duplicate_sample (keep first row as listed), merit_invalid (non-finite, or the deposit's -9), no_platemap_position, outside_xrf_extent, xrd_dist_gt_0.05 (nearest XRD by 0.5*L1 over cation fractions). Negative photocurrents are finite measured values and are kept. Then P-I4 (>=15).",
        "Pre-check: experiments whose Iphoto FOM holds <15 distinct samples in total are EXCLUDED under P-I4 without resolving conditions.",
        "Cross-check (sources.xrf.mead_interp_crosscheck per plate): where MEAD's own FOM_Interp_Merge_Ana used platemap-numbered XRF, our compositions agree with MEAD's (median 0.5*L1 0.0000-0.0103 on 3059, 3067, 3071, 3202, 3214, 3215, 3446, 3448, 3455, 3459, 3925); curated deposits agree too (3594 q9zpw median 0.0000, max 0.016; 3557 0hj2v median 0.0000, max 0.024; 3557 .udi XRD comps max 0.005). Disagreements: (a) raster-numbered plates 3046/3050/3051/3199 (median 0.06-0.19): MEAD's 2019 values are non-monotonic along the line, consistent with MEAD reading raster indices 1..1521 as platemap numbers; our raster-mapped XRF maps are as spatially smooth as platemap-numbered 1521-point maps (nearest-neighbour |dF| 0.005-0.007 vs 0.009 on 3059/3102) and give monotonic gradients; (b) 3224 (median 0.099): MEAD's platemap_xy_line took x as the line axis on a vertical line and returned one constant composition; the three XRF columns of 3224 agree with each other at equal y, and ours varies monotonically with y.",
        "Line libraries (XRF on one line): candidates keep the XRF composition at their along-line coordinate whatever their perpendicular offset (MEAD convention); the largest offset per episode is recorded as max_perp_offset_mm (maximum 24.4 mm, plate 3112).",
        "Electrolyte field = rcp original_solution_description (as entered at measurement) when present, else solution_description; pH = rcp solution_ph. Episodes are split whenever any electrolyte field differs between runs.",
        "Substrate: FTO where stated by the deposit's paper (3594 J Phys Energy 2022; 3928/3930/3933 npj Comput Mater 2022); '' otherwise. annealT_C: census max_temperature; -1 when unknown.",
    ]
    for P in ledger_plates:
        for n in P.get("notes", []):
            pass
    combined = sorted(e["episode_id"] for e in all_eps if "+" in str(e["illum"].get("source", "")))
    if combined:
        notes.append("FLAG for the caller: episodes " + ", ".join(combined) + " use illumination_source 'Doric LEDc2 388+W35' "
                     "(a 388 nm LED channel combined with a white W35 LED; npj Comput Mater 2022 describes it as 388 nm + white light). "
                     "The illumination is fixed within each episode and illumination_wavelength reads 388, so they are admitted; "
                     "drop them if P-I2 'exactly one LED' is read as a single emitter.")
    not_proc = [p for p in ledger_plates if p.get("rule") == "NOT_PROCESSED"]
    completeness = ("All 34 in-scope plates were processed" if not not_proc else
                    f"{len(ledger_plates)-len(not_proc)} of {len(ledger_plates)} in-scope plates processed; not processed: "
                    + "; ".join(f"{p['plate_id']} ({p['reason']})" for p in not_proc))
    completeness += (". Not processed by design: census PARTIAL/REJECT entries (not ADMIT), ADMIT_NEEDS_XRF plates (P-E3, listed), "
                     "2D-frame-only plates (P-E2, listed), bfap4 plate 2283 (P-E1). MEAD eche experiments without a deposited .exp and without "
                     "matching run records have their rows EXCLUDED under P-I2 (listed per plate).")
    L = dict(
        built_by="bench/pool_loader.py", rules="rev21/pool/POOL_RULES.md (frozen 2026-09-18)", date=time.strftime("%Y-%m-%d"),
        libraries=_library_map(ledger_plates),
        plates=ledger_plates, not_in_scope_or_excluded_by_class=others,
        totals=dict(n_plates=sum(p["status"] == "ADMITTED" for p in ledger_plates), n_episodes=len(all_eps),
                    n_chemistries=len(chems), chemistries=dict(sorted(chems.items())),
                    excluded_plates={p["plate_id"]: p.get("rule") for p in ledger_plates if p["status"] != "ADMITTED"},
                    excluded_episodes_by_rule=_count_rules(ledger_plates)),
        notes=notes, completeness=completeness)
    json.dump(L, open(LEDGER, "w"), indent=1, default=_jsonable)


def _library_map(ps):
    """The 36 ADMIT library entries of sibling_ledger.json -> pooled plate(s) and their status."""
    st = {p["plate_id"]: p["status"] + (f" ({p['rule']})" if p.get("rule") else "") for p in ps}
    out = {"q9zpw-g8s64 + MEAD 7qy17-9az58": {"3594": st.get("3594")},
           "0hj2v-qwv46 + ehp06-pcf04": {"3557": st.get("3557")},
           "dekcc-2tb35 (+ MEAD XRD analyses, DRNets)": {"3928": st.get("3928"), "3930": st.get("3930"),
                                                         "3933": st.get("3933"), "3932": "EXCLUDED (P-I1)"}}
    for p in ps:
        if p["plate_id"] != "3557":
            out[f"MEAD plate {p['plate_id']}"] = {p["plate_id"]: st[p["plate_id"]]}
    return out


def _count_rules(ps):
    out = {}
    for p in ps:
        for e in p.get("excluded_episodes", []):
            out[e["rule"]] = out.get(e["rule"], 0) + 1
    return out


def _jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (set, tuple)):
        return sorted(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


if __name__ == "__main__":
    main()
