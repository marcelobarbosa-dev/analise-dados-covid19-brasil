"""
src/analysis.py
----------------
Estatística descritiva, EDA e geração das figuras (estáticas + interativas)
usadas no artigo (docs/index.html), a partir do dataset processado.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
import plotly.express as px

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed" / "covid_states_processed.parquet"
ASSETS = ROOT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

PALETTE = ["#1f4e8c", "#2e8b8b", "#d9823b", "#8b3a62", "#5a7d3a", "#b23b3b"]
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#444444",
    "axes.labelcolor": "#222222",
    "text.color": "#222222",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "font.size": 11,
    "axes.grid": True,
    "grid.alpha": 0.25,
})


def load():
    return pd.read_parquet(PROCESSED)


def descritive_stats(df: pd.DataFrame) -> pd.DataFrame:
    last_day = df.sort_values("date").groupby("state").tail(1)
    stats = last_day[[
        "state", "region", "totalCases_per_100k_inhabitants",
        "deaths_per_100k_inhabitants", "lethality_rate",
        "vaccinated_per_100_inhabitants",
    ]].describe(include="all")
    stats.to_csv(ROOT / "data" / "processed" / "summary_stats_last_day.csv")
    return last_day


# ---------------------------------------------------------------------------
# Figura 1 (estática): evolução da média móvel de óbitos/100k, por região
# ---------------------------------------------------------------------------
def fig1_regional_timeseries(df: pd.DataFrame):
    regional = (
        df.groupby(["region", "date"])
        .apply(lambda g: pd.Series({
            "deaths_7d_avg_per_100k": g["deaths_7d_avg"].sum() / g["totalCases_per_100k_inhabitants"].replace(0, np.nan).count() if False else None,
        }))
    )
    # Métrica simples e correta: soma de óbitos novos (média móvel) / soma populacional proxy via per-100k agregados
    agg = (
        df.groupby(["region", "date"], as_index=False)
        .agg(deaths_7d_avg=("deaths_7d_avg", "sum"))
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, region in enumerate(sorted(agg["region"].dropna().unique())):
        sub = agg[agg["region"] == region]
        ax.plot(sub["date"], sub["deaths_7d_avg"], label=region, color=PALETTE[i % len(PALETTE)], linewidth=1.6)
    ax.set_title("Óbitos diários por COVID-19 (média móvel de 7 dias), por região do Brasil")
    ax.set_xlabel("Data")
    ax.set_ylabel("Óbitos/dia (média móvel 7d, soma dos estados da região)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(title="Região", frameon=False, ncols=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(ASSETS / "fig1_regional_timeseries.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figura 2 (estática): ranking de estados por óbitos/100k ao final da série
# ---------------------------------------------------------------------------
def fig2_ranking_states(last_day: pd.DataFrame):
    ranked = last_day.sort_values("deaths_per_100k_inhabitants", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 9))
    colors = [PALETTE[0] if r != "Sudeste" else PALETTE[3] for r in ranked["region"]]
    ax.barh(ranked["state"], ranked["deaths_per_100k_inhabitants"], color=PALETTE[0])
    ax.invert_yaxis()
    ax.set_title("Óbitos acumulados por 100 mil habitantes, por Unidade Federativa\n(fim da série histórica)")
    ax.set_xlabel("Óbitos por 100 mil habitantes")
    fig.tight_layout()
    fig.savefig(ASSETS / "fig2_ranking_states.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figura 3 (estática): letalidade por fase (pré x pós vacinação), boxplot
# ---------------------------------------------------------------------------
def fig3_lethality_by_phase(df: pd.DataFrame):
    sample = df.dropna(subset=["lethality_rate"])
    sample = sample[sample["totalCases"] > 100]  # evita ruído de denominador pequeno
    fig, ax = plt.subplots(figsize=(7, 5))
    data = [
        sample.loc[sample["wave_phase"] == "pré-vacinação", "lethality_rate"] * 100,
        sample.loc[sample["wave_phase"] == "pós-vacinação", "lethality_rate"] * 100,
    ]
    bp = ax.boxplot(data, tick_labels=["Pré-vacinação", "Pós-vacinação"], patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], [PALETTE[2], PALETTE[1]]):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    ax.set_title("Distribuição da taxa de letalidade aparente, por fase da campanha de vacinação")
    ax.set_ylabel("Taxa de letalidade (%)")
    fig.tight_layout()
    fig.savefig(ASSETS / "fig3_lethality_by_phase.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figura 4 (interativa, Plotly): dispersão cobertura vacinal x letalidade
# ---------------------------------------------------------------------------
def fig4_vaccination_vs_lethality(last_day: pd.DataFrame):
    d = last_day.dropna(subset=["vaccinated_per_100_inhabitants", "lethality_rate"]).copy()
    d["lethality_pct"] = d["lethality_rate"] * 100
    fig = px.scatter(
        d, x="vaccinated_per_100_inhabitants", y="lethality_pct",
        color="region", text="state", size="totalCases_per_100k_inhabitants",
        size_max=28,
        labels={
            "vaccinated_per_100_inhabitants": "Cobertura vacinal — 1ª dose (% da população)",
            "lethality_pct": "Taxa de letalidade aparente (%)",
            "region": "Região",
        },
        title="Cobertura vacinal vs. taxa de letalidade aparente, por UF (fim da série)",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textposition="top center", marker=dict(line=dict(width=0.5, color="white")))
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Georgia, 'Times New Roman', serif", size=13, color="#222"),
        title_font=dict(size=16),
        margin=dict(l=40, r=20, t=60, b=40),
        height=520,
    )
    fig.write_html(ASSETS / "fig4_vaccination_vs_lethality.html", include_plotlyjs="cdn", full_html=False)


# ---------------------------------------------------------------------------
# Figura 5 (interativa, Plotly): heatmap de casos/100k por estado x mês
# ---------------------------------------------------------------------------
def fig5_heatmap_monthly(df: pd.DataFrame):
    d = df.copy()
    d["month"] = d["date"].dt.to_period("M").astype(str)
    monthly_new_cases = (
        d.groupby(["state", "month"], as_index=False)["newCases"].sum()
    )
    pivot = monthly_new_cases.pivot(index="state", columns="month", values="newCases").fillna(0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0, "#f3f6fa"], [0.5, "#2e8b8b"], [1, "#1f4e8c"]],
        colorbar=dict(title="Novos casos/mês"),
    ))
    fig.update_layout(
        title="Novos casos de COVID-19 por mês, por Unidade Federativa",
        template="plotly_white",
        font=dict(family="Georgia, 'Times New Roman', serif", size=12, color="#222"),
        xaxis=dict(title="Mês", tickangle=-60),
        yaxis=dict(title="UF", autorange="reversed"),
        height=720,
        margin=dict(l=50, r=20, t=60, b=100),
    )
    fig.write_html(ASSETS / "fig5_heatmap_monthly.html", include_plotlyjs="cdn", full_html=False)


def correlation_summary(last_day: pd.DataFrame) -> dict:
    d = last_day.dropna(subset=["vaccinated_per_100_inhabitants", "lethality_rate"])
    corr = d["vaccinated_per_100_inhabitants"].corr(d["lethality_rate"])
    top5 = last_day.sort_values("deaths_per_100k_inhabitants", ascending=False).head(5)[["state", "deaths_per_100k_inhabitants"]]
    bottom5 = last_day.sort_values("deaths_per_100k_inhabitants", ascending=True).head(5)[["state", "deaths_per_100k_inhabitants"]]
    out = {
        "pearson_corr_vacc_lethality": round(float(corr), 4),
        "top5_deaths_per_100k": top5.to_dict("records"),
        "bottom5_deaths_per_100k": bottom5.to_dict("records"),
        "national_mean_deaths_per_100k": round(float(last_day["deaths_per_100k_inhabitants"].mean()), 2),
        "national_mean_lethality_pct": round(float(last_day["lethality_rate"].mean()) * 100, 2),
    }
    return out


if __name__ == "__main__":
    df = load()
    last_day = descritive_stats(df)
    fig1_regional_timeseries(df)
    fig2_ranking_states(last_day)
    fig3_lethality_by_phase(df)
    fig4_vaccination_vs_lethality(last_day)
    fig5_heatmap_monthly(df)
    summary = correlation_summary(last_day)
    import json
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    with open(ROOT / "data" / "processed" / "correlation_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print("[analysis] Figuras salvas em docs/assets/")
