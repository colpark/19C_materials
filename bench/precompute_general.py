"""FM summary for an arbitrary cation set (pooled libraries). Same channel as precompute_fm.py:
MACE-MP-0 medium hull (binaries <= 30 sites, others <= 80) and MEGNet HSE/PBE gaps for mixed-cation phases.

Writes env/cache/fm_summary_general/<chem>.json with, per phase, the cation fraction vector over the chem's elements.
    python bench/precompute_general.py Ag-V Bi-Cu-V ...
"""
import itertools, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from pymatgen.core import Composition

OUT = os.path.join(fm.CACHE, "fm_summary_general" + fm.MACE_TAG)
os.makedirs(OUT, exist_ok=True)
BINARY_MAX_SITES = 30


def summary(chem):
    path = os.path.join(OUT, f"{chem}.json")
    if os.path.exists(path):
        return json.load(open(path))
    cats = sorted(chem.split("-"))
    entries, rows = [], []
    for r_ in range(1, len(cats) + 1):
        for sub in itertools.combinations(cats, r_):
            sysl = list(sub) + ["O"]
            for r in fm.chemsys_structures(sysl):
                cap = BINARY_MAX_SITES if len(sysl) == 2 else fm.MAX_SITES
                if r["nsites"] > cap:
                    rows.append(dict(id=r["id"], formula=r["formula"], skipped=f"{r['nsites']} sites > cap {cap}")); continue
                s = fm.to_structure(r); m = fm.mace_relax(s)
                if "energy_per_atom_eV" not in m:
                    rows.append(dict(id=r["id"], formula=r["formula"], skipped=m.get("error"))); continue
                ef = fm.formation_energy(s, m["energy_per_atom_eV"]); comp = s.composition
                entries.append(PDEntry(comp, ef * comp.num_atoms, name=r["id"]))
                tot = sum(comp[c] for c in cats if c in comp)
                rows.append(dict(id=r["id"], formula=r["formula"], nsites=r["nsites"], ef_eV_atom=round(ef, 4),
                                 frac={c: round((comp[c] if c in comp else 0) / tot, 4) for c in cats},
                                 mixed=len(sub) >= 2))
    for el in cats + ["O"]:
        entries.append(PDEntry(Composition(el), 0.0, name=f"ref_{el}"))
    pd_ = PhaseDiagram(entries)
    eh = {e.name: pd_.get_e_above_hull(e) for e in entries}
    for row in rows:
        if "ef_eV_atom" in row:
            row["ehull_eV_atom"] = round(float(eh[row["id"]]), 4)
            if row["mixed"]:
                present = sorted(k for k in row["frac"] if row["frac"][k] > 0) + ["O"]
                s = fm.to_structure(next(x for x in fm.chemsys_structures(present) if x["id"] == row["id"]))
                row["megnet_gap_pbe_eV"] = round(fm.megnet_gap(s, 0)["gap_eV"], 3)
                row["megnet_gap_hse_eV"] = round(fm.megnet_gap(s, 2)["gap_eV"], 3)
    out = dict(chem=chem, elements=cats, n_phases=len(rows), rows=rows, model=f"MACE {fm.MACE_MODEL} float64; MEGNet-BandGap-mfi-MP-2019.4.1")
    json.dump(out, open(path, "w"), indent=1)
    return out


if __name__ == "__main__":
    for chem in sys.argv[1:]:
        t = time.time(); s = summary(chem)
        mixed = [r for r in s["rows"] if r.get("mixed") and "ehull_eV_atom" in r]
        print(chem, len(s["rows"]), "phases,", len(mixed), "mixed-cation,", f"{time.time()-t:.0f}s", flush=True)
