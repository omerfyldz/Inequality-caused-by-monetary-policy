# Deviations and Validation Notes

This document records the remaining differences between this Python/Jupyter replication and the original Stata/EViews main-paper replication.

## Resolved Since Initial Implementation

### Figure 6 percentile system

The initial notebook estimated P90-P50 and P10-P50 spreads separately. This has been replaced with the original stacked system from Stata `step406`, including the joint equality test of P90-P50 versus P10-P50 over horizons 0-20.

Current comparison:

| Figure 6 panel | Paper p-value | Python p-value | Same 5% conclusion |
|---|---:|---:|---|
| Income | 0.000 | 0.000 | Yes |
| Earnings | 0.209 | 0.428 | Yes |
| Expenditure | 0.000 | 0.000 | Yes |
| Consumption | 0.000 | 0.000 | Yes |

### Figure 5 historical smoothing

The output table now contains both corrected moving averages and Stata-compatible moving averages. The plotted Figure 5 uses the Stata-compatible version, which divides a centered five-quarter sum by 3 as in the original code.

### Figure 2 macro display convention

The macro notebook now follows `step402` more literally:

- real variables and unemployment use the one-quarter-lagged RR shock;
- real variables and `dUE` use the shifted cumulative display with zero at horizon 0;
- the published unemployment panel is `dUE`, not unemployment in levels;
- the fed funds rate uses the contemporaneous shock and a non-cumulative response;
- `DGS10` and auxiliary macro series are estimated for audit but omitted from the 12-panel combined figure, matching the published combined graph.

### Figure 4 auxiliary OLS specification

The variance-decomposition helper now includes an intercept plus horizon dummies, matching Stata's `reg ... i.hor` structure in `step404`.

### Figure 5 forecast-solve emulation

The historical-contribution helper now mirrors the two-regression structure in `step405`: estimate the AR-shock equation, save the residual, re-estimate with that residual included, then dynamically solve the model with shocks present and with shocks set to zero.

### Figure 9 structure

The inflation-target notebook now produces IRF, variance-decomposition, and historical-contribution outputs, matching the main structure of paper Figure 9.

## Remaining Important Deviations

### 1. Raw CEX construction is not rebuilt

The Python repo starts from the authors' supplied final analysis workfiles:

- `workfiles/all_CEX_data_short.dta`
- `workfiles/all_CEX_data_cohort.dta` for checks if needed

This is intentional. The project scope excludes deep data preparation and appendix replication.

Impact: low for main-paper econometric replication; high only if the required deliverable becomes a full raw-data rebuild.

### 2. EViews/X-12 seasonal adjustment is not rerun

The original pipeline exports inequality series to EViews for X-12 seasonal adjustment and then imports the adjusted series back to Stata. This repo uses the final `_SA` variables from the supplied workfiles.

Impact: low for reproducing the paper's analysis layer because the analysis uses those final seasonally adjusted variables.

### 3. Driscoll-Kraay covariance is not bit-identical to Stata `xtscc`

Original:

```stata
xtscc y x, fe
```

Python:

```python
PanelOLS(..., entity_effects=True).fit(cov_type="driscoll-kraay")
```

Both are Driscoll-Kraay panel covariance estimators, but finite-sample corrections, bandwidth defaults, and degrees-of-freedom treatment can differ. This mostly affects standard errors and p-values, not the point-estimate IRF paths.

Impact: moderate. The core conclusions match, but p-values are not expected to be bit-for-bit identical.

### 4. Macro data are reconstructed because `macro_data_all.dta` is not supplied

The original Stata `step402` uses `macro_data_all`, created by `step090`. The final `macro_data_all.dta` is not present in the provided `workfiles`, so the Python repo reconstructs it from:

- `source_files/JMEinequality.xls`
- `source_files/monthly.dta`
- `source_files/daily.dta`

Impact: moderate for Figure 2 and Table 1. This is the main remaining source of macro-side differences.

### 5. Figure 2 macro IRFs remain directionally but not numerically exact

The Python Figure 2 matches the broad sanity-check pattern:

- Fed funds rate rises after a contractionary shock.
- GDP and consumption fall at medium horizons.
- Unemployment rises at medium horizons.
- House prices and business income fall.
- Financial income rises.

Remaining differences:

- exact macro inputs are reconstructed because the final `macro_data_all.dta` is not supplied;
- `linearmodels` Driscoll-Kraay inference is not bit-identical to Stata `xtscc`;
- GDP and consumption still rebound above zero at long horizons in Python;
- wages/salaries remain more significant in Python than emphasized in the paper;
- the house-price decline remains somewhat larger than the paper's text description.

Impact: moderate. Figure 2 is a validation/sanity-check figure, not the central inequality result.

### 6. Figure 4 variance-decomposition magnitudes are not exact

The Python code follows the original Stata formula, including the nonstandard denominator convention and the intercept plus horizon-dummy OLS structure. Still, some magnitudes differ:

- Earnings contribution remains small, matching the paper.
- Expenditure contribution is broadly similar and is the largest series in several panels.
- Income and consumption contributions are somewhat lower than the paper's narrative range.
- Current maximum contributions after rerunning are approximately: income 0.078, earnings 0.020, expenditure 0.286, consumption 0.130 across the plotted inequality measures.

Impact: moderate. The qualitative ranking is mostly preserved, but exact magnitudes should be treated cautiously.

### 7. Figure 5 historical contribution is a Python emulation of Stata `forecast solve`

The Python implementation now follows the same residual-augmented dynamic model used before Stata `forecast solve`. It still does not call Stata's actual `forecast create` / `forecast solve` machinery.

Relevant Stata documentation: [`forecast solve`](https://www.stata.com/manuals/tsforecastsolve.pdf) computes static or dynamic forecasts from the model currently in memory after `forecast create` and `forecast estimates`. The Python code implements the same dynamic shock-removal idea directly.

Impact: moderate. The interpretation is parallel, but exact historical paths can differ.

### 8. Inflation-target shocks are used, not re-estimated

The repo uses the supplied `sh_pi` variable and applies the original sign convention. It does not re-estimate the Coibion-Gorodnichenko time-varying inflation-target model.

Impact: low for paper-analysis replication; high only for a raw shock-construction replication.

### 9. Plot style is Matplotlib, not Stata `.gph`

The figures preserve layout, recession shading, confidence bands, and labels where relevant. Exact Stata fonts, graph spacing, and `.gph` rendering are not replicated.

Impact: low.

## Current Validation Summary

The latest validation file is:

`outputs/tables/validation_summary.csv`

Current checks:

- Figure 3: `12/12` panels match the paper's 5% conclusion.
- Figure 6: `4/4` panels match the paper's 5% equality-test conclusion.
- Figure 8: `4/4` panels match the paper's 5% conclusion.
- Table 1: maximum absolute correlation difference is about `0.056`.

Affected notebooks rerun after the latest fixes:

- `notebooks/03_macro_irfs.ipynb`
- `notebooks/05_variance_and_history.ipynb`
- `notebooks/06_channels_and_inflation_target.ipynb`

## Bottom Line

The repo is now a defensible main-paper Python replication. The central inequality result is parallel with the paper. The remaining issues are mainly exact-software equivalence, macro-data reconstruction, and historical/variance-decomposition details, not the core causal conclusion.
