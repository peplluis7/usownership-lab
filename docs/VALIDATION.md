# Verification record - revision 0.2.0

Executed on 8 September 2026 with Python 3.13.5, NumPy 2.3.5 and pandas 2.2.3. The complete default pipeline regenerated the original 450 macro paths and 99 comparative paths, produced tables/figures/workbook, and compiled the main manuscript and supplement successfully. The final test suite reports **47 passed**. See `results/reproduction_v020.log`, `results/run_manifest.json`, `results/comparison_manifest.json` and `results/test_results.txt`.

## Numerical checks

- Maximum main-path monetary accounting residual: 6.1904e-16.
- Maximum main-path goods-accounting residual: 3.0065e-16.
- Maximum main-path equity residual: 2.4425e-15.
- Forty-eight matched-policy macro checks: maximum exported discrepancy 0.0.
- Maximum scaled difference from the saved v0.1.0 horizon outputs: 9.2107e-14 across common numerical columns. See `results/legacy_regression.json`.
- Four explicit spreadsheet formula identities and their cached values were checked. Comparative worksheet presence and CSV counts are tested.
- Failed or incomplete model paths remain labelled in the CSVs; no later outcomes are filled by interpolation.

These checks validate implementation identities and reproducibility, not the external truth of behavioural parameters or welfare-optimality.

## Artifact checks

The final manuscript is 23 pages and the supplement 14 pages. Both compile with resolved references and citations and no overfull horizontal boxes under the provided checker. The main bibliography cites 47 entries; the source ledger and `.bib` contain 51 records. All figures are generated from code. The long article is approximately 4,500 words and 11 PDF pages. All PDF pages were rendered and reviewed in contact sheets; high-risk tables, title, references and revised final pages were also inspected at readable resolution. This is not a claim of a line-by-line visual inspection of every page at 100% zoom. Programmatic geometry checks found no text blocks outside page boundaries in the reviewed renders.

Each of the three one-page Word submission documents was rendered and inspected. Unwanted inherited title borders were removed and the affected files re-rendered. All fifteen workbook sheets were rendered in sample ranges; the formula checks cover the formula cells beyond those ranges. The workbook is a data companion, not a newly estimated model.

## Execution notes

Several long single-call executions were interrupted by the tool runtime before completion. A process allowed to finish within the same work session completed the entire command successfully; interrupted attempts are not counted as additional scientific experiments. BLAS thread counts are set explicitly for predictable small-matrix performance and can be controlled through `SSM_NUM_THREADS`. Layout-only changes and workbook display ordering were subsequently rebuilt and checked; they do not alter the numerical experiment.

## Remaining human checks

Verify journal-specific instructions, author identity and declarations, source claims recorded as abstract-only, licence choice, public archive metadata, and the substantive research itself. No human approval, journal submission, open-source licence or public repository is asserted.

The standalone LaTeX source folder was also compiled from a clean copy without inherited auxiliary files. Both PDFs built successfully using only the supplied text, bibliography, figure and table dependencies.
