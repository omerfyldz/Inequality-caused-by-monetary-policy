from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL_ROOT = PROJECT_ROOT.parent / "replication_folder"


@dataclass(frozen=True)
class Paths:
    project_root: Path
    original_root: Path
    workfiles: Path
    source_files: Path
    figures: Path
    tables: Path


def load_config(path: str | Path | None = None) -> dict:
    config_path = Path(path) if path is not None else PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = PROJECT_ROOT / "config.example.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_paths(config_path: str | Path | None = None) -> Paths:
    cfg = load_config(config_path)
    original_root = Path(cfg.get("original_replication_root", DEFAULT_ORIGINAL_ROOT)).expanduser()
    if not original_root.is_absolute():
        original_root = (PROJECT_ROOT / original_root).resolve()
    return Paths(
        project_root=PROJECT_ROOT,
        original_root=original_root,
        workfiles=original_root / "workfiles",
        source_files=original_root / "source_files",
        figures=PROJECT_ROOT / "outputs" / "figures",
        tables=PROJECT_ROOT / "outputs" / "tables",
    )


def ensure_output_dirs(paths: Paths | None = None) -> None:
    paths = paths or get_paths()
    paths.figures.mkdir(parents=True, exist_ok=True)
    paths.tables.mkdir(parents=True, exist_ok=True)


def read_stata(path: str | Path) -> pd.DataFrame:
    return pd.read_stata(Path(path), convert_categoricals=False)


def load_cex_short(paths: Paths | None = None) -> pd.DataFrame:
    paths = paths or get_paths()
    df = read_stata(paths.workfiles / "all_CEX_data_short.dta")
    return add_quarter_index(df)


def load_cex_cohort(paths: Paths | None = None) -> pd.DataFrame:
    paths = paths or get_paths()
    df = read_stata(paths.workfiles / "all_CEX_data_cohort.dta")
    return add_quarter_index(df)


def add_quarter_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["year"] = out["year"].astype(int)
    out["quarter"] = out["quarter"].astype(int)
    out["period"] = pd.PeriodIndex.from_fields(
        year=out["year"], quarter=out["quarter"], freq="Q-DEC"
    )
    if "time" not in out:
        out["time"] = out["year"] + (out["quarter"] - 1) / 4
    return out.sort_values(["year", "quarter"]).reset_index(drop=True)


def quarter_span(df: pd.DataFrame, column: str) -> dict:
    s = df.loc[df[column].notna(), ["period", column]]
    if s.empty:
        return {"variable": column, "n": 0, "start": None, "end": None}
    return {
        "variable": column,
        "n": int(s[column].notna().sum()),
        "start": str(s["period"].iloc[0]),
        "end": str(s["period"].iloc[-1]),
        "mean": float(s[column].mean()),
        "std": float(s[column].std()),
    }


def audit_variables(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame([quarter_span(df, c) for c in columns])


def load_macro_data(paths: Paths | None = None) -> pd.DataFrame:
    """Recreate Stata step090's macro_data_all from read-only source files.

    The original final workfiles do not include macro_data_all, so this reads the
    bundled daily/monthly .dta files plus the Quarterly sheet in JMEinequality.xls.
    """
    paths = paths or get_paths()
    source = paths.source_files
    monthly = read_stata(source / "monthly.dta")
    daily = read_stata(source / "daily.dta")
    quarterly = pd.read_excel(source / "JMEinequality.xls", sheet_name="Quarterly")
    if "DATE" not in quarterly.columns:
        raise ValueError("Quarterly sheet must contain DATE.")
    quarterly["DATE"] = pd.to_datetime(quarterly["DATE"])
    quarterly["year"] = quarterly["DATE"].dt.year
    quarterly["quarter"] = quarterly["DATE"].dt.quarter

    df = quarterly.merge(daily, on=["year", "quarter"], how="outer")
    df = df.merge(monthly, on=["year", "quarter"], how="outer")
    df = df.sort_values(["year", "quarter"]).reset_index(drop=True)

    gdpdef = df["GDPDEF"]
    derived = {
        "lnGDP": np.log(df["GDPC1"]),
        "lnConsumption": np.log(df["PCECC96"]),
        "lnInvestment": np.log(df["GPDIC96"]),
        "UE": df["UNRATE"],
        "lnPGDP": np.log(gdpdef),
        "lnSP500": np.log(df["SPASTT01USM661N"]),
        "FFR": df["FEDFUNDS"],
        "lnHousePrice": np.log(df["CSUSHPISA"]),
        "lnHousePrice2": np.log(df["USSTHPI"]),
        "lnBusinessIncome": np.log((df["PROPINC"] + df["CP"]) / gdpdef),
        "lnWagesSalaries": np.log(df["A576RC1Q027SBEA"] / gdpdef),
        "lnFinancialIncome": np.log(df["W210RC1Q027SBEA"] / gdpdef),
        "lnTransferIncome": np.log(df["A577RC1Q027SBEA"] / gdpdef),
        "lnDurables": np.log(df["PCDG"] / gdpdef),
        "lnNonDurables": np.log(df["PCND"] / gdpdef),
        "lnServices": np.log(df["PCESV"] / gdpdef),
        "lnBusinessIncomeN": np.log(df["PROPINC"] + df["CP"]),
        "lnWagesSalariesN": np.log(df["A576RC1Q027SBEA"]),
        "lnFinancialIncomeN": np.log(df["W210RC1Q027SBEA"]),
        "lnTransferIncomeN": np.log(df["A577RC1Q027SBEA"]),
    }
    keep = df[["year", "quarter", "DGS10"]].copy()
    for col, val in derived.items():
        keep[col] = val
    for col in [c for c in keep.columns if c.startswith("ln")]:
        keep["d" + col] = keep[col].diff() * 100
    return add_quarter_index(keep)


def load_analysis_panel(paths: Paths | None = None) -> pd.DataFrame:
    cex = load_cex_short(paths)
    macro = load_macro_data(paths)
    cols = ["year", "quarter"] + [
        c for c in macro.columns if c not in {"year", "quarter", "period", "time"}
    ]
    out = cex.merge(macro[cols], on=["year", "quarter"], how="left")
    return add_quarter_index(out)


def hp_cycle(series: pd.Series, lamb: float = 1600.0) -> pd.Series:
    from statsmodels.tsa.filters.hp_filter import hpfilter

    s = series.astype(float)
    if s.notna().sum() < 8:
        return pd.Series(index=s.index, dtype=float)
    cycle, _ = hpfilter(s.dropna(), lamb=lamb)
    out = pd.Series(index=s.index, dtype=float)
    out.loc[cycle.index] = cycle
    return out
