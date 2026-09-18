# Rev 2.1 redo: restart checkpoint (2026-09-18)

**Rev 2.1 adds O1:** route every CLOSE, UNDEMONSTRATED or ESCALATE. An autonomous move is launched only inside a declared resource envelope and decision rights; reserved moves go on a card. Refusal 23 forbids ending a closure with "open for the user".

## Recheck of the restart point

- **D1 to the P7 provisional pass: unchanged by rev 2.1.** The rev2 evidence and rulings stand: I2 fm_prior CLOSE, fm_xrd LIFT; P7 CLOSE_UNRESOLVABLE.
- **What rev2 got wrong under rev 2.1:**
  - It ended on "open for the user" (refusal 23).
  - It never routed the I2 CLOSE of fm_prior.
  - It proposed the forced-consultation lift as its own next step. Rev 2.1 reserves that move after outcomes were seen (run 1), so it is carded.
- **Missing declarations (no evidence touched):** the D4 portfolio, and the D5 envelope plus decision rights.
- **Restart = O1 on the rev2 P7 closure**, after adding those declarations: `rev21/manifest_rev21.json` and `rev21/router/portfolio.json`.

## Envelope (declared; spend measured)

| Resource | Ceiling | Spent before rev 2.1 | Hard limit (×3) |
|---|---|---|---|
| GPU hours | 12 | 2.5 | 36 |
| Storage GB | 10 | 0.6 | 30 |
| Tokens (M) | 60 | 19.6 | 180 |
| Wall hours | 24 | 12 | 72 |

The per-episode measurement budget (B_EQE) is **reserved** to the user (cost of action). The user's "budget is not a problem" is read as the resource envelope, per CHANGELOG 2.1, "The two budgets".
