import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precompute_fm as P
for M in sys.argv[1:]:
    t = time.time(); s = P.system_summary(M)
    tern = [r for r in s["rows"] if r.get("ternary")]
    print(M, len(s["rows"]), "phases,", len(tern), "ternary,", f"{time.time()-t:.0f}s", flush=True)
    for r in sorted(tern, key=lambda r: r["ehull_eV_atom"])[:4]:
        print("   ", r["id"], r["formula"], "sb", r["sb_frac"], "ehull", r["ehull_eV_atom"], "gap(pbe,hse)", r.get("megnet_gap_pbe_eV"), r.get("megnet_gap_hse_eV"), flush=True)
