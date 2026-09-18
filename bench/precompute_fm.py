"""Precompute MACE formation energies, MACE hull and MEGNet gaps for every MP phase in each M-Sb-O system.

Writes env/cache/fm_summary/<M>.json. The FM floor reads these; the FM arm's tools compute the
same numbers on demand (shared cache, identical values).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm, data
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from pymatgen.core import Composition

OUT = os.path.join(fm.CACHE, "fm_summary")
os.makedirs(OUT, exist_ok=True)


def system_summary(M):
    path = os.path.join(OUT, f"{M}.json")
    if os.path.exists(path):
        return json.load(open(path))
    entries, rows = [], []
    for sysl in ([M, "Sb", "O"], [M, "O"], ["Sb", "O"]):
        for r in fm.chemsys_structures(sysl):
            if r["nsites"] > fm.MAX_SITES:
                rows.append(dict(id=r["id"], formula=r["formula"], skipped=f"{r['nsites']} sites")); continue
            s = fm.to_structure(r)
            m = fm.mace_relax(s)
            if "energy_per_atom_eV" not in m:
                rows.append(dict(id=r["id"], formula=r["formula"], skipped=m.get("error"))); continue
            ef = fm.formation_energy(s, m["energy_per_atom_eV"])
            comp = s.composition
            entries.append(PDEntry(comp, ef * comp.num_atoms, name=r["id"]))
            nm, nsb = comp[M] if M in comp else 0, comp["Sb"] if "Sb" in comp else 0
            rows.append(dict(id=r["id"], formula=r["formula"], nsites=r["nsites"], ef_eV_atom=round(ef, 4),
                             sb_frac=round(nsb / (nm + nsb), 4) if nm + nsb else None,
                             ternary=len(comp.elements) == 3))
    for el in (M, "Sb", "O"):
        entries.append(PDEntry(Composition(el), 0.0, name=f"ref_{el}"))
    pd_ = PhaseDiagram(entries)
    ehull = {e.name: pd_.get_e_above_hull(e) for e in entries}
    for row in rows:
        if "ef_eV_atom" in row:
            row["ehull_eV_atom"] = round(float(ehull[row["id"]]), 4)
            if row["ternary"]:
                r = next(x for x in fm.chemsys_structures([M, "Sb", "O"]) if x["id"] == row["id"])
                row["megnet_gap_pbe_eV"] = round(fm.megnet_gap(fm.to_structure(r), 0)["gap_eV"], 3)
                row["megnet_gap_hse_eV"] = round(fm.megnet_gap(fm.to_structure(r), 2)["gap_eV"], 3)
    out = dict(element=M, n_phases=len(rows), rows=rows,
               model="MACE-MP-0 medium float64 FIRE+FrechetCellFilter fmax0.05 150 steps; MEGNet-BandGap-mfi-MP-2019.4.1")
    json.dump(out, open(path, "w"), indent=1)
    return out


if __name__ == "__main__":
    els = sorted({e["el"] for e in data.episodes()})
    for M in els:
        t = time.time()
        s = system_summary(M)
        tern = [r for r in s["rows"] if r.get("ternary")]
        print(M, len(s["rows"]), "phases,", len(tern), "ternary,", f"{time.time()-t:.0f}s", flush=True)
        for r in sorted(tern, key=lambda r: r["ehull_eV_atom"])[:4]:
            print("   ", r["id"], r["formula"], "sb", r["sb_frac"], "ehull", r["ehull_eV_atom"],
                  "gap(pbe,hse)", r.get("megnet_gap_pbe_eV"), r.get("megnet_gap_hse_eV"), flush=True)
