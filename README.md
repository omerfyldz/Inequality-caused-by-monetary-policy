# Inequality Caused by Monetary Policy

Python/Jupyter replication of Coibion, Gorodnichenko, Kueng, and Silvia (2017), **"Innocent Bystanders? Monetary Policy and Inequality"**, *Journal of Monetary Economics*, 88, 70-89.

This repository contains a transparent replication of the paper's main empirical results. The project focuses on the econometric analysis: monetary policy shock identification, Jordà local projections, impulse-response estimation, distributional mechanisms, and comparison with the published findings.

## Replication Paper

The written replication study is included here:

- [docs/replication_study.pdf](docs/replication_study.pdf)

The paper explains the research question, data structure, identification strategy, estimation method, replication design, results, limitations, and interpretation.

## Research Question

The original paper asks whether contractionary monetary policy shocks increase economic inequality in the United States.

The main outcomes are:

- labor earnings inequality
- total income inequality
- consumption inequality
- total expenditure inequality

Each outcome is studied using three inequality measures:

- cross-sectional standard deviation
- Gini coefficient
- 90th-10th percentile gap

## Method

The replication follows the paper's core time-series framework.

1. Monetary policy shocks are based on the Romer and Romer approach, which removes the predictable component of Federal Reserve rate decisions using the Fed's real-time forecasts.
2. Dynamic effects are estimated with Jordà local projections over horizons 0-20 quarters.
3. Main inequality responses are interpreted as cumulative impulse responses.
4. Inference uses Driscoll-Kraay robust covariance estimation to account for serial and cross-horizon dependence.
5. The central statistical comparison is whether the full response path is jointly different from zero.

The project is intentionally focused on the analysis layer rather than rebuilding all raw survey processing.

## Main Findings

The Python replication confirms the central conclusion of the paper:

> Contractionary monetary policy shocks persistently increase inequality in income, labor earnings, consumption, and total expenditures.

Current validation results:

- Figure 3 main inequality responses: `12/12` panels match the paper's 5% joint-test conclusion.
- Figure 6 percentile mechanism tests: `4/4` conclusions match the paper.
- Figure 8 net-worth group tests: `4/4` conclusions match the paper.
- Table 1-style descriptive correlations: maximum absolute difference from the paper is approximately `0.056`.

The mechanism results also support the paper's interpretation: consumption and expenditure inequality are driven especially by asymmetric responses at the upper end of the distribution, while net-worth group comparisons are consistent with a savings-redistribution channel.

## Repository Structure

```text
notebooks/
  00_project_overview.ipynb
  01_data_audit.ipynb
  02_descriptive_results.ipynb
  03_macro_irfs.ipynb
  04_main_inequality_irfs.ipynb
  05_variance_and_history.ipynb
  06_channels_and_inflation_target.ipynb

src/
  data.py
  local_projection.py
  plots.py
  metrics.py

docs/
  replication_study.pdf

outputs/
  figures/
  tables/
```

## Notebooks

The notebooks are organized in the same order as the replication workflow.

1. `00_project_overview.ipynb` maps the paper's objectives to the Python project.
2. `01_data_audit.ipynb` checks sample windows and key variables.
3. `02_descriptive_results.ipynb` reproduces descriptive inequality patterns and correlation evidence.
4. `03_macro_irfs.ipynb` checks whether the monetary shocks generate plausible aggregate responses.
5. `04_main_inequality_irfs.ipynb` reproduces the central inequality impulse responses.
6. `05_variance_and_history.ipynb` studies variance contributions and historical contribution exercises.
7. `06_channels_and_inflation_target.ipynb` reproduces mechanism and inflation-target exercises.

## Data Requirements

The project expects the authors' supplied replication data folder to be available locally. Data files are not committed to this repository.

Expected local layout:

```text
Inequality_CGKS_replication_folder/
  replication_folder/
  python_replication/
```

If your local folder differs, copy `config.example.yaml` to `config.yaml` and edit:

```yaml
original_replication_root: "../replication_folder"
```

`config.yaml` is ignored by Git so that local paths remain private.

## Setup

```powershell
cd path\to\python_replication
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Main dependencies:

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

## Reproducing Results

Run notebooks from a fresh kernel in numeric order:

```text
00 -> 01 -> 02 -> 03 -> 04 -> 05 -> 06
```

Generated tables and figures are written to:

```text
outputs/tables/
outputs/figures/
```

Generated outputs are not tracked because they can be recreated by running the notebooks.

## Validation and Limitations

The main replication conclusions match the published paper. Remaining differences are documented in:

- [DEVIATIONS.md](DEVIATIONS.md)

The most important limitations are:

- the project uses supplied final analysis workfiles rather than rebuilding all raw survey construction;
- some macro inputs are reconstructed from available source files;
- exact finite-sample inference can differ across software implementations;
- historical and variance contribution exercises should be interpreted qualitatively rather than as bit-for-bit numerical reproductions.

These limitations do not change the central conclusion that contractionary monetary policy shocks raise measured inequality over the five-year response horizon.

## Citation

Original paper:

Coibion, O., Gorodnichenko, Y., Kueng, L., and Silvia, J. (2017). "Innocent Bystanders? Monetary Policy and Inequality." *Journal of Monetary Economics*, 88, 70-89.

Replication author:

Ömer Faruk Yıldız, Department of Economics, Boğaziçi University.
