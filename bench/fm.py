"""Structure lookup (classical) and foundation-model channels (MACE-MP-0 energy, MEGNet band gap).

Tool roles, per manifest.md:
  - structure lookup and substitution: classical; the agent constructs a hypothetical structure
  - XRD simulation: classical forward simulator (pymatgen), see classical.py
  - MACE-MP-0 relaxed energy + convex hull: FM simulator / scorer on an agent-built input
  - MEGNet multi-fidelity band gap: FM predictor on an agent-built input
Results are cached by a structure content hash so the floors and the arms read identical numbers.
"""
from __future__ import annotations
import hashlib, json, os, threading, urllib.parse, urllib.request, warnings
import numpy as np
from pymatgen.core import Structure, Lattice, Composition

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "env", "cache")
os.makedirs(os.path.join(CACHE, "optimade"), exist_ok=True)
MAX_SITES = 80
MACE_MODEL = os.environ.get("FMAB_MACE_MODEL", "medium")          # rev2.1 swap: "medium-mpa-0"
MACE_TAG = "" if MACE_MODEL == "medium" else "_" + MACE_MODEL.replace("-", "")
_lock = threading.Lock()

# ---------------------------------------------------------------- structure lookup (classical)
def _optimade(filter_):
    out, url = [], "https://optimade.materialsproject.org/v1/structures?" + urllib.parse.urlencode({
        "filter": filter_, "page_limit": 100,
        "response_fields": "chemical_formula_reduced,nsites,lattice_vectors,species_at_sites,cartesian_site_positions"})
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 fmab-materials"})
        d = json.load(urllib.request.urlopen(req, timeout=120))
        out += d["data"]
        url = d.get("links", {}).get("next")
        if isinstance(url, dict): url = url.get("href")
    return out


def chemsys_structures(elements):
    """All MP structures whose elements are exactly `elements` (cached)."""
    key = "-".join(sorted(elements))
    path = os.path.join(CACHE, "optimade", key + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    els = ",".join(f'"{e}"' for e in sorted(elements))
    data = _optimade(f"elements HAS ALL {els} AND nelements={len(elements)}")
    recs = []
    for x in data:
        a = x["attributes"]
        recs.append(dict(id=x["id"], formula=a["chemical_formula_reduced"], nsites=a["nsites"],
                         lattice=a["lattice_vectors"], species=a["species_at_sites"],
                         cart=a["cartesian_site_positions"]))
    _atomic_dump(recs, path)
    return recs


def to_structure(rec):
    return Structure(Lattice(rec["lattice"]), rec["species"], rec["cart"], coords_are_cartesian=True)


def struct_hash(s: Structure):
    s = s.get_sorted_structure()
    blob = json.dumps([np.round(s.lattice.matrix, 3).tolist(), [str(x.specie) for x in s],
                       np.round(s.frac_coords % 1.0, 3).tolist()])
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- FM channels
_mace = None
_megnet = None


def _get_mace():
    global _mace
    if _mace is None:
        import torch
        from mace.calculators import mace_mp
        _mace = mace_mp(model=MACE_MODEL, device="cuda" if torch.cuda.is_available() else "cpu",
                        default_dtype="float64")
    return _mace


def _get_megnet():
    global _megnet
    if _megnet is None:
        import matgl
        _megnet = matgl.load_model("MEGNet-BandGap-mfi-MP-2019.4.1")
    return _megnet


def _cache_get(kind, h):
    p = os.path.join(CACHE, kind, h + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def _atomic_dump(obj, path):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w") as f: json.dump(obj, f)
    os.replace(tmp, path)          # concurrent workers: last writer wins, readers never see a partial file


def _cache_put(kind, h, obj):
    os.makedirs(os.path.join(CACHE, kind), exist_ok=True)
    _atomic_dump(obj, os.path.join(CACHE, kind, h + ".json"))


def mace_relax(s: Structure, steps=150, fmax=0.05):
    """Relaxed total energy per atom and relaxed structure (positions + cell), MACE-MP-0 medium."""
    h = struct_hash(s)
    c = _cache_get("mace" + MACE_TAG, h)
    if c: return c
    if len(s) > MAX_SITES:
        return {"hash": h, "error": f"{len(s)} sites exceeds cap {MAX_SITES}"}
    from ase.optimize import FIRE
    from ase.filters import FrechetCellFilter
    from pymatgen.io.ase import AseAtomsAdaptor
    with _lock:
        atoms = AseAtomsAdaptor.get_atoms(s)
        atoms.calc = _get_mace()
        opt = FIRE(FrechetCellFilter(atoms), logfile=None)
        opt.run(fmax=fmax, steps=steps)
        e = float(atoms.get_potential_energy()) / len(atoms)
        rs = AseAtomsAdaptor.get_structure(atoms)
    out = {"hash": h, "energy_per_atom_eV": e, "n_sites": len(s), "steps": steps,
           "relaxed": rs.as_dict(), "formula": s.composition.reduced_formula}
    _cache_put("mace" + MACE_TAG, h, out)
    return out


def megnet_gap(s: Structure, fidelity=0):
    """MEGNet multi-fidelity band gap (eV); fidelity 0=PBE, 1=GLLB-SC, 2=HSE, 3=SCAN."""
    import torch
    h = struct_hash(s) + f"_f{fidelity}"
    c = _cache_get("megnet", h)
    if c: return c
    with _lock:
        g = float(_get_megnet().predict_structure(s, state_attr=torch.tensor([fidelity])))
    out = {"hash": h, "gap_eV": max(g, 0.0), "fidelity": fidelity, "formula": s.composition.reduced_formula}
    _cache_put("megnet", h, out)
    return out


# ---------------------------------------------------------------- hull from MACE energies
O2_REF = None


def ref_energy(el):
    """Elemental reference energy per atom (MACE), lowest over MP elemental structures <= MAX_SITES."""
    p = _cache_get("ref" + MACE_TAG, el)
    if p: return p["e"]
    if el == "O":
        from ase import Atoms
        from pymatgen.io.ase import AseAtomsAdaptor
        a = Atoms("O2", positions=[[0, 0, 0], [0, 0, 1.21]], cell=[12, 12, 12], pbc=True)
        s = AseAtomsAdaptor.get_structure(a)
        from ase.optimize import BFGS
        with _lock:
            a.calc = _get_mace(); BFGS(a, logfile=None).run(fmax=0.02, steps=100)
            e = float(a.get_potential_energy()) / 2
    else:
        es = []
        for r in chemsys_structures([el]):
            if r["nsites"] <= 16:
                m = mace_relax(to_structure(r))
                if "energy_per_atom_eV" in m: es.append(m["energy_per_atom_eV"])
        e = min(es)
    _cache_put("ref" + MACE_TAG, el, {"e": e})
    return e


def formation_energy(s: Structure, e_per_atom):
    comp = s.composition
    n = comp.num_atoms
    return (e_per_atom * n - sum(ref_energy(str(el)) * amt for el, amt in comp.items())) / n
