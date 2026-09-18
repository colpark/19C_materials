"""Pooled-cohort episode server (rev 2.3 pass). One process per (episode, arm).

Arms:
  bare       env tools only
  classical  env + classical tools
  fm_forced  env + classical + FM tools, and the forced-consultation lift: every merit measurement must be preceded by
             record_consultation(index, receipts, verdict) citing >= 1 FM receipt (mace_stability / megnet_bandgap)
             issued since the previous merit measurement (PI standing ruling 2026-09-19, scope pooled cohort).
  stub       synthetic item for R1
Every call is appended to <out>/calls.jsonl with a receipt; env.json holds what was measured (the blind file source).
"""
from __future__ import annotations
import argparse, functools, hashlib, itertools, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "bench"))
from mcp.server.mcpserver import MCPServer

ap = argparse.ArgumentParser()
ap.add_argument("--episode", required=True)
ap.add_argument("--arm", choices=("bare", "classical", "fm_forced", "stub"), required=True)
ap.add_argument("--out", required=True)
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)

import pool_floors as P, classical
from pymatgen.core import Structure

if A.arm == "stub":
    EP = dict(episode_id="synthetic", source="stub", chem="X-Y", elements=["X", "Y"], plate_id=None,
              comp=[[0.9, 0.1], [0.7, 0.3], [0.5, 0.5], [0.3, 0.7], [0.1, 0.9]], merit=[0.1, 0.4, 1.0, 0.3, 0.2],
              nearest_xrd=[0, 1, 2, 3, 4], led_eV=3.2)
    MERIT_NAME = "EQE_pct"
else:
    EP = next(e for e in P.all_episodes() if e["episode_id"] == A.episode)
    if EP["source"] == "base":
        MERIT_NAME = "EQE_pct"
    else:
        raw = next(json.loads(l) for l in open(os.path.join(ROOT, "env/pool/episodes.jsonl")) if "P" + json.loads(l)["episode_id"] == A.episode)
        MERIT_NAME = raw.get("merit_name", "photocurrent_A")
B_EQE, B_XRD = P.B_EQE, P.B_XRD
STATE = dict(merit={}, xrd={}, submitted=None, hypos={}, n_calls=0, receipts={}, fm_since_last=[], consult={}, consultations=[])
mcp = MCPServer(f"env-{A.arm}", version="2.3.0")
_orig_tool = mcp.tool


def _safe_tool(*targs, **tkw):
    deco = _orig_tool(*targs, **tkw)
    def wrap(fn):
        @functools.wraps(fn)
        def inner(*a, **k):
            try:
                return fn(*a, **k)
            except Exception as ex:
                return _log(tkw.get("name", fn.__name__), dict(args=[str(x) for x in a], **{kk: str(v) for kk, v in k.items()}),
                            dict(error=f"{type(ex).__name__}: {str(ex)[:300]}"))
        return deco(inner)
    return wrap


mcp.tool = _safe_tool


def _log(tool, args, result):
    STATE["n_calls"] += 1
    rid = hashlib.sha256(f"{A.episode}|{A.arm}|{STATE['n_calls']}|{tool}|{json.dumps(args, sort_keys=True)}".encode()).hexdigest()[:12]
    STATE["receipts"][rid] = tool
    if tool in ("mace_stability", "megnet_bandgap") and isinstance(result, dict) and "error" not in result:
        STATE["fm_since_last"].append(rid)
    with open(os.path.join(A.out, "calls.jsonl"), "a") as f:
        f.write(json.dumps(dict(t=time.time(), n=STATE["n_calls"], tool=tool, args=args, receipt=rid,
                                result=result if len(json.dumps(result)) < 4000 else "<large>")) + "\n")
    json.dump(dict(episode=EP["episode_id"], arm=A.arm, eqe=STATE["merit"], xrd=list(STATE["xrd"]), submitted=STATE["submitted"],
                   n_calls=STATE["n_calls"], consultations=STATE["consultations"]), open(os.path.join(A.out, "env.json"), "w"))
    if isinstance(result, dict):
        result = dict(result, receipt=rid)
    return result


def _idx(i):
    i = int(i)
    if not 0 <= i < len(EP["merit"]):
        raise ValueError(f"index must be 0..{len(EP['merit'])-1}")
    return i


def _comp(i):
    return {el: round(float(x), 4) for el, x in zip(EP["elements"], EP["comp"][i])}


# ------------------------------------------------------------------ environment tools (all arms)
@mcp.tool(name="episode_info")
def episode_info() -> dict:
    """Describe the combinatorial library, the measurement conditions, the candidate compositions and remaining budgets."""
    r = dict(system=f"{'-'.join(EP['elements'])} oxide thin-film composition library", cations=EP["elements"],
             geometry="composition line" if len(EP["elements"]) == 2 else "composition spread",
             illumination_photon_energy_eV=(round(EP["led_eV"], 2) if EP.get("led_eV") else "as deposited (single fixed lamp)"),
             merit=MERIT_NAME, candidates=[dict(index=i, cation_fractions=_comp(i)) for i in range(len(EP["merit"]))],
             budget_remaining=dict(merit=B_EQE - len(STATE["merit"]), xrd=B_XRD - len(STATE["xrd"])))
    return _log("episode_info", {}, r)


MEASURE_DOC = ("Spend one photoelectrochemical merit measurement (EQE in % or photocurrent in A, as named by episode_info) on candidate `index`."
               + (" FORCED CONSULTATION: allowed only after record_consultation for this same index, citing at least one mace_stability or "
                  "megnet_bandgap receipt obtained since your previous merit measurement." if A.arm == "fm_forced" else ""))


@mcp.tool(name="measure_eqe", description=MEASURE_DOC)
def measure_eqe(index: int) -> dict:
    i = _idx(index)
    if i in STATE["merit"]:
        return _log("measure_eqe", {"index": i}, dict(index=i, merit=STATE["merit"][i], note="already measured; no budget spent"))
    if len(STATE["merit"]) >= B_EQE:
        return _log("measure_eqe", {"index": i}, dict(error="merit budget exhausted"))
    if A.arm == "fm_forced":
        c = STATE["consult"].get(i)
        if not c:
            return _log("measure_eqe", {"index": i}, dict(error="forced consultation: call record_consultation for this index first, citing an FM receipt obtained since your previous merit measurement"))
    v = round(float(EP["merit"][i]), 8)
    STATE["merit"][i] = v
    if A.arm == "fm_forced":
        STATE["consult"].pop(i, None); STATE["fm_since_last"] = []; STATE["consult"] = {}
    return _log("measure_eqe", {"index": i}, dict(index=i, cation_fractions=_comp(i), merit=v, merit_name=MERIT_NAME,
                                                 budget_remaining=B_EQE - len(STATE["merit"])))


@mcp.tool(name="measure_xrd")
def measure_xrd(index: int) -> dict:
    """Spend one XRD measurement on candidate `index`. Returns the strongest background-subtracted peaks (Q in 1/Angstrom, relative intensity)."""
    i = _idx(index)
    if len(STATE["xrd"]) >= B_XRD and i not in STATE["xrd"]:
        return _log("measure_xrd", {"index": i}, dict(error="XRD budget exhausted"))
    if A.arm == "stub":
        pk = [(1.8, 100.0), (2.6, 40.0)]
    else:
        Q, I = P.plate_xrd(EP, EP["nearest_xrd"][i]); pk = classical.peaks(Q, I, n=20)
    STATE["xrd"][i] = pk
    return _log("measure_xrd", {"index": i}, dict(index=i, cation_fractions=_comp(i), peaks_Q_invA_relI=pk,
                                                 xrd_budget_remaining=B_XRD - len(STATE["xrd"])))


@mcp.tool(name="submit")
def submit(best_index: int, rationale: str, rejected: list[dict] | None = None) -> dict:
    """Finish the episode. best_index: the measured composition you judge best. rationale: why.
    rejected: optional list of {"index" or "hypothesis": ..., "reason": ...} for alternatives you ruled out."""
    STATE["submitted"] = dict(best_index=int(best_index), rationale=rationale[:4000], rejected=rejected or [])
    return _log("submit", {"best_index": int(best_index)}, dict(ok=True, merit_measured=len(STATE["merit"]), xrd_measured=len(STATE["xrd"])))


# ------------------------------------------------------------------ classical tools
if A.arm in ("classical", "fm_forced"):
    import fm

    def _subsystems():
        cats = EP["elements"]
        for r_ in range(1, len(cats) + 1):
            for sub in itertools.combinations(cats, r_):
                yield list(sub) + ["O"]

    def _phase_structure(pid):
        if pid in STATE["hypos"]:
            return Structure.from_dict(STATE["hypos"][pid])
        for sysl in _subsystems():
            for r in fm.chemsys_structures(sysl):
                if r["id"] == pid:
                    return fm.to_structure(r)
        raise ValueError(f"unknown phase id {pid}")

    @mcp.tool(name="list_phases")
    def list_phases() -> dict:
        """List known crystal structures (Materials Project) in every cation subset of this system plus O: id, formula, sites, cation fractions. No energies."""
        out = []
        for sysl in _subsystems():
            for r in fm.chemsys_structures(sysl):
                if r["nsites"] > fm.MAX_SITES: continue
                c = fm.to_structure(r).composition; tot = sum(c[e] for e in EP["elements"] if e in c)
                out.append(dict(id=r["id"], formula=r["formula"], nsites=r["nsites"],
                                cation_fractions={e: round((c[e] if e in c else 0) / tot, 3) for e in EP["elements"]}))
        return _log("list_phases", {}, dict(phases=out, n=len(out)))

    @mcp.tool(name="substitute_structure")
    def substitute_structure(phase_id: str, from_element: str, to_element: str) -> dict:
        """Build a hypothetical structure by replacing every `from_element` site of a listed phase (or an earlier hypothetical id) with `to_element`. Returns a new id usable by the other tools."""
        s = _phase_structure(phase_id).copy(); s.replace_species({from_element: to_element})
        hid = "hyp-" + fm.struct_hash(s)[:8]; STATE["hypos"][hid] = s.as_dict()
        return _log("substitute_structure", dict(phase_id=phase_id, from_element=from_element, to_element=to_element),
                    dict(id=hid, formula=s.composition.reduced_formula, nsites=len(s)))

    @mcp.tool(name="simulate_xrd")
    def simulate_xrd(phase_id: str) -> dict:
        """Simulated powder XRD peaks (Q in 1/Angstrom, relative intensity) for a phase id or hypothetical id."""
        return _log("simulate_xrd", dict(phase_id=phase_id), dict(id=phase_id, peaks_Q_invA_relI=classical.sim_peaks(_phase_structure(phase_id), phase_id)))

    @mcp.tool(name="match_xrd")
    def match_xrd(index: int, phase_ids: list[str]) -> dict:
        """Cosine similarity (0-1, best over a small rigid Q shift) between the measured XRD at `index` (measure it first) and simulated patterns of the given phases."""
        i = _idx(index)
        if i not in STATE["xrd"]:
            return _log("match_xrd", dict(index=i), dict(error="measure_xrd at this index first"))
        Q, I = P.plate_xrd(EP, EP["nearest_xrd"][i]); ym = classical.measured_on_grid(Q, I)
        res = {pid: classical.match(ym, classical.simulate(_phase_structure(pid), pid)) for pid in phase_ids[:40]}
        return _log("match_xrd", dict(index=i, phase_ids=phase_ids[:40]), dict(index=i, similarity=res))

    @mcp.tool(name="gp_suggest")
    def gp_suggest() -> dict:
        """Gaussian-process UCB suggestion for the next merit measurement from the merits measured so far (RBF kernel on composition)."""
        X = P.coords(EP); idx = list(STATE["merit"]); y = [STATE["merit"][i] for i in idx]
        mu, sd = P.gp_post(X[idx], y, X) if idx else (np.zeros(len(X)), np.ones(len(X)))
        s = mu + P.BETA * sd; s[idx] = -np.inf; top = np.argsort(-s)[:5]
        return _log("gp_suggest", {}, dict(next_index=int(top[0]), top5=[dict(index=int(t), mean=float(mu[t]), sd=float(sd[t])) for t in top]))

# ------------------------------------------------------------------ foundation-model tools + forced consultation
if A.arm == "fm_forced":
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
    from pymatgen.core import Composition

    @mcp.tool(name="mace_stability")
    def mace_stability(phase_id: str) -> dict:
        """MACE-MP-0 (universal ML interatomic potential): relax the structure; return formation energy and energy above the convex hull (eV/atom) against all known phases of this system."""
        s = _phase_structure(phase_id); m = fm.mace_relax(s)
        if "energy_per_atom_eV" not in m:
            return _log("mace_stability", dict(phase_id=phase_id), dict(error=m.get("error")))
        ef = fm.formation_energy(s, m["energy_per_atom_eV"])
        rows = P.fm_rows(EP["chem"])
        ents = [PDEntry(Composition(r["formula"]), r["ef_eV_atom"] * Composition(r["formula"]).num_atoms, name=pid) for pid, r in rows.items()]
        extra = sorted({str(e) for e in s.composition.elements} - set(EP["elements"]) - {"O"})
        ents += [PDEntry(Composition(e), 0.0, name="ref_" + e) for e in EP["elements"] + ["O"] + extra]
        me = PDEntry(s.composition, ef * s.composition.num_atoms, name="query"); pd_ = PhaseDiagram(ents + [me])
        r = dict(id=phase_id, formula=s.composition.reduced_formula, formation_energy_eV_atom=round(ef, 4),
                 e_above_hull_eV_atom=round(float(pd_.get_e_above_hull(me)), 4))
        if extra: r["caveat"] = f"elements {extra} are outside this system; e_above_hull is a lower bound"
        return _log("mace_stability", dict(phase_id=phase_id), r)

    @mcp.tool(name="megnet_bandgap")
    def megnet_bandgap(phase_id: str, fidelity: str = "hse") -> dict:
        """MEGNet multi-fidelity band-gap prediction (eV) for a phase or hypothetical id. fidelity: pbe | gllb | hse | scan."""
        f = {"pbe": 0, "gllb": 1, "hse": 2, "scan": 3}.get(fidelity, 2)
        g = fm.megnet_gap(_phase_structure(phase_id), f)
        return _log("megnet_bandgap", dict(phase_id=phase_id, fidelity=fidelity), dict(id=phase_id, gap_eV=round(g["gap_eV"], 3), fidelity=fidelity))

    @mcp.tool(name="record_consultation")
    def record_consultation(index: int, receipts: list[str], verdict: str) -> dict:
        """REQUIRED before each merit measurement in this arm. index: the candidate you intend to measure next. receipts: receipt ids of
        mace_stability / megnet_bandgap calls made since your previous merit measurement (at least one). verdict: your written judgement of
        what the foundation-model results imply for measuring this candidate (support, against, or uninformative, and why)."""
        i = _idx(index)
        valid = [r for r in receipts if r in STATE["fm_since_last"]]
        if not valid:
            return _log("record_consultation", dict(index=i, receipts=receipts), dict(error="no valid FM receipt since the previous merit measurement; call mace_stability or megnet_bandgap first and cite its receipt"))
        if len(verdict.strip()) < 20:
            return _log("record_consultation", dict(index=i, receipts=receipts), dict(error="verdict too short: write what the FM results imply for this candidate"))
        STATE["consult"] = {i: dict(receipts=valid, verdict=verdict[:2000])}
        STATE["consultations"].append(dict(index=i, receipts=valid, verdict=verdict[:2000]))
        return _log("record_consultation", dict(index=i, receipts=valid), dict(ok=True, index=i, cleared_to_measure=i))


if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run_stdio_async())
