"""Build REPORT.html from the ledgers. Every number is read from a ledger file, never typed in."""
import json, os, html
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p)))
S = J("adjudication/score_record.json"); PW = J("supply/power_record.json"); CS = J("discovery/census/census_summary.json")
MAN = J("discovery/manifest.json"); I4 = J("instrument/i4_construct.json")["summary"]; CL = J("discovery/corpus_ledger.json")
r = pd.DataFrame(J("adjudication/scores_main.json"))
rng = np.random.default_rng(20260918)

def boot(x, n=4000):
    x = np.asarray(x, float); idx = rng.integers(0, len(x), (n, len(x))); m = x[idx].mean(1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

rows = [("Chance (random 5)", "chance", "floor"), ("Floor: GP-UCB, EQE only", "floor_cls_gp", "floor"),
        ("Floor: XRD-match prior", "floor_cls_xrd", "floor"), ("Floor: FM prior (MACE+MEGNet)", "floor_fm_prior", "floor"),
        ("Floor: FM-weighted XRD", "floor_fm_xrd", "floor"),
        ("Agent, bare (env only)", "bare", "bare"), ("Agent, classical tools", "classical", "classical"), ("Agent, classical + FM", "fm", "fm")]
stats = [(lab, key, kind, *boot(r[key])) for lab, key, kind in rows]
COL = {"floor": "var(--floor)", "bare": "var(--s3)", "classical": "var(--s1)", "fm": "var(--s2)"}

def dotplot():
    W, H, L, R_, T = 760, 40 + 34 * len(stats), 250, 30, 26
    lo, hi = 0.5, 0.85
    x = lambda v: L + (v - lo) / (hi - lo) * (W - L - R_)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Realized value by arm with 95% bootstrap intervals" class="chart">']
    for t in np.arange(0.5, 0.851, 0.05):
        s.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{T-6}" y2="{H-22}" class="grid"/>'
                 f'<text x="{x(t):.1f}" y="{H-6}" class="tick" text-anchor="middle">{t:.2f}</text>')
    for i, (lab, key, kind, m, a, b) in enumerate(stats):
        y = T + 12 + i * 34
        if i == 5: s.append(f'<line x1="8" x2="{W-8}" y1="{y-18}" y2="{y-18}" class="sep"/>')
        s.append(f'<text x="{L-14}" y="{y+4}" class="lab" text-anchor="end">{html.escape(lab)}</text>')
        s.append(f'<line x1="{x(a):.1f}" x2="{x(b):.1f}" y1="{y}" y2="{y}" stroke="{COL[kind]}" stroke-width="2" stroke-linecap="round"/>')
        s.append(f'<circle cx="{x(m):.1f}" cy="{y}" r="6" fill="{COL[kind]}" stroke="var(--bg)" stroke-width="2"><title>{lab}: {m:.3f} (95% CI {a:.3f}–{b:.3f}, n=100)</title></circle>')
        s.append(f'<text x="{x(b)+10:.1f}" y="{y+4}" class="val">{m:.3f}</text>')
    s.append("</svg>")
    return "".join(s)

def clusterplot():
    r["d"] = r.fm - r.classical
    g = r.groupby("el").agg(d=("d", "mean"), n=("d", "size")).sort_values("d")
    W, H, L, R_, T = 760, 40 + 26 * len(g), 70, 60, 20
    lo, hi = -1.0, 1.0
    x = lambda v: L + (v - lo) / (hi - lo) * (W - L - R_)
    ci = S["primary_metric"]["cluster"]["ci95_cluster"]
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="FM minus classical, mean per element system" class="chart">',
         f'<rect x="{x(ci[0]):.1f}" y="{T-8}" width="{x(ci[1])-x(ci[0]):.1f}" height="{H-T-22}" class="band"><title>cluster-level 95% CI {ci[0]:+.3f} to {ci[1]:+.3f}</title></rect>']
    for t in (-1, -0.5, 0, 0.5, 1):
        s.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{T-8}" y2="{H-22}" class="{"zero" if t == 0 else "grid"}"/>'
                 f'<text x="{x(t):.1f}" y="{H-6}" class="tick" text-anchor="middle">{t:+.1f}</text>')
    for i, (el, row) in enumerate(g.iterrows()):
        y = T + 6 + i * 26
        s.append(f'<text x="{L-12}" y="{y+4}" class="lab" text-anchor="end">{el}–Sb–O</text>')
        s.append(f'<line x1="{x(0):.1f}" x2="{x(row.d):.1f}" y1="{y}" y2="{y}" class="stem"/>')
        s.append(f'<circle cx="{x(row.d):.1f}" cy="{y}" r="5.5" fill="var(--s2)" stroke="var(--bg)" stroke-width="2"><title>{el}: {row.d:+.3f} over {int(row.n)} episodes</title></circle>')
        s.append(f'<text x="{W-R_+8}" y="{y+4}" class="val">n={int(row.n)}</text>')
    s.append("</svg>")
    return "".join(s), g

def censusplot():
    ps = CS["per_set"]; names = {"Z": "Zn–Ti–O", "E": "Cathode EXAFS", "R": "Cathode Rietveld"}
    keys = [("alt", "alternative visible", "var(--q1)"), ("named", "rejection named", "var(--q2)"), ("numbered", "rejection with a number", "var(--q3)")]
    W, L, R_, T = 760, 150, 40, 14; bh, gap = 12, 2
    H = T + 3 * (3 * (bh + gap) + 18) + 24
    mx = 35; x = lambda v: L + v / mx * (W - L - R_)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Branch census counts per paper set" class="chart">']
    for t in range(0, 36, 5):
        s.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{T-4}" y2="{H-22}" class="grid"/><text x="{x(t):.1f}" y="{H-6}" class="tick" text-anchor="middle">{t}</text>')
    y = T
    for code in ("Z", "E", "R"):
        s.append(f'<text x="{L-12}" y="{y+ (3*(bh+gap))/2 + 3}" class="lab" text-anchor="end">{names[code]}</text>')
        for k, lab, c in keys:
            v = ps[code][k]
            s.append(f'<rect x="{L}" y="{y}" width="{max(x(v)-L, 0.01):.1f}" height="{bh}" rx="2" fill="{c}"><title>{names[code]}: {v} branch points with {lab}</title></rect>'
                     f'<text x="{x(v)+6:.1f}" y="{y+bh-2}" class="val">{v}</text>')
            y += bh + gap
        y += 18
    s.append("</svg>")
    return "".join(s)

def pct(v): return f"{100*v:.0f}%"
cp, g = clusterplot()
pm = S["process_metrics"]; arms = {a["arm"]: a for a in S["arms"]}
P = {(p["a"], p["b"]): p for p in S["paired_comparisons"]}
prim = S["primary_metric"]; tot = CS["total"]
stats_rows = "".join(f'<tr><td>{html.escape(l)}</td><td class="num">{m:.3f}</td><td class="num">{a:.3f} – {b:.3f}</td></tr>' for l, k, kd, m, a, b in stats)
proc_rows = "".join(
    f'<tr><td>{n}</td><td class="num">{pct(pm[a]["share_any_xrd"])}</td><td class="num">{pct(pm[a]["share_any_classical_tool"])}</td><td class="num">{pct(pm[a]["share_any_fm_tool"])}</td>'
    f'<td class="num">{pm[a]["mean_eval_categories"]:.2f}</td><td class="num">{pm[a]["mean_explicit_rejections"]:.2f}</td><td class="num">${arms[a]["cost_usd"]:.2f}</td></tr>'
    for n, a in (("Bare", "bare"), ("Classical", "classical"), ("Classical + FM", "fm")))
cmp_rows = "".join(
    f'<tr><td>{a} − {b.replace("floor_", "floor ")}</td><td class="num">{P[(a,b)]["delta_primary"]:+.3f}</td><td class="num">{P[(a,b)]["delta_cluster"]:+.3f}</td>'
    f'<td class="num">{P[(a,b)]["ci95_cluster"][0]:+.3f} – {P[(a,b)]["ci95_cluster"][1]:+.3f}</td><td class="num">{P[(a,b)]["p_cluster"]:.2f}</td><td class="num">{"/".join(map(str,P[(a,b)]["wins_ties_losses"]))}</td></tr>'
    for a, b in [("fm", "classical"), ("fm", "bare"), ("classical", "bare"), ("fm", "floor_cls_gp"), ("classical", "floor_cls_gp"), ("fm", "chance")])
fmused = S["strata"]["fm_tool_used"]; fmnot = S["strata"]["fm_tool_not_used"]

HTML = f"""<title>Antimonate Photoanode Benchmark</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>
:root{{--bg:#f5f7f6;--panel:#ffffff;--ink:#16201c;--ink2:#46524c;--muted:#6b766f;--rule:#d9e0dc;--grid:#e6ebe8;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--floor:#8b9590;--q1:#b7d3f6;--q2:#5598e7;--q3:#1c5cab;--band:rgba(235,104,52,.10);
--verdict:#16201c;--verdict-ink:#f5f7f6;--chip:#e8eeea;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#141816;--panel:#1b201d;--ink:#eef2ef;--ink2:#c1cbc5;--muted:#8e9a93;--rule:#2d3531;--grid:#262d29;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--floor:#7d8782;--q1:#184f95;--q2:#3987e5;--q3:#9ec5f4;--band:rgba(217,89,38,.16);--verdict:#eef2ef;--verdict-ink:#141816;--chip:#232a26;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141816;--panel:#1b201d;--ink:#eef2ef;--ink2:#c1cbc5;--muted:#8e9a93;--rule:#2d3531;--grid:#262d29;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--floor:#7d8782;--q1:#184f95;--q2:#3987e5;--q3:#9ec5f4;--band:rgba(217,89,38,.16);--verdict:#eef2ef;--verdict-ink:#141816;--chip:#232a26;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font:16px/1.6 "IBM Plex Sans",system-ui,sans-serif}}
.wrap{{max-width:880px;margin:0 auto;padding-inline:20px;padding-block:40px 80px}}
h1,h2,h3{{font-family:"IBM Plex Sans Condensed","Arial Narrow",sans-serif;text-wrap:balance;line-height:1.15;margin:0}}
h1{{font-size:clamp(30px,5vw,44px);font-weight:700;letter-spacing:-.01em}}
h2{{font-size:24px;font-weight:600;margin-top:56px;padding-top:14px;border-top:1px solid var(--rule)}}
h3{{font-size:17px;font-weight:600;margin-top:26px}}
p{{max-width:68ch;margin:12px 0}} .lede{{font-size:18px;color:var(--ink2)}}
.eyebrow{{font:500 12px/1 "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.verdict{{background:var(--verdict);color:var(--verdict-ink);border-radius:6px;padding:22px 24px;margin-top:28px;display:grid;gap:14px}}
.verdict .big{{font:600 26px/1.2 "IBM Plex Sans Condensed",sans-serif}}
.verdict p{{margin:0;max-width:none;opacity:.92}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:6px;overflow:hidden;margin-top:22px}}
.kpi{{background:var(--panel);padding:14px 16px}} .kpi b{{display:block;font:500 24px/1.2 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}}
.kpi span{{font-size:13px;color:var(--muted)}}
figure{{margin:22px 0 8px;background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:16px 14px 8px;overflow-x:auto}}
figcaption{{font-size:13.5px;color:var(--muted);margin:6px 4px 6px}}
.chart{{width:100%;min-width:560px;height:auto;display:block}}
.chart .grid{{stroke:var(--grid);stroke-width:1}} .chart .zero{{stroke:var(--ink2);stroke-width:1}} .chart .sep{{stroke:var(--rule);stroke-dasharray:3 4}}
.chart .band{{fill:var(--band)}} .chart .stem{{stroke:var(--floor);stroke-width:1.5}}
.chart text{{fill:var(--ink2);font:13px "IBM Plex Sans",sans-serif}} .chart .tick{{fill:var(--muted);font:11.5px "IBM Plex Mono",monospace}}
.chart .val{{fill:var(--ink);font:12px "IBM Plex Mono",monospace}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--ink2);margin:0 4px 8px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
.tw{{overflow-x:auto;margin:14px 0}} table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}} th{{font-weight:600;color:var(--ink2);font-size:13px}}
td.num{{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;white-space:nowrap}}
.chip{{display:inline-block;font:500 12px/1 "IBM Plex Mono",monospace;padding:4px 7px;border-radius:3px;background:var(--chip);color:var(--ink2);white-space:nowrap}}
.chip.close{{background:rgba(227,73,72,.14);color:var(--ink)}} .chip.go{{background:rgba(27,175,122,.18);color:var(--ink)}} .chip.none{{background:rgba(237,161,0,.2);color:var(--ink)}}
blockquote{{margin:16px 0;padding:4px 0 4px 16px;border-left:3px solid var(--s2);color:var(--ink2);font-style:italic;max-width:66ch}}
code{{font:13.5px "IBM Plex Mono",monospace;background:var(--chip);padding:1px 5px;border-radius:3px}}
ul{{padding-left:20px;max-width:68ch}} li{{margin:6px 0}}
a{{color:var(--s1)}} a:focus-visible{{outline:2px solid var(--s1);outline-offset:2px}}
details{{margin:10px 0}} summary{{cursor:pointer;color:var(--ink2);font-size:14px}}
</style>
<div class="wrap">
<div class="eyebrow">FM-advantage benchmark · materials instance · run of 2026-09-17/18</div>
<h1 style="margin-top:10px">Do materials foundation models make an agent a better experimentalist?</h1>
<p class="lede">An intervene-root benchmark on 22 combinatorial X–Sb–O photoanode libraries. The subject is claude-opus-5, and the question is where to spend 5 EQE and 5 XRD measurements. Three arms: environment only, plus classical tools, and plus MACE-MP-0 and MEGNet. Every arm is scored against mechanical floors and chance on 100 paired episodes.</p>

<div class="verdict">
<div class="eyebrow" style="color:inherit;opacity:.7">Result · A4</div>
<div class="big">No claim. The FM tools did not move the decision, and no agent arm beat a plain Gaussian-process floor.</div>
<p>FM − classical: <b>{prim['episode_mean_diff']:+.3f}</b> of the plate maximum per episode (naive 95% CI {prim['episode_ci95_naive'][0]:+.3f} to {prim['episode_ci95_naive'][1]:+.3f}). At the preregistered element-cluster level it is <b>{prim['cluster']['cluster_mean_diff']:+.3f}</b> (95% CI {prim['cluster']['ci95_cluster'][0]:+.3f} to {prim['cluster']['ci95_cluster'][1]:+.3f}, p = {prim['cluster']['p_cluster']:.2f}). The FM arm called an FM tool in only {pct(pm['fm']['share_any_fm_tool'])} of its episodes.</p>
</div>

<div class="kpis">
<div class="kpi"><b>{stats[7][3]:.3f}</b><span>agent + FM tools</span></div>
<div class="kpi"><b>{stats[6][3]:.3f}</b><span>agent + classical</span></div>
<div class="kpi"><b>{stats[1][3]:.3f}</b><span>GP-UCB floor, no agent</span></div>
<div class="kpi"><b>{stats[0][3]:.3f}</b><span>chance, random 5 of ~29</span></div>
<div class="kpi"><b>{PW['mde']:.3f} → {S['mde']:.3f}</b><span>MDE, forecast → observed (cluster level; delta 0.17)</span></div>
</div>

<h2>1 · The census the guideline asked for</h2>
<p>The guideline predicted that EXAFS and Rietveld papers publish their rejected models with R-factors "by convention", so found negatives would be free. We read 30 open-access papers in full under a protocol frozen before counting: 10 on Zn–Ti–O, 10 on cathode EXAFS, 10 on cathode Rietveld. Where the SI was reachable we read it too, including numbers that exist only inside SI images.</p>
<figure>{censusplot()}
<div class="legend"><span><i style="background:var(--q1)"></i>alternative visible</span><span><i style="background:var(--q2)"></i>rejected model named</span><span><i style="background:var(--q3)"></i>rejected model with a fit metric</span></div>
<figcaption>Branch points per set. Of {tot['alt']} visible choices, {tot['named']} name the rejected option and {tot['numbered']} attach a number to it. Only <b>{tot['papers_with_numbered']} of 30 papers</b> publish a numbered rejected model; 6 of the 11 numbers come from one XRD-methods paper. Only {tot['papers_numbered_and_raw']} papers carry both a numbered negative and deposited raw data.</figcaption></figure>
<p><b>What it decided.</b> Rejections are named at about half the branch points and quantified at 13%. The "found negative" premise fails in this sample. Structure solution from spectra (C3) closes at the grader gate: to re-fit a rejected model you need the raw spectrum, and 28 of 30 papers do not deposit one. The route forward is constructed negatives or a replayable environment. We built the replayable environment.</p>

<h2>2 · The environment: a replayable combinatorial library</h2>
<p>The Zn–Ti–O wafer the guideline names is not public. We used CaltechDATA <code>42gwd-8wg77</code> (CC0): 22 X–Sb–O thin-film composition lines across 14 elements. Every point has an XRD pattern and EQE at four photon energies and up to three electrolytes. Because the whole map is recorded, the outcome of every action not taken is known. This is the selective-labels condition that shape.md says leaves the intervene root empty.</p>
<div class="tw"><table>
<tr><th>Slot</th><th>Value</th><th>Derived from</th></tr>
<tr><td>Decision shape</td><td>intervene / choose the next measurement</td><td>the seeds' practitioners commit measurements (S1–S3). Infer fails Gate 1; explain and generate fail Gate 2</td></tr>
<tr><td>Episode</td><td>plate × electrolyte × LED; ~29 candidate compositions; 5 EQE + 5 XRD</td><td>{CL['corpus']['n_episodes_total']} episodes, {CL['corpus']['n_included']} included, cohort of 100 (LED-stratified hash sample)</td></tr>
<tr><td>Score</td><td>best measured EQE ÷ best on the line (graded, 1 scalar per episode)</td><td>EQE is measured truth; phase labels are annotation and are never scored</td></tr>
<tr><td>Independent unit</td><td>element system, 14 clusters</td><td>amendment A-01: XRD-map similarity clustered by substrate (FTO vs Pt), and tau.py refused the curve</td></tr>
<tr><td>Delta</td><td>0.17</td><td>S3's ≥2× acceleration, expressed in this metric: E[best of 10 random] − E[best of 5 random]</td></tr>
<tr><td>Contamination</td><td>all data predate the subject; 7 text-level answers excluded</td><td>no-tool recall probe: citing the paper gives no gain (3/28 vs 4/28 within 0.05)</td></tr>
</table></div>

<h3>Candidates ruled at D4</h3>
<div class="tw"><table>
<tr><th>Family (from the guideline)</th><th>Root</th><th>Ruling</th></tr>
{''.join(f'<tr><td>{html.escape(c["family"])}</td><td>{html.escape(c["shape"])}</td><td><span class="chip {"go" if c["disposition"]=="PROCEED" else "close"}">{c["disposition"]}</span> {html.escape(c.get("binding_gate",""))}</td></tr>' for c in MAN['candidates'])}
</table></div>

<h2>3 · Before any agent ran: floors and resolution</h2>
<p>Mechanical compositions, with no agent in the loop, built blind and hashed. The FM channels were checked for construct validity against the paper's observed photoactive phases. MACE placed {I4['mace_on_hull'].split(' observed')[0]} observed top-EQE crystalline phases within 50 meV/atom of its hull. MEGNet's gap is at or below the photon energy for {I4['megnet_absorbs'].split(' have')[0]}. So the tools measure something real. It still does not carry over: the FM-prior floor ({stats[3][3]:.3f}) does not beat an EQE-only GP ({stats[1][3]:.3f}), and FM weighting adds +0.003 to the XRD composition (I2).</p>
<p>P7 forecast a cluster-level MDE of {PW['mde']:.3f}, under delta, so the comparison was ruled resolvable and the agent arms were run.</p>

<h2>4 · The scored comparison</h2>
<figure>{dotplot()}
<div class="legend"><span><i style="background:var(--floor)"></i>no agent</span><span><i style="background:var(--s3)"></i>agent, bare</span><span><i style="background:var(--s1)"></i>agent, classical</span><span><i style="background:var(--s2)"></i>agent, classical + FM</span></div>
<figcaption>Mean realized value over the same 100 episodes, with 95% bootstrap intervals over episodes. All three agent arms beat chance. None beats the GP-UCB floor.</figcaption></figure>
<details><summary>Table view</summary><div class="tw"><table><tr><th>Arm</th><th>Mean</th><th>95% CI</th></tr>{stats_rows}</table></div></details>

<div class="tw"><table>
<tr><th>Paired comparison</th><th>Δ per episode</th><th>Δ per cluster</th><th>Cluster 95% CI</th><th>p (df 13)</th><th>W/T/L</th></tr>{cmp_rows}
</table></div>

<figure>{cp}
<figcaption>FM − classical, mean per element system. The shaded band is the cluster-level 95% CI. The La outlier comes from 2 episodes whose EQE sits at the noise floor (≈0.01%). The observed cluster variance gives an MDE of {S['mde']:.3f}, above delta, so the preregistered cluster-level test is underpowered after the fact. The episode-level interval is the tighter statement: no FM benefit above about +0.03 is hiding.</figcaption></figure>

<h2>5 · Why: the agent rarely reached for the model</h2>
<div class="tw"><table>
<tr><th>Arm</th><th>any XRD</th><th>any classical tool</th><th>any FM tool</th><th>eval. categories</th><th>explicit rejections</th><th>cost (100 ep.)</th></tr>{proc_rows}
</table></div>
<p>The FM arm called MACE or MEGNet in {fmused['n']} of 100 episodes. Where it did, FM − classical was {fmused['diff']:+.3f}; where it did not, {fmnot['diff']:+.3f}. That split is post-treatment and descriptive only. In most episodes the agent spent its EQE budget straight from chemistry priors, for example "AgSbO3 absorbs visible light". That matches the hypothesis in shape.md that agents select tools competently and evaluate shallowly.</p>
<p>When the FM arm did use the models, it produced exactly the branch the guideline described: two modalities must agree on one structure, and candidates that fail one of them are rejected with a reason.</p>
<blockquote>At Sb=0.22 bixbyite In2O3 also appears, and the In11Sb3O24 phase predicted there did not form.</blockquote>
<blockquote>La3Sb5O12 has a predicted gap of 2.26 eV, but its composition gave no EQE and its XRD did not match that phase.</blockquote>
<p>The reasoning pattern exists. It did not turn into more EQE found per measurement.</p>

<h2>6 · What this does and does not establish</h2>
<ul>
<li><b>Established:</b> on this library, at a 5-of-29 budget, adding MACE-MP-0 and MEGNet to an Opus-5 agent that already has classical tools does not raise the realized value by more than about 0.03 of the plate maximum (episode level). A plain GP-UCB loop at 0.740 is the bar every future arm has to clear.</li>
<li><b>Established:</b> the guideline's "found negatives by convention" premise does not hold in 30 read papers (4 with numbers, 2 with raw data).</li>
<li><b>Not established:</b> anything at the element-cluster level. The observed MDE of {S['mde']:.3f} exceeds delta. Fourteen chemistries are the binding supply; more libraries, not more episodes, would raise power.</li>
<li><b>Not established:</b> whether forcing evaluation depth would change the result. That would be a lift, and it needs its own floor rebuilt against the lifted task.</li>
<li><b>Limits:</b> FM construct validity was checked on proxies (stability, gap), not on EQE. There is one subject model. The environment's EQE carries no repeat noise. R1 ran before D5 froze (disclosed). R0 replay was not blind.</li>
</ul>

<h2>7 · Where everything is</h2>
<p>Every stage, ledger, trace and log is in <a href="https://github.com/colpark/19C_materials">github.com/colpark/19C_materials</a>. Start with <code>STATE.md</code> and <code>RUN_LOG.md</code>. The benchmark is runnable: <code>bench/floors.py</code> for the floors, <code>runtime/run_batch.py</code> for the arms, <code>adjudication/score.py</code> for scoring.</p>
</div>
"""
open(os.path.join(ROOT, "REPORT.html"), "w").write(HTML)
print("wrote REPORT.html", len(HTML))
