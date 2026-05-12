# Inequality Caused by Monetary Policy

Python/Jupyter replication of the main-paper results from:

> Coibion, Gorodnichenko, Kueng, and Silvia (2017), **"Innocent Bystanders? Monetary Policy and Inequality"**.

This project reproduces the paper's main empirical logic in Python while keeping the authors' original Stata/EViews replication folder untouched. The goal is not to rebuild all raw CEX preparation. The goal is to replicate the paper's analysis layer: the local projections, inequality responses, variance exercises, historical contribution exercises, and mechanism figures.

## Repository Scope

Replicated main-paper components:

- Figure 1 and Table 1-style descriptive inequality evidence
- Figure 2 macroeconomic local-projection sanity checks
- Figure 3 main inequality impulse responses
- Figures 4-5 variance decomposition and historical contribution
- Figures 6-8 mechanism, percentile, transition, and net-worth exercises
- Figure 9 inflation-target shock exercises

Out of scope:

- Appendix robustness tables and figures
- Full raw CEX microdata construction
- Re-running EViews/X-12 seasonal adjustment
- Re-estimating the inflation-target shock series from scratch

## Expected Folder Layout

This repo is designed to sit next to the original replication folder:

```text
Inequality_CGKS_replication_folder/
  replication_folder/      # original authors' files, read-only input
  python_replication/      # this repository
```

The Python code reads from the original folder through `src/data.py`. The original folder is not modified.

If your local path differs, copy `config.example.yaml` to `config.yaml` and edit:

```yaml
original_replication_root: C:/path/to/Inequality_CGKS_replication_folder/replication_folder
```

`config.yaml` is intentionally ignored by Git.

## Setup

```powershell
cd path\to\Inequality_CGKS_replication_folder\python_replication
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The main dependencies are:

- `pandas`
- `numpy`
- `matplotlib`
- `scipy`
- `statsmodels`
- `linearmodels`
- `pyreadstat`
- `openpyxl`
- `xlrd`
- `jupyter`

## Run Order

Run notebooks from a fresh kernel in numeric order:

1. `notebooks/00_project_overview.ipynb`
2. `notebooks/01_data_audit.ipynb`
3. `notebooks/02_descriptive_results.ipynb`
4. `notebooks/03_macro_irfs.ipynb`
5. `notebooks/04_main_inequality_irfs.ipynb`
6. `notebooks/05_variance_and_history.ipynb`
7. `notebooks/06_channels_and_inflation_target.ipynb`

Generated figures and tables are written to:

```text
outputs/figures/
outputs/tables/
```

Those generated outputs are ignored by Git because they can be recreated by running the notebooks.

## Code Structure

```text
src/
  data.py              # paths, Stata/Excel loading, macro reconstruction
  local_projection.py  # stacked local projections, tests, Figure 4-5 helpers
  plots.py             # consistent plotting helpers
  metrics.py           # validation/comparison table helpers

notebooks/
  00_project_overview.ipynb
  01_data_audit.ipynb
  02_descriptive_results.ipynb
  03_macro_irfs.ipynb
  04_main_inequality_irfs.ipynb
  05_variance_and_history.ipynb
  06_channels_and_inflation_target.ipynb
```

## Method Summary

The paper studies how contractionary monetary policy shocks affect inequality. The core empirical method is Jorda-style local projections estimated over horizons 0-20. The main Python implementation follows the original Stata workflow:

- use the authors' supplied final CEX workfiles as canonical analysis inputs;
- stack horizon-specific local-projection observations;
- estimate fixed-effects horizon systems;
- use Driscoll-Kraay standard errors through `linearmodels.PanelOLS`;
- compute cumulative impulse responses for the paper's inequality outcomes;
- reproduce the paper's joint tests where the Stata scripts test full response paths.

Where the original code uses Stata-specific commands, this project implements Python equivalents and documents any non-bit-identical behavior.

## Current Validation Status

The notebooks have been executed end-to-end from fresh kernels.

Current checks:

- Figure 3 main inequality IRFs: `12/12` panels match the paper's 5% joint-rejection conclusion.
- Figure 6 percentile equality tests: `4/4` panels match the paper's 5% equality-test conclusion.
- Figure 8 net-worth group gaps: `4/4` panels match the paper's 5% joint-rejection conclusion.
- Table 1 HP-filtered correlations: maximum absolute difference from the paper is about `0.056`.

See `DEVIATIONS.md` for the full validation and deviation log.

## Important Deviations

The main remaining deviations are documented rather than hidden:

- Stata `xtscc ..., fe` is translated with `linearmodels.PanelOLS(..., entity_effects=True).fit(cov_type="driscoll-kraay")`. Both are Driscoll-Kraay approaches, but finite-sample details are not bit-identical.
- The EViews/X-12 seasonal-adjustment stage is not rerun. The authors' final seasonally adjusted variables are used.
- `macro_data_all.dta` is not supplied, so Figure 2 macro inputs are reconstructed from the available source files.
- Figure 4 follows the original Stata formula, including the nonstandard denominator convention and the intercept plus horizon-dummy auxiliary OLS.
- Figure 5 is a Python emulation of Stata's residual-augmented `forecast solve` setup. It follows the same economic counterfactual idea, but does not call Stata directly.
- Appendix robustness work is intentionally excluded.

## Data Policy

This repository does not include the original authors' large Stata data files. To run the notebooks, place this repo next to the original `replication_folder` or configure the path in `config.yaml`.

## Bottom Line

This is a defensible Python/Jupyter replication of the main paper. The central inequality result is parallel with the published paper: contractionary monetary policy increases inequality, especially for consumption and expenditure measures. Remaining differences are mainly exact-software equivalence, reconstructed macro inputs, and historical/variance-decomposition details.
