from __future__ import annotations

import numpy as np
import pandas as pd


PAPER_FIG3_PVALUES = {
    "D_SD_LNYBTIMP2_SA": 0.000,
    "D_SD_LNSALARYIMP_SA": 0.008,
    "D_SD_LNTOTALEXP3_SA": 0.002,
    "D_SD_LNCONS_SA": 0.006,
    "D_GINI_YBTIMP2_SA": 0.000,
    "D_GINI_SALARYIMP_SA": 0.000,
    "D_GINI_TOTALEXP3_SA": 0.000,
    "D_GINI_CONS_SA": 0.000,
    "P9010_LNYBTIMP2_SA": 0.000,
    "P9010_LNSALARYIMP_SA": 0.037,
    "P9010_LNTOTALEXP3_SA": 0.000,
    "P9010_LNCONS_SA": 0.000,
}


def fig3_comparison(summary: pd.DataFrame) -> pd.DataFrame:
    out = summary.copy()
    out["paper_p_value"] = out["variable"].map(PAPER_FIG3_PVALUES)
    out["same_rejection_5pct"] = (out["p_value"] < 0.05) == (
        out["paper_p_value"] < 0.05
    )
    out["qualitative_note"] = np.where(
        out["same_rejection_5pct"],
        "matches 5% joint-rejection conclusion",
        "differs from published 5% joint-rejection conclusion",
    )
    return out


def write_table(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False)

