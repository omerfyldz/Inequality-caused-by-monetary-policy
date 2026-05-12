from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .local_projection import LPResult


RECESSIONS = [
    (1980.00, 1980.50),
    (1981.75, 1982.75),
    (1990.50, 1991.00),
    (2001.00, 2001.75),
    (2007.75, 2009.25),
]

SERIES_LABELS = {
    "YBTIMP2": "Income",
    "SALARYIMP": "Earnings",
    "TOTALEXP3": "Expenditure",
    "CONS": "Consumption",
    "INCNTIMP2": "After-tax income",
}

FIG3_VARS = [
    ("D_SD_LNYBTIMP2_SA", "Income", "st.dev."),
    ("D_SD_LNSALARYIMP_SA", "Earnings", "st.dev."),
    ("D_SD_LNTOTALEXP3_SA", "Expenditure", "st.dev."),
    ("D_SD_LNCONS_SA", "Consumption", "st.dev."),
    ("D_GINI_YBTIMP2_SA", "Income", "Gini"),
    ("D_GINI_SALARYIMP_SA", "Earnings", "Gini"),
    ("D_GINI_TOTALEXP3_SA", "Expenditure", "Gini"),
    ("D_GINI_CONS_SA", "Consumption", "Gini"),
    ("P9010_LNYBTIMP2_SA", "Income", "90-10"),
    ("P9010_LNSALARYIMP_SA", "Earnings", "90-10"),
    ("P9010_LNTOTALEXP3_SA", "Expenditure", "90-10"),
    ("P9010_LNCONS_SA", "Consumption", "90-10"),
]


def paper_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 180,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#e5e5e5",
            "font.size": 9,
        }
    )


def shade_recessions(ax, ymin=None, ymax=None, color="#d8d8d8") -> None:
    for start, end in RECESSIONS:
        ax.axvspan(start, end, color=color, alpha=0.55, lw=0)


def savefig(fig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")


def plot_descriptive_figure(df: pd.DataFrame, outpath: str | Path | None = None):
    paper_style()
    panels = [
        (
            "Panel A: Cross-sectional standard deviation",
            [
                ("C_SD_LNYBTIMP2_SA", "Income", "black", "-"),
                ("C_SD_LNINCNTIMP2_SA", "After-tax income", "#0099aa", "--"),
                ("C_SD_LNSALARYIMP_SA", "Earnings", "#cc2c2c", "-"),
                ("C_SD_LNTOTALEXP3_SA", "Expenditure", "#2b6cb0", "-"),
                ("C_SD_LNCONS_SA", "Consumption", "#2f855a", "-"),
            ],
            "Standard deviation",
        ),
        (
            "Panel B: Gini coefficients",
            [
                ("C_GINI2_YBTIMP2_SA", "Income", "black", "-"),
                ("C_GINI2_INCNTIMP2_SA", "After-tax income", "#0099aa", "--"),
                ("C_GINI2_SALARYIMP_SA", "Earnings", "#cc2c2c", "-"),
                ("C_GINI2_TOTALEXP3_SA", "Expenditure", "#2b6cb0", "-"),
                ("C_GINI2_CONS_SA", "Consumption", "#2f855a", "-"),
            ],
            "Gini",
        ),
        (
            "Panel C: 90-10 percentile gap",
            [
                ("C_P9010_LNYBTIMP2_SA", "Income", "black", "-"),
                ("C_P9010_LNINCNTIMP2_SA", "After-tax income", "#0099aa", "--"),
                ("C_P9010_LNSALARYIMP_SA", "Earnings", "#cc2c2c", "-"),
                ("C_P9010_LNTOTALEXP3_SA", "Expenditure", "#2b6cb0", "-"),
                ("C_P9010_LNCONS_SA", "Consumption", "#2f855a", "-"),
            ],
            "90-10",
        ),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    for ax, (title, series, ylabel) in zip(axes, panels):
        shade_recessions(ax)
        for col, label, color, ls in series:
            ax.plot(df["time"], df[col], color=color, linestyle=ls, lw=1.6, label=label)
        ax.set_title(title, loc="left")
        ax.set_ylabel(ylabel)
        ax.set_xlim(1980, 2009)
    axes[0].legend(ncol=5, loc="upper left", frameon=False)
    axes[-1].set_xlabel("Year")
    if outpath:
        savefig(fig, outpath)
    return fig


def plot_irf_grid(
    results: dict[str, LPResult],
    variables=FIG3_VARS,
    outpath: str | Path | None = None,
    title: str | None = None,
):
    paper_style()
    fig, axes = plt.subplots(3, 4, figsize=(11, 7.5), sharex=True)
    for ax, (var, label, ylabel) in zip(axes.ravel(), variables):
        res = results[var]
        h = res.horizons
        ax.fill_between(h, res.lower_165se, res.upper_165se, color="#dddddd")
        ax.fill_between(h, res.lower_1se, res.upper_1se, color="#a6a6a6")
        ax.plot(h, res.irf, color="black", lw=1.8)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(f"{label} (p-val = {res.pvalue:.3f})")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 20)
    for ax in axes[-1, :]:
        ax.set_xlabel("Quarters")
    if title:
        fig.suptitle(title, y=1.01)
    if outpath:
        savefig(fig, outpath)
    return fig


def plot_simple_grid(
    data: dict[str, pd.DataFrame],
    y_col: str,
    title_col: str = "title",
    outpath: str | Path | None = None,
    ylabel: str = "",
    ncols: int = 4,
):
    paper_style()
    n = len(data)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 2.5 * nrows), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, (name, frame) in zip(axes, data.items()):
        ax.plot(frame.iloc[:, 0], frame[y_col], color="black", lw=1.8)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(frame.attrs.get(title_col, name))
        ax.set_ylabel(ylabel)
    for ax in axes[n:]:
        ax.axis("off")
    if outpath:
        savefig(fig, outpath)
    return fig

