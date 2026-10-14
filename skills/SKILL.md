---
name: skills
description: >-
  Regenerate the main tables (Table 2, 3, 4) and figures (Figure 1, extension
  coefficient plot) of the Card & Krueger (1994) minimum-wage difference-in-
  differences replication from data/raw/public.csv. Use whenever the task is to
  produce, reproduce, update, or explain these DID results.
---

# DID replication — main tables and figures

This skill stores the reusable procedures that produce the main results of the
Card & Krueger (1994) minimum-wage DID replication. Each section is a recipe:
the variable definitions, the estimation, and the file it writes.

The end-to-end implementation lives in `code/run_all.py`, which runs every step
in order. Install the dependencies once:

```bash
python3 -m pip install numpy pandas scipy matplotlib statsmodels
```

Then run from the project root (the folder containing `code/`, `data/`, and
`outputs/`):

```bash
python3 code/run_all.py
```

`run_all.py` resolves the project root itself from
`Path(__file__).resolve().parents[1]`, so it needs no hardcoded paths and works
unchanged on any machine.

Input data: `data/raw/public.csv` (410 stores, 46 columns — see `DATA_DICTIONARY.md`).
All outputs land in `outputs/tables/`, `outputs/figures/`, and intermediate
analysis files in `data/processed/`.

---

## Skill 1 — FTE construction and closure handling

Full-time-equivalent employment is the core outcome variable. Reuse this exact
definition in every table and figure.

```
FTE1 = EMPFT + NMGRS + 0.5 * EMPPT      # Wave 1 (Feb 1992)
FTE2 = EMPFT2 + NMGRS2 + 0.5 * EMPPT2   # Wave 2 (Nov 1992)
```

Baseline closure adjustment on `STATUS2`:

| `STATUS2` | Meaning           | Wave-2 employment treatment |
|-----------|-------------------|-----------------------------|
| 0         | refused           | keep as reported            |
| 1         | answered          | keep as reported            |
| 2, 4, 5   | temporary closure | missing (`NaN`)             |
| 3         | permanent closure | zero (`0.0`)                |

This baseline rule holds throughout: permanently closed stores (`STATUS2 == 3`)
have Wave-2 employment set to 0; temporarily closed stores (`STATUS2` in 2, 4,
5) are treated as missing. Temporary closures are set to 0 only in Table 3 Row
5. The extension robustness check does not change closure coding — it instead
re-estimates on a sample that excludes permanently closed stores (see Skill 6).

Employment change: `DELTA_FTE = FTE2 - FTE1`. Table 4 re-derives the same
quantities under `_T4`-suffixed names (`FTE1_T4`, `FTE2_T4`, `DELTA_FTE_T4`);
see Skill 5.

---

## Skill 2 — Table 2: store and worker characteristics (p. 776)

Summary statistics by state (`STATE`: 1 = New Jersey, 0 = Pennsylvania),
reported as NJ mean, PA mean, with standard errors and a Welch (unequal-
variance) t-test for the difference.

Derived variables, in order:

- `FULLTIME_PCT* = 100 * EMPFT* / (EMPFT* + EMPPT*)` — full-time share among
  non-managerial employees (only where the denominator is positive).
- `MEAL* = PSODA* + PFRY* + PENTREE*` — price of a full meal, tax included
  (`min_count=3` so a store missing any component is missing).
- `WAGE425_*`, `WAGE505_*` — indicator × 100 for whether the starting wage
  equals $4.25 / $5.05, with missing wages coded to 0 so the denominator is
  all stores, not just valid-wage stores.
- `OWNED_PCT = CO_OWNED * 100`, `BONUS_PCT = BONUS * 100`,
  `SPECIAL2_PCT = SPECIAL2 * 100`.

Layout: Part 1 = store types (chain shares + company-owned), Part 2 = Wave 1
characteristics, Part 3 = Wave 2 characteristics.

> Replication caveat to carry forward: Wave 2 "special recruiting program"
> (`SPECIAL2`) is only a **proxy** for the Wave 1 cash recruiting bonus
> (`BONUS`); the two are not equivalent.

Writes: `outputs/tables/table2_replication.csv`,
`outputs/tables/table2_comparison.csv`,
`data/processed/table2_analysis.csv`.

---

## Skill 3 — Figure 1: distribution of starting wages (p. 777)

Two-panel histogram of the starting wage, one panel per survey wave, with
New Jersey (solid black) and Pennsylvania (white, hatched) side by side.

Binning recipe (match the original figure):

```python
centers = np.round(np.arange(4.25, 5.56, 0.10), 2)  # $4.25 ... $5.55
bins    = np.round(np.arange(4.20, 5.61, 0.10), 2)  # half-step boundaries
bar_width = 0.04
```

- Count = `np.histogram(wage, bins=bins)` per state per wave.
- Percentage denominator = all valid wage observations in that state and wave.
- NJ bars at `centers - bar_width/2`; PA bars at `centers + bar_width/2`.
- x-axis ticks at `centers`, rotated 45°; y-axis = "Percent of Stores".
- Wave 1 y-limits 0–35; Wave 2 y-limits 0–100.

Writes: `outputs/figures/figure1_replication.png`,
`outputs/figures/figure1_replication.pdf`,
`data/processed/figure1_analysis.csv`,
`data/processed/figure1_wage_distribution.csv`.

---

## Skill 4 — Table 3: employment before and after (p. 780)

Wage groups use the **Wave 1** NJ starting wage:

- `Low`      — `WAGE_ST == 4.25`
- `Midrange` — `4.25 < WAGE_ST < 5.00`
- `High`     — `WAGE_ST >= 5.00`

Closure handling mirrors Skill 1 (`FTE2_BASE`: permanent → 0, temporary →
`NaN`). Rows:

1. FTE before (`FTE1`)
2. FTE after (`FTE2_BASE`)
3. Change in group means (row 2 − row 1; SE from the two cross-sectional SEs,
   ignoring within-store covariance)
4. Balanced-sample change (`FTE2_BASE - FTE1` only where both waves are valid)
5. Temporary closures set to zero (`FTE2_ZERO_TEMP = FTE2_BASE` with temporary
   closures → 0, then `FTE2_ZERO_TEMP - FTE1`)

Columns: `PA`, `NJ`, `NJ_minus_PA`, `Low`, `Midrange`, `High`,
`Low_minus_High`, `Mid_minus_High` — each with mean, SE, and N. Group
differences use the two-sample difference-in-means SE.

Writes: `outputs/tables/table3_replication.csv`,
`outputs/tables/table3_comparison.csv`,
`outputs/tables/table3_sample_sizes.csv`,
`data/processed/table3_analysis.csv`.

---

## Skill 5 — Table 4: reduced-form employment-change models

Outcome: `DELTA_FTE_T4 = FTE2_T4 - FTE1_T4`, where
`FTE1_T4 = EMPFT + NMGRS + 0.5 * EMPPT` and
`FTE2_T4 = EMPFT2 + NMGRS2 + 0.5 * EMPPT2`. Closure handling follows Skill 1
(permanent closures → 0, temporary closures → `NaN`).

Main variables: `STATE` (NJ dummy, models i–ii) and `WAGE_GAP` (models iii–v).

Initial wage gap (the proportional raise needed to reach $5.05):

```
WAGE_GAP = 0                                    if STATE == 0 (PA)
         = max(0, (5.05 - WAGE_ST) / WAGE_ST)   if STATE == 1 (NJ), WAGE_ST > 0
```

Controls — chain/ownership (`KFC`, `ROY`, `WENDYS` dummies with Burger King as
the omitted reference; `OWNED = CO_OWNED`) and region (`SOUTHJ`, `CENTRALJ`,
`PA1`, `PA2`).

Five specifications (main variable, then controls):

| Model | Main variable | Controls                              |
|-------|---------------|---------------------------------------|
| i     | `STATE`       | —                                     |
| ii    | `STATE`       | chain + ownership                     |
| iii   | `WAGE_GAP`    | —                                     |
| iv    | `WAGE_GAP`    | chain + ownership                     |
| v     | `WAGE_GAP`    | chain + ownership + region            |

Sample construction (target N = 357):

- valid `DELTA_FTE_T4`, and `WAGE_ST` not missing and > 0; and
- either `WAGE_ST2` valid (> 0) **or** permanently closed (`STATUS2 == 3`);
- then drop rows missing any model control.

Estimate with OLS (`statsmodels`). For each model report the main coefficient,
its SE, the SER (`sqrt(mse_resid)`), an F-test p-value for the controls
(if any), N, and R². Format into the paper layout (coefficient + parenthesized
SE, controls yes/no rows, SER, control p-value, N).

Writes (among others): `outputs/tables/table4_replication.csv`,
`table4_formatted.csv`, `table4_original_formatted.csv`,
`table4_comparison.csv`, `table4_full_comparison.csv`,
`table4_sample_validation.csv`, `table4_regression_details.txt`,
`data/processed/table4_analysis.csv`.

---

## Skill 6 — Extension: chain-level heterogeneity and robustness

Load the Table 4 regression sample (`data/processed/table4_analysis.csv`).

1. Build interactions `NJ_KFC = STATE × KFC`, `NJ_ROY = STATE × ROY`, and
   `NJ_WENDYS = STATE × WENDYS`, with Burger King the reference chain.
2. Regress `DELTA_FTE_T4` on `STATE + KFC + ROY + WENDYS + NJ_KFC + NJ_ROY +
   NJ_WENDYS`, using OLS with heteroskedasticity-robust standard errors
   (`cov_type="HC1"`).
3. Joint Wald test that the three interaction coefficients are jointly zero
   (`NJ_KFC = NJ_ROY = NJ_WENDYS = 0`, `use_f=True`).
4. Chain-specific NJ−PA differences via linear combinations
   (`STATE = 0`, `STATE + NJ_KFC = 0`, `STATE + NJ_ROY = 0`,
   `STATE + NJ_WENDYS = 0`), each with robust SE, p-value, and 95% CI.
5. Plot the four differences as a coefficient chart with 95% CI error bars and
   a zero reference line (chains on the y-axis, inverted).
6. Robustness: re-estimate on the sample that **excludes** permanently closed
   stores (`STATUS2 != 3`) and compare coefficients.

Writes: `outputs/tables/extension_chain_effects.csv`,
`extension_chain_descriptive.csv`, `extension_chain_sample_sizes.csv`,
`extension_robustness.csv`, `extension_regression_details.txt`,
`extension_robustness_details.txt`, and
`outputs/figures/extension_chain_effects.png` / `.pdf`.

---

## Output map

| Result | Replication file | Processed data |
|--------|------------------|----------------|
| Table 2 | `table2_replication.csv`, `table2_comparison.csv` | `table2_analysis.csv` |
| Figure 1 | `figure1_replication.png/.pdf` | `figure1_analysis.csv`, `figure1_wage_distribution.csv` |
| Table 3 | `table3_replication.csv`, `table3_comparison.csv`, `table3_sample_sizes.csv` | `table3_analysis.csv` |
| Table 4 | `table4_*` (formatted, comparison, sample validation, regression details) | `table4_analysis.csv` |
| Extension | `extension_chain_effects.csv`, `extension_robustness.csv`, `extension_chain_effects.png/.pdf` | — |

## Gotchas to preserve across any rewrite

- `STATE == 1` is New Jersey (treatment), `STATE == 0` Pennsylvania (control).
- Closure coding drives every table: permanent (`3`) → 0, temporary
  (`2,4,5`) → missing. Temporary closures are set to 0 only in Table 3's row 5;
  the extension robustness check instead drops permanent closures.
- The wage-gap denominator is the Wave 1 wage; PA stores have gap 0 by
  construction.
- `SPECIAL2` (Wave 2) is a proxy for the cash bonus, not the same variable.
- Table 3 row 3 and group-difference SEs ignore within-store covariance — an
  approximation, not a paired test.
- Table 4's 357-observation sample is smaller than the 410-row raw file because
  of the valid-wage / closure screen; validate N, mean, and SD against the
  originals (357, −0.237, 8.825) and flag any mismatch.

## Final validation checklist

Before submitting, confirm each item:

- [ ] `python3 code/run_all.py` runs to completion with no errors or warnings.
- [ ] Raw data `data/raw/public.csv` contains 410 restaurants.
- [ ] Table 2, Table 3, Table 4, and Figure 1 are all generated (files in
      `outputs/tables/` and `outputs/figures/`).
- [ ] Table 4 and the Extension regression use 357 observations.
- [ ] The Extension robustness check uses 351 observations (357 minus the 6
      permanently closed stores).
- [ ] Every figure (`figure1_replication.*`, `extension_chain_effects.*`)
      opens correctly.
- [ ] Replicated results are compared against the original Card & Krueger
      (1994) tables and figure.

Caveats to state when reporting results:

- Table 2 uses alternative definitions for a few variables (notably the Wave 2
  "special recruiting program" is a proxy, and the full-time percentage
  excludes managers).
- Some Table 3 standard errors are approximate (the change-in-means and
  group-difference SEs ignore within-store covariance).
- Table 4 Model (v) shows a small difference from the original paper.
