"""Episode MCP server: one process per (episode, arm). Holds the hidden map; reveals only what is measured.

Arms: bare (env only), classical (env + classical), fm (env + classical + FM).
Every call is appended to <out>/calls.jsonl with a receipt id; the scorer reads only env.json.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "bench"))
from mcp.server.mcpserver import MCPServer

ap = argparse.ArgumentParser()
ap.add_argument("--episode", required=True)
ap.add_argument("--arm", choices=("bare", "classical", "fm", "stub"), required=True)
ap.add_argument("--out", required=True)
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)

import data, classical, floors
from pymatgen.core import Structure

if A.arm == "stub":   # R1 synthetic item: no domain data
    EP = dict(episode_id="synthetic", el="X", sb=[0.1, 0.3, 0.5, 0.7, 0.9], eqe=[0.1, 0.4, 1.0, 0.3, 0.2],
              nearest_xrd=[0, 1, 2, 3, 4], led_eV=3.2, ph=7.0, electrolyte="none", substrate="none", annealT_C=0,
              plate_id=None)
else:
    EP = data.episode(A.episode)
STATE = dict(eqe={}, xrd={}, submitted=None, hypos={}, n_calls=0)
B_EQE, B_XRD = floors.B_EQE, floors.B_XRD
mcp = MCPServer(f"env-{A.arm}", version="1.0.0")


def _log(tool, args, result):
    STATE["n_calls"] += 1
    rid = hashlib.sha256(f"{A.episode}|{A.arm}|{STATE['n_calls']}|{tool}|{json.dumps(args, sort_keys=True)}".encode()).hexdigest()[:12]
    with open(os.path.join(A.out, "calls.jsonl"), "a") as f:
        f.write(json.dumps(dict(t=time.time(), n=STATE["n_calls"], tool=tool, args=args, receipt=rid,
                                result=result if len(json.dumps(result)) < 4000 else "<large>")) + "\n")
    json.dump(dict(episode=EP["episode_id"], arm=A.arm, eqe=STATE["eqe"], xrd=list(STATE["xrd"]),
                   submitted=STATE["submitted"], n_calls=STATE["n_calls"]),
              open(os.path.join(A.out, "env.json"), "w"))
    if isinstance(result, dict):
        result = dict(result, receipt=rid)
    return result


def _idx(i):
    i = int(i)
    if not 0 <= i < len(EP["sb"]):
        raise ValueError(f"index must be 0..{len(EP['sb'])-1}")
    return i


# ------------------------------------------------------------------ environment tools (all arms)
@mcp.tool(name="episode_info")
def episode_info() -> dict:
    """Describe the combinatorial plate, the measurement conditions, the candidate compositions and remaining budgets."""
    r = dict(system=f"{EP['el']}-Sb-O thin-film composition line", element=EP["el"], substrate=EP["substrate"],
             anneal_T_C=EP["annealT_C"], electrolyte_pH=EP["ph"], illumination_photon_energy_eV=EP["led_eV"],
             candidates=[dict(index=i, sb_fraction=s) for i, s in enumerate(EP["sb"])],
             sb_fraction_definition="Sb/(M+Sb) cation fraction",
             budget_remaining=dict(eqe=B_EQE - len(STATE["eqe"]), xrd=B_XRD - len(STATE["xrd"])))
    return _log("episode_info", {}, r)


@mcp.tool(name="measure_eqe")
def measure_eqe(index: int) -> dict:
    """Spend one EQE measurement (photoelectrochemical external quantum efficiency, %) on candidate `index`."""
    i = _idx(index)
    if i in STATE["eqe"]:
        return _log("measure_eqe", {"index": i}, dict(index=i, eqe_pct=STATE["eqe"][i], note="already measured; no budget spent"))
    if len(STATE["eqe"]) >= B_EQE:
        return _log("measure_eqe", {"index": i}, dict(error="EQE budget exhausted"))
    v = round(float(EP["eqe"][i]), 5)
    STATE["eqe"][i] = v
    return _log("measure_eqe", {"index": i}, dict(index=i, sb_fraction=EP["sb"][i], eqe_pct=v,
                                                 eqe_budget_remaining=B_EQE - len(STATE["eqe"])))


@mcp.tool(name="measure_xrd")
def measure_xrd(index: int) -> dict:
    """Spend one XRD measurement on candidate `index`. Returns the strongest background-subtracted peaks (Q in 1/Angstrom, relative intensity)."""
    i = _idx(index)
    if len(STATE["xrd"]) >= B_XRD and i not in STATE["xrd"]:
        return _log("measure_xrd", {"index": i}, dict(error="XRD budget exhausted"))
    if A.arm == "stub":
        pk = [(1.8, 100.0), (2.6, 40.0)]
    else:
        p = data.plates()[EP["plate_id"]]
        pk = classical.peaks(p["Q"], p["xrd"][EP["nearest_xrd"][i]], n=20)
    STATE["xrd"][i] = pk
    return _log("measure_xrd", {"index": i}, dict(index=i, sb_fraction=EP["sb"][i], peaks_Q_invA_relI=pk,
                                                 xrd_budget_remaining=B_XRD - len(STATE["xrd"])))


@mcp.tool(name="submit")
def submit(best_index: int, rationale: str, rejected: list[dict] | None = None) -> dict:
    """Finish the episode. best_index: the composition you judge best among those measured. rationale: why.
    rejected: optional list of {"index" or "hypothesis": ..., "reason": ...} for alternatives you ruled out."""
    STATE["submitted"] = dict(best_index=int(best_index), rationale=rationale[:4000], rejected=rejected or [])
    return _log("submit", {"best_index": int(best_index)}, dict(ok=True, eqe_measured=len(STATE["eqe"]), xrd_measured=len(STATE["xrd"])))


# ------------------------------------------------------------------ classical tools
if A.arm in ("classical", "fm"):
    import fm

    def _phase_structure(pid):
        if pid in STATE["hypos"]:
            return Structure.from_dict(STATE["hypos"][pid])
        for sysl in ([EP["el"], "Sb", "O"], [EP["el"], "O"], ["Sb", "O"]):
            for r in fm.chemsys_structures(sysl):
                if r["id"] == pid:
                    return fm.to_structure(r)
        raise ValueError(f"unknown phase id {pid}")

    @mcp.tool(name="list_phases")
    def list_phases() -> dict:
        """List known crystal structures (Materials Project) in the M-Sb-O, M-O and Sb-O systems: id, formula, sites, Sb cation fraction. No energies."""
        out = []
        for sysl in ([EP["el"], "Sb", "O"], [EP["el"], "O"], ["Sb", "O"]):
            for r in fm.chemsys_structures(sysl):
                if r["nsites"] > fm.MAX_SITES: continue
                c = fm.to_structure(r).composition
                nm = c[EP["el"]] if EP["el"] in c else 0; nsb = c["Sb"] if "Sb" in c else 0
                out.append(dict(id=r["id"], formula=r["formula"], nsites=r["nsites"],
                                sb_fraction=round(nsb / (nm + nsb), 3) if nm + nsb else None))
        return _log("list_phases", {}, dict(phases=out, n=len(out)))

    @mcp.tool(name="substitute_structure")
    def substitute_structure(phase_id: str, from_element: str, to_element: str) -> dict:
        """Build a hypothetical structure by replacing every `from_element` site of a known phase (any chemical system) with `to_element`. Returns a new id usable by other tools."""
        s = None
        for sysl in ([EP["el"], "Sb", "O"], [EP["el"], "O"], ["Sb", "O"]):
            for r in fm.chemsys_structures(sysl):
                if r["id"] == phase_id: s = fm.to_structure(r)
        if s is None:
            q = phase_id
            s = _phase_structure(q) if q in STATE["hypos"] else None
        if s is None:
            return _log("substitute_structure", dict(phase_id=phase_id), dict(error="phase id not in this system; use list_phases ids or a prior hypothetical id"))
        s = s.copy(); s.replace_species({from_element: to_element})
        hid = "hyp-" + fm.struct_hash(s)[:8]
        STATE["hypos"][hid] = s.as_dict()
        return _log("substitute_structure", dict(phase_id=phase_id, from_element=from_element, to_element=to_element),
                    dict(id=hid, formula=s.composition.reduced_formula, nsites=len(s)))

    @mcp.tool(name="simulate_xrd")
    def simulate_xrd(phase_id: str) -> dict:
        """Simulated powder XRD peaks (Q in 1/Angstrom, relative intensity) for a phase id or hypothetical id."""
        s = _phase_structure(phase_id)
        return _log("simulate_xrd", dict(phase_id=phase_id), dict(id=phase_id, peaks_Q_invA_relI=classical.sim_peaks(s, phase_id)))

    @mcp.tool(name="match_xrd")
    def match_xrd(index: int, phase_ids: list[str]) -> dict:
        """Cosine similarity (0-1, best over a small rigid Q shift) between the measured XRD at `index` (must already be measured) and simulated patterns of the given phases."""
        i = _idx(index)
        if i not in STATE["xrd"]:
            return _log("match_xrd", dict(index=i), dict(error="measure_xrd at this index first"))
        p = data.plates()[EP["plate_id"]]
        ym = classical.measured_on_grid(p["Q"], p["xrd"][EP["nearest_xrd"][i]])
        res = {pid: classical.match(ym, classical.simulate(_phase_structure(pid), pid)) for pid in phase_ids[:40]}
        return _log("match_xrd", dict(index=i, phase_ids=phase_ids[:40]), dict(index=i, similarity=res))

    @mcp.tool(name="gp_suggest")
    def gp_suggest() -> dict:
        """Gaussian-process UCB suggestion for the next EQE measurement from the EQE values measured so far (RBF kernel on Sb fraction)."""
        x = np.array(EP["sb"]); idx = list(STATE["eqe"]); y = [STATE["eqe"][i] for i in idx]
        if not idx:
            return _log("gp_suggest", {}, dict(next_index=len(x) // 2, note="no observations; middle of line"))
        n, mu, sd = classical.ucb_next(x, idx, y)
        top = np.argsort(-(mu + 2 * sd))[:5]
        return _log("gp_suggest", {}, dict(next_index=n, top5=[dict(index=int(t), mean=round(float(mu[t]), 4), sd=round(float(sd[t]), 4)) for t in top]))

# ------------------------------------------------------------------ foundation-model tools
if A.arm == "fm":
    import json as _j
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
    from pymatgen.core import Composition

    @mcp.tool(name="mace_stability")
    def mace_stability(phase_id: str) -> dict:
        """MACE-MP-0 (universal ML interatomic potential): relax the structure and return formation energy and energy above the convex hull (eV/atom) against all known phases of the system."""
        s = _phase_structure(phase_id)
        m = fm.mace_relax(s)
        if "energy_per_atom_eV" not in m:
            return _log("mace_stability", dict(phase_id=phase_id), dict(error=m.get("error")))
        ef = fm.formation_energy(s, m["energy_per_atom_eV"])
        rows = floors.fm_rows(EP["el"])
        ents = [PDEntry(Composition(r["formula"]), r["ef_eV_atom"] * Composition(r["formula"]).num_atoms, name=pid) for pid, r in rows.items()]
        ents += [PDEntry(Composition(e), 0.0, name="ref_" + e) for e in (EP["el"], "Sb", "O")]
        me = PDEntry(s.composition, ef * s.composition.num_atoms, name="query")
        pd_ = PhaseDiagram(ents + [me])
        return _log("mace_stability", dict(phase_id=phase_id), dict(id=phase_id, formula=s.composition.reduced_formula,
                    formation_energy_eV_atom=round(ef, 4), e_above_hull_eV_atom=round(float(pd_.get_e_above_hull(me)), 4)))

    @mcp.tool(name="megnet_bandgap")
    def megnet_bandgap(phase_id: str, fidelity: str = "hse") -> dict:
        """MEGNet multi-fidelity graph network band-gap prediction (eV) for a phase or hypothetical id. fidelity: pbe | gllb | hse | scan."""
        f = {"pbe": 0, "gllb": 1, "hse": 2, "scan": 3}.get(fidelity, 2)
        s = _phase_structure(phase_id)
        g = fm.megnet_gap(s, f)
        return _log("megnet_bandgap", dict(phase_id=phase_id, fidelity=fidelity), dict(id=phase_id, gap_eV=round(g["gap_eV"], 3), fidelity=fidelity))


if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run_stdio_async())
