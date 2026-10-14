# Replication of Card & Krueger (1994)

**Paper**: David Card and Alan B. Krueger (1994), "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania," *American Economic Review*, 84(4), 772–793.

**Objective**: reproduce the paper's main results — Table 2, Table 3, Table 4, and Figure 1 — from the store-level survey data, and add an independent chain-level heterogeneity extension with a robustness check.

## Background

In April 1992, New Jersey raised its minimum wage from $4.25 to $5.05, while neighboring Pennsylvania left it unchanged. Card and Krueger surveyed fast-food restaurants in both states in February 1992 (before) and November 1992 (after). The paper uses a difference-in-differences design — New Jersey as the treatment state and Pennsylvania as the control — to estimate the effect of the minimum-wage increase on employment.

## What this project reproduces

- **Table 2** (p. 776): store and worker characteristics by state, for both survey waves.
- **Figure 1** (p. 777): distribution of starting wages, by state and wave.
- **Table 3** (p. 780): employment before and after the increase, by state and initial-wage group.
- **Table 4**: reduced-form OLS models of the change in FTE employment.
- **Extension**: chain-level heterogeneity (Burger King, KFC, Roy Rogers, Wendy's) with a robustness check.

## Repository structure

```
.
├── code/run_all.py           # single script that runs every step in order
├── data/raw/public.csv       # raw store-level survey data (410 stores × 46 columns)
├── data/processed/           # per-table analysis datasets (written by the script)
├── outputs/tables/           # replicated tables (CSV) and regression details (TXT)
├── outputs/figures/          # Figure 1 and the extension figure (PNG / PDF)
├── skills/SKILL.md           # reusable recipes for each table and figure
├── DATA_DICTIONARY.md        # column definitions for public.csv
├── AI_USE_DISCLOSURE.md      # how AI was used, checked, and corrected
└── README.md                 # this file
```

## Requirements

- Python 3
- Packages: `numpy`, `pandas`, `scipy`, `matplotlib`, `statsmodels`

Install them once:

```bash
python3 -m pip install numpy pandas scipy matplotlib statsmodels
```

## Data

The raw store-level survey data is read from `data/raw/public.csv` (410
observations × 46 columns; see `DATA_DICTIONARY.md` for column definitions). The
script writes per-table analysis datasets to `data/processed/`.

## Running the replication

From the project root (the folder containing `code/`, `data/`, and `outputs/`):

```bash
python3 code/run_all.py
```

The script resolves the project root from its own location
(`Path(__file__).resolve().parents[1]`), so it needs no hardcoded paths and runs
unchanged on any machine.

## The replication process (what `run_all.py` does)

The script is organised into seven steps. Each step loads data, applies one
procedure, prints diagnostics, and writes its outputs.

1. **Load and inspect** — read `data/raw/public.csv`; report the shape (410 rows × 46 columns), restaurant counts by state, and missingness in the key employment variables.
2. **Data cleaning and FTE construction** — build full-time-equivalent employment
   `FTE = EMPFT + NMGRS + 0.5 * EMPPT` for both waves; set Wave-2 FTE to 0 for permanently closed stores (`STATUS2 == 3`) and to missing for temporarily closed stores (`STATUS2` in 2, 4, 5); compute `DELTA_FTE = FTE2 - FTE1`.
3. **Table 2** — compute NJ vs PA means, standard errors, and Welch t-tests for store types and Wave-1 / Wave-2 characteristics; write `table2_replication.csv` and `table2_comparison.csv`.
4. **Figure 1** — bin starting wages into 10-cent ranges from $4.20 to $5.60 and plot the NJ vs PA distribution for each wave; write `figure1_replication.png/.pdf` and the underlying distribution data.
5. **Table 3** — split NJ stores into low / midrange / high initial-wage groups; compute employment before/after and the change under alternative closure treatments; write `table3_replication.csv`, `table3_comparison.csv`, and `table3_sample_sizes.csv`.
6. **Table 4** — build the initial wage gap, select the 357-observation regression sample, and estimate five OLS models; write the paper-formatted table, the comparisons, and the regression details.
7. **Extension** — regress the change in FTE on state × chain interactions with HC1 robust standard errors, run a joint Wald test, plot chain-specific NJ−PA differences, and re-estimate excluding permanently closed restaurants.

## Expected outputs

`run_all.py` generates every file below. Table/CSV and TXT files are under
`outputs/tables/`, figures under `outputs/figures/`, and analysis datasets under
`data/processed/`.

| Step | Files written |
|------|---------------|
| Table 2 | `table2_replication.csv`, `table2_comparison.csv` |
| Figure 1 | `figure1_replication.png`, `figure1_replication.pdf` |
| Table 3 | `table3_replication.csv`, `table3_comparison.csv`, `table3_sample_sizes.csv` |
| Table 4 | `table4_replication.csv`, `table4_formatted.csv`, `table4_original_formatted.csv`, `table4_coefficient_comparison.csv`, `table4_comparison.csv`, `table4_full_comparison.csv`, `table4_sample_validation.csv`, `table4_sample_audit.csv`, `table4_regression_details.txt` |
| Extension | `extension_chain_sample_sizes.csv`, `extension_chain_descriptive.csv`, `extension_chain_effects.csv`, `extension_regression_details.txt`, `extension_robustness.csv`, `extension_robustness_details.txt`, `extension_chain_effects.png`, `extension_chain_effects.pdf` |
| Processed data | `table2_analysis.csv`, `table3_analysis.csv`, `table4_analysis.csv`, `figure1_analysis.csv`, `figure1_wage_distribution.csv` |

## How to verify this project is feasible

An AI agent or reviewer can confirm the replication by following these checks in
order.

1. **Data present** — `data/raw/public.csv` exists with 410 rows and 46 columns.
2. **Dependencies** — `python3 -c "import numpy, pandas, scipy, matplotlib, statsmodels"` exits without error.
3. **Runs end-to-end** — `python3 code/run_all.py` completes with exit code 0 (no traceback), and every file listed above exists afterward.
4. **Sample sizes** — Table 4 and the extension use 357 observations; the extension robustness check uses 351 (357 minus the 6 permanently closed stores).
5. **Table 4 coefficients** (rounded to two decimals):

   | Model | Main variable | Replication | Paper |
   |-------|---------------|-------------|-------|
   | (i)   | NJ dummy      | 2.33        | 2.33  |
   | (ii)  | NJ dummy      | 2.30        | 2.30  |
   | (iii) | Wage gap      | 15.65       | 15.65 |
   | (iv)  | Wage gap      | 14.92       | 14.92 |
   | (v)   | Wage gap      | 11.98       | 11.91 |

   The change in FTE has mean −0.238 and standard deviation 8.825 in the
   replication sample (the paper reports −0.237 and 8.825).

6. **Extension results** — the joint heterogeneity F-test has F = 2.490 and
   p = 0.060 in the baseline, and F = 2.409 and p = 0.067 (N = 351) after
   excluding permanently closed stores. At the 5% level, neither model rejects
   the joint null that the NJ−PA employment change is the same across chains; at
   the 10% level, both show marginally significant heterogeneity evidence. KFC's
   individual NJ−PA difference is significant at 5% without a multiple-comparison
   adjustment, but this does not establish that the brands differ overall.
7. **Figures open** — `figure1_replication.pdf/.png` and
   `extension_chain_effects.pdf/.png` render.

## Troubleshooting

- **File-path / `No such file or directory` errors** — run `python3 code/run_all.py` from the project root; the script resolves all paths relative to its own location, so an absolute path is not required.
- **`ModuleNotFoundError` (e.g. `statsmodels`)** — install the missing package with `python3 -m pip install numpy pandas scipy matplotlib statsmodels`.
- **`data/raw/public.csv` not found** — confirm the raw file is present at `data/raw/public.csv`; if it was moved, update the `DATA_PATH` and `DATA_PATH_T4` variables in `run_all.py`.
- **No output files after running** — the script stopped at an error. Re-run and read the last traceback; each step prints its own diagnostics and the files it writes.

## Known differences from the original paper (recorded, not adjusted)

- **Table 2**: the full-time-employee percentage uses an alternative definition (it excludes managers), and the Wave-2 "special recruiting program" is a proxy for the paper's cash recruiting bonus, not the same variable.
- **Table 3**: the change-in-means and group-difference standard errors are approximate — they ignore the within-store covariance across the two waves.
- **Table 4**: model (v)'s coefficient replicates at 11.98 rather than the paper's 11.91; the difference is recorded rather than adjusted. A matching sample size (357) also does not by itself prove the sample construction is identical to the paper's.

## AI use

How AI (ChatGPT and Claude) was used, how its outputs were checked, and where its suggestions were corrected or rejected is documented in `AI_USE_DISCLOSURE.md`.
