# D1 branch census: frozen protocol (frozen 2026-09-17 22:40, before any count)

**Purpose.** This is the census the seed guideline recommends. It counts how many EXAFS and Rietveld papers publish a rejected structural model with a number attached (an R-factor, reduced chi², Rwp, GOF or similar). That count decides whether C3 is built from found negatives or constructed ones.

## Selection rule (frozen)

- **Source:** Europe PMC REST search, with `OPEN_ACCESS:y AND HAS_FT:y`, sorted by Europe PMC default relevance.
- **What is taken:** the first N research articles that return full text, per query. Reviews are skipped and logged as skipped with the reason.

| Set | Query | N |
|---|---|---|
| Z (Zn-Ti-O) | `(ZnTiO3 OR Zn2TiO4 OR "zinc titanate") AND Rietveld` | 8 |
| Z (Zn-Ti-O) | `EXAFS AND ZnO AND (Ti OR titanium) AND (fit OR fitting)` | 2 |
| E (cathode EXAFS) | `EXAFS AND fitting AND cathode AND lithium AND (coordination number)` | 10 |
| R (cathode Rietveld) | `Rietveld AND cathode AND lithium AND (refinement) AND (Rwp OR "goodness of fit" OR chi2)` | 10 |

- **Endpoints:** full text from `https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML`; supplementary files from `https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/supplementaryFiles`, a zip that may contain PDFs, and `pdftotext` is used where one is available.
- **Reading:** read every paper whole, including the SI where it can be reached. Never work from the abstract.

## Definitions (frozen)

- **chain_length:** the number of operations from sample or input to reported structural result (e.g. synthesize → measure → normalize → fit → report).
- **branch_alt_visible:** points where the text shows a choice among alternatives with a reason (model, shell count, space group, fixed vs floated parameter, phase set, amorphous vs crystalline call, stopping).
- **branch_rejected_named:** the subset where the rejected alternative is explicitly named.
- **rejected_with_number:** the subset where the rejected alternative carries a quantitative fit metric in the paper or SI. **This is the headline count.**
- **channels_claimed:** the measurement modalities the authors say they combined for the structural conclusion (XRD, XAS/EXAFS, XANES, Raman, TEM, NMR, DFT, and so on).
- **raw_data_deposited:** whether the raw spectrum or pattern is deposited (repository DOI, SI data file), or only figures.
- Every fact carries a locator: section title, table number or figure number.
