from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class LPResult:
    dep_var: str
    shock_var: str
    horizons: np.ndarray
    irf: np.ndarray
    se: np.ndarray
    pvalue: float
    fstat: float
    nobs: int
    covariance: str
    coefficients: pd.Series
    covariance_matrix: pd.DataFrame
    stacked: pd.DataFrame
    model_result: object

    @property
    def lower_1se(self) -> np.ndarray:
        return self.irf - self.se

    @property
    def upper_1se(self) -> np.ndarray:
        return self.irf + self.se

    @property
    def lower_165se(self) -> np.ndarray:
        return self.irf - 1.65 * self.se

    @property
    def upper_165se(self) -> np.ndarray:
        return self.irf + 1.65 * self.se


@dataclass
class PercentileSystemResult:
    base: str
    shock_var: str
    horizons: np.ndarray
    p10_irf: np.ndarray
    p10_se: np.ndarray
    p90_irf: np.ndarray
    p90_se: np.ndarray
    equality_pvalue: float
    equality_fstat: float
    nobs: int
    covariance: str
    coefficients: pd.Series
    covariance_matrix: pd.DataFrame
    model_result: object


def _lag(s: pd.Series, n: int) -> pd.Series:
    return s.shift(n)


def _lead(s: pd.Series, n: int) -> pd.Series:
    return s.shift(-n)


def make_stacked_lp_data(
    df: pd.DataFrame,
    dep_var: str,
    shock_var: str = "sh_rr",
    horizons: int = 20,
    ar_lags: int = 2,
    shock_lags: int = 20,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    base = df.sort_values(["year", "quarter"]).copy().reset_index(drop=True)
    for lag in range(shock_lags + 1):
        base[f"{shock_var}_L{lag}"] = _lag(base[shock_var], lag)
    for lag in range(1, ar_lags + 1):
        base[f"{dep_var}_L{lag}"] = _lag(base[dep_var], lag)
    for h in range(horizons + 1):
        base[f"{dep_var}_F{h}"] = _lead(base[dep_var], h)

    rows = []
    for h in range(horizons + 1):
        cols = ["year", "quarter", "t", "time", f"{dep_var}_F{h}"]
        cols += [f"{shock_var}_L{i}" for i in range(shock_lags + 1)]
        cols += [f"{dep_var}_L{i}" for i in range(1, ar_lags + 1)]
        tmp = base[cols].copy()
        tmp = tmp.rename(columns={f"{dep_var}_F{h}": "Y"})
        tmp["hor"] = h
        rows.append(tmp)
    stacked = pd.concat(rows, ignore_index=True)

    exog_cols: list[str] = []
    shock0_cols: list[str] = []
    interaction_data: dict[str, pd.Series] = {}
    for h in range(horizons + 1):
        mask = (stacked["hor"] == h).astype(float)
        for lag in range(shock_lags + 1):
            col = f"shock_L{lag}_H{h}"
            interaction_data[col] = stacked[f"{shock_var}_L{lag}"] * mask
            exog_cols.append(col)
            if lag == 0:
                shock0_cols.append(col)
        for lag in range(1, ar_lags + 1):
            col = f"dep_L{lag}_H{h}"
            interaction_data[col] = stacked[f"{dep_var}_L{lag}"] * mask
            exog_cols.append(col)

    stacked = pd.concat([stacked, pd.DataFrame(interaction_data, index=stacked.index)], axis=1)
    stacked = stacked.dropna(subset=["Y"] + exog_cols).copy()
    stacked["entity"] = stacked["hor"].astype(int)
    stacked["time_id"] = stacked["t"].astype(int)
    return stacked, exog_cols, shock0_cols


def run_stacked_lp(
    df: pd.DataFrame,
    dep_var: str,
    shock_var: str = "sh_rr",
    horizons: int = 20,
    ar_lags: int = 2,
    shock_lags: int = 20,
    cumulative: bool = True,
    cov_type: str = "driscoll-kraay",
) -> LPResult:
    stacked, exog_cols, shock0_cols = make_stacked_lp_data(
        df, dep_var, shock_var, horizons, ar_lags, shock_lags
    )
    y = stacked["Y"].astype(float)
    x = stacked[exog_cols].astype(float)

    covariance_label = cov_type
    try:
        from linearmodels.panel import PanelOLS

        panel = stacked.set_index(["entity", "time_id"])
        mod = PanelOLS(panel["Y"], panel[exog_cols], entity_effects=True)
        res = mod.fit(cov_type=cov_type)
        params = res.params
        cov = res.cov
        nobs = int(res.nobs)
    except Exception:
        import statsmodels.api as sm

        covariance_label = "statsmodels HAC fallback"
        dummies = pd.get_dummies(stacked["hor"].astype(int), prefix="hor", drop_first=True)
        x_sm = pd.concat([x, dummies.astype(float)], axis=1)
        res = sm.OLS(y, x_sm).fit(cov_type="HAC", cov_kwds={"maxlags": horizons})
        params = res.params
        cov = res.cov_params()
        nobs = int(res.nobs)

    coefs = np.array([params.get(c, np.nan) for c in shock0_cols])
    cov_sub = cov.loc[shock0_cols, shock0_cols].to_numpy()
    hgrid = np.arange(horizons + 1)

    if cumulative:
        transform = np.tril(np.ones((horizons + 1, horizons + 1)))
        irf = transform @ coefs
        vcov_irf = transform @ cov_sub @ transform.T
    else:
        irf = coefs
        vcov_irf = cov_sub
    se = np.sqrt(np.maximum(np.diag(vcov_irf), 0))

    # Joint test on cumulative path, matching the Stata lincom/test construction.
    if cumulative:
        rmat = np.tril(np.ones((horizons + 1, horizons + 1)))
    else:
        rmat = np.eye(horizons + 1)
    q = rmat @ coefs
    v = rmat @ cov_sub @ rmat.T
    rank = np.linalg.matrix_rank(v)
    if rank:
        wald = float(q.T @ np.linalg.pinv(v) @ q)
        fstat = wald / rank
        df_resid = getattr(res, "df_resid", None)
        if df_resid is not None and np.isfinite(float(df_resid)):
            pvalue = float(1 - stats.f.cdf(fstat, rank, float(df_resid)))
        else:
            pvalue = float(1 - stats.chi2.cdf(wald, rank))
    else:
        fstat = np.nan
        pvalue = np.nan

    return LPResult(
        dep_var=dep_var,
        shock_var=shock_var,
        horizons=hgrid,
        irf=irf,
        se=se,
        pvalue=pvalue,
        fstat=fstat,
        nobs=nobs,
        covariance=covariance_label,
        coefficients=params,
        covariance_matrix=cov,
        stacked=stacked,
        model_result=res,
    )


def run_percentile_spread_system(
    df: pd.DataFrame,
    base: str,
    shock_var: str = "sh_rr",
    horizons: int = 20,
    ar_lags: int = 2,
    shock_lags: int = 20,
    cov_type: str = "driscoll-kraay",
) -> PercentileSystemResult:
    """Replicate Stata step406's joint P10/P90 percentile-spread system.

    For a base such as ``LNCONS_SA``, the system jointly estimates responses of
    ``D_P10_base - D_P50_base`` and ``D_P90_base - D_P50_base`` and tests whether
    the two cumulative response paths are equal across all horizons.
    """
    base_df = df.sort_values(["year", "quarter"]).copy().reset_index(drop=True)
    for lag in range(shock_lags + 1):
        base_df[f"{shock_var}_L{lag}"] = base_df[shock_var].shift(lag)
    for pp in (10, 90):
        spread = base_df[f"D_P{pp}_{base}"] - base_df[f"D_P50_{base}"]
        for lag in range(1, ar_lags + 1):
            base_df[f"spread{pp}_L{lag}"] = spread.shift(lag)
        for h in range(horizons + 1):
            base_df[f"spread{pp}_F{h}"] = spread.shift(-h)

    rows = []
    for h in range(horizons + 1):
        for pp in (10, 90):
            cols = ["year", "quarter", "t", "time"]
            cols += [f"{shock_var}_L{i}" for i in range(shock_lags + 1)]
            cols += [f"spread10_L{i}" for i in range(1, ar_lags + 1)]
            cols += [f"spread90_L{i}" for i in range(1, ar_lags + 1)]
            tmp = base_df[cols].copy()
            tmp["Y"] = base_df[f"spread{pp}_F{h}"]
            tmp["hor"] = h
            tmp["pp"] = pp
            rows.append(tmp)
    stacked = pd.concat(rows, ignore_index=True)

    exog_cols: list[str] = []
    p10_shock0: list[str] = []
    p90_shock0: list[str] = []
    interaction_data: dict[str, pd.Series] = {}
    for h in range(horizons + 1):
        hmask = (stacked["hor"] == h).astype(float)
        for pp in (10, 90):
            ppmask = (stacked["pp"] == pp).astype(float)
            mask = hmask * ppmask
            for lag in range(shock_lags + 1):
                col = f"shock_L{lag}_H{h}_pp{pp}"
                interaction_data[col] = stacked[f"{shock_var}_L{lag}"] * mask
                exog_cols.append(col)
                if lag == 0 and pp == 10:
                    p10_shock0.append(col)
                if lag == 0 and pp == 90:
                    p90_shock0.append(col)
            for lag in range(1, ar_lags + 1):
                col = f"spread{pp}_L{lag}_H{h}"
                interaction_data[col] = stacked[f"spread{pp}_L{lag}"] * mask
                exog_cols.append(col)

    stacked = pd.concat([stacked, pd.DataFrame(interaction_data, index=stacked.index)], axis=1)
    stacked = stacked.dropna(subset=["Y"] + exog_cols).copy()
    stacked["entity"] = stacked["hor"].astype(int) * 100 + stacked["pp"].astype(int)
    stacked["time_id"] = stacked["t"].astype(int)

    covariance_label = cov_type
    try:
        from linearmodels.panel import PanelOLS

        panel = stacked.set_index(["entity", "time_id"])
        mod = PanelOLS(panel["Y"], panel[exog_cols], entity_effects=True)
        res = mod.fit(cov_type=cov_type)
        params = res.params
        cov = res.cov
        nobs = int(res.nobs)
    except Exception:
        import statsmodels.api as sm

        covariance_label = "statsmodels HAC fallback"
        dummies = pd.get_dummies(stacked["entity"].astype(int), prefix="entity", drop_first=True)
        x_sm = pd.concat([stacked[exog_cols].astype(float), dummies.astype(float)], axis=1)
        res = sm.OLS(stacked["Y"].astype(float), x_sm).fit(
            cov_type="HAC", cov_kwds={"maxlags": horizons}
        )
        params = res.params
        cov = res.cov_params()
        nobs = int(res.nobs)

    def cumulative_irf(cols: list[str]) -> tuple[np.ndarray, np.ndarray]:
        coefs = np.array([params.get(c, np.nan) for c in cols])
        cov_sub = cov.loc[cols, cols].to_numpy()
        transform = np.tril(np.ones((horizons + 1, horizons + 1)))
        irf = transform @ coefs
        vcov = transform @ cov_sub @ transform.T
        se = np.sqrt(np.maximum(np.diag(vcov), 0))
        return irf, se

    p10_irf, p10_se = cumulative_irf(p10_shock0)
    p90_irf, p90_se = cumulative_irf(p90_shock0)

    all_cols = p90_shock0 + p10_shock0
    cov_sub = cov.loc[all_cols, all_cols].to_numpy()
    coefs = np.array([params.get(c, np.nan) for c in all_cols])
    rmat = np.zeros((horizons + 1, len(all_cols)))
    for h in range(horizons + 1):
        rmat[h, : h + 1] = 1.0
        rmat[h, horizons + 1 : horizons + 1 + h + 1] = -1.0
    q = rmat @ coefs
    v = rmat @ cov_sub @ rmat.T
    rank = np.linalg.matrix_rank(v)
    if rank:
        wald = float(q.T @ np.linalg.pinv(v) @ q)
        fstat = wald / rank
        df_resid = getattr(res, "df_resid", None)
        if df_resid is not None and np.isfinite(float(df_resid)):
            pvalue = float(1 - stats.f.cdf(fstat, rank, float(df_resid)))
        else:
            pvalue = float(1 - stats.chi2.cdf(wald, rank))
    else:
        fstat = np.nan
        pvalue = np.nan

    return PercentileSystemResult(
        base=base,
        shock_var=shock_var,
        horizons=np.arange(horizons + 1),
        p10_irf=p10_irf,
        p10_se=p10_se,
        p90_irf=p90_irf,
        p90_se=p90_se,
        equality_pvalue=pvalue,
        equality_fstat=fstat,
        nobs=nobs,
        covariance=covariance_label,
        coefficients=params,
        covariance_matrix=cov,
        model_result=res,
    )


def lp_summary(results: dict[str, LPResult]) -> pd.DataFrame:
    rows = []
    for name, res in results.items():
        rows.append(
            {
                "variable": name,
                "p_value": res.pvalue,
                "f_stat": res.fstat,
                "nobs": res.nobs,
                "peak_irf": float(np.nanmax(res.irf)),
                "trough_irf": float(np.nanmin(res.irf)),
                "h_peak": int(res.horizons[np.nanargmax(res.irf)]),
                "covariance": res.covariance,
            }
        )
    return pd.DataFrame(rows)


def percentile_system_summary(results: dict[str, PercentileSystemResult]) -> pd.DataFrame:
    rows = []
    for name, res in results.items():
        rows.append(
            {
                "variable": name,
                "equality_p_value": res.equality_pvalue,
                "equality_f_stat": res.equality_fstat,
                "nobs": res.nobs,
                "p90_peak_irf": float(np.nanmax(res.p90_irf)),
                "p10_trough_irf": float(np.nanmin(res.p10_irf)),
                "covariance": res.covariance,
            }
        )
    return pd.DataFrame(rows)


def variance_decomposition(
    df: pd.DataFrame,
    dep_var: str,
    shock_var: str = "sh_rr",
    horizons: int = 20,
    ar_lags: int = 2,
    shock_lags: int = 20,
) -> pd.DataFrame:
    """Python translation of the original Figure 4 logic.

    This intentionally follows the Stata denominator convention from step404,
    including its known nonstandard long-horizon behavior.
    """
    import statsmodels.api as sm

    stacked, exog_cols, shock0_cols = make_stacked_lp_data(
        df, dep_var, shock_var, horizons, ar_lags, shock_lags
    )
    dummies = pd.get_dummies(stacked["hor"].astype(int), prefix="hor", drop_first=True)
    x = pd.concat([stacked[exog_cols].astype(float), dummies.astype(float)], axis=1)
    x = sm.add_constant(x, has_constant="add")
    fit = sm.OLS(stacked["Y"].astype(float), x).fit()
    tmp = stacked[["t", "hor"]].copy()
    tmp["resid"] = fit.resid
    tmp = tmp.sort_values(["t", "hor"])
    tmp["cum_res"] = tmp.groupby("t")["resid"].cumsum()
    cum_res_sd = tmp.groupby("hor")["cum_res"].std()

    shock_sd2 = stacked["shock_L0_H0"].std() ** 2
    coefs = np.array([fit.params.get(c, 0.0) for c in shock0_cols])
    cum_shock = np.cumsum(coefs)
    cum_shock2 = np.cumsum(cum_shock**2) * shock_sd2
    contr = cum_shock2 / (cum_res_sd.to_numpy() ** 2 + (cum_shock**2) * shock_sd2)
    return pd.DataFrame({"horizon": np.arange(horizons + 1), "contribution": contr})


def historical_contribution(
    df: pd.DataFrame,
    dep_var: str,
    shock_var: str = "sh_rr",
    ar_lags: int = 2,
    shock_lags: int = 20,
    start_t: int = 49,
) -> pd.DataFrame:
    """Dynamic shock-removal simulation used for Figures 5 and 9.

    The output includes both a standard centered five-quarter mean and a
    Stata-compatible MA5 column that divides the five-quarter sum by 3, matching
    the original step405/step409 code and published figure scale.
    """
    import statsmodels.api as sm

    work = df[["t", "time", dep_var, shock_var]].copy().sort_values("t")
    for lag in range(1, ar_lags + 1):
        work[f"y_L{lag}"] = work[dep_var].shift(lag)
    for lag in range(shock_lags + 1):
        work[f"shock_L{lag}"] = work[shock_var].shift(lag)
    cols = [f"y_L{lag}" for lag in range(1, ar_lags + 1)] + [
        f"shock_L{lag}" for lag in range(shock_lags + 1)
    ]
    sample_first = work.dropna(subset=[dep_var] + cols).copy()
    first_fit = sm.OLS(sample_first[dep_var], sm.add_constant(sample_first[cols])).fit()
    work["res0"] = np.nan
    work.loc[sample_first.index, "res0"] = first_fit.resid

    # Stata step405 runs the AR-shock model, saves its residual, then
    # re-estimates the equation with that residual before forecast solve.
    sample = work.dropna(subset=[dep_var] + cols + ["res0"]).copy()
    fit_cols = cols + ["res0"]
    fit = sm.OLS(sample[dep_var], sm.add_constant(sample[fit_cols])).fit()

    by_t = work.set_index("t")
    resid = sample.set_index("t")["res0"]
    sim_all = by_t[dep_var].astype(float).copy()
    sim_no_shock = by_t[dep_var].astype(float).copy()
    for t in by_t.index[by_t.index >= start_t]:
        if t not in resid.index:
            continue
        row = {"const": 1.0}
        row0 = {"const": 1.0}
        for lag in range(1, ar_lags + 1):
            row[f"y_L{lag}"] = sim_all.get(t - lag, np.nan)
            row0[f"y_L{lag}"] = sim_no_shock.get(t - lag, np.nan)
        for lag in range(shock_lags + 1):
            row[f"shock_L{lag}"] = by_t[shock_var].get(t - lag, np.nan)
            row0[f"shock_L{lag}"] = 0.0
        row["res0"] = resid.get(t, np.nan)
        row0["res0"] = resid.get(t, np.nan)
        if any(pd.isna(v) for v in row.values()) or any(pd.isna(v) for v in row0.values()):
            continue
        sim_all.loc[t] = sum(fit.params[k] * row[k] for k in fit.params.index)
        sim_no_shock.loc[t] = sum(fit.params[k] * row0[k] for k in fit.params.index)

    out = by_t[["time", dep_var]].copy()
    out["actual_simulated"] = sim_all
    out["no_shock_counterfactual"] = sim_no_shock
    out["shock_contribution"] = sim_all - sim_no_shock
    out = out.reset_index()
    for src, prefix in [
        ("actual_simulated", "actual"),
        ("shock_contribution", "contribution"),
    ]:
        out[f"{prefix}_ma5_correct"] = out[src].rolling(5, center=True).mean()
        out[f"{prefix}_ma5_stata"] = out[src].rolling(5, center=True).sum() / 3
        out[f"{prefix}_ma3"] = out[src].rolling(3, center=True).mean()
    return out
