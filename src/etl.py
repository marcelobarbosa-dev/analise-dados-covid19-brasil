"""
src/etl.py
----------
Pipeline determinístico de ingestão, limpeza e enriquecimento dos dados de
COVID-19 por Unidade Federativa do Brasil.

Fonte primária oficial dos dados: Brasil.IO (dataset `covid19`, tabela
`caso_full`) — https://brasil.io/dataset/covid19/caso_full/
Cópia estruturada utilizada como insumo direto: wcota/covid19br, que agrega
Brasil.IO e demais fontes oficiais em arquivos CSV versionados por data.
Ver `data/data_dictionary.md` para a justificativa completa da proveniência.

Uso:
    python src/etl.py            # baixa (se necessário), limpa e persiste
    python src/etl.py --no-download   # usa apenas os arquivos já em data/raw/
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

BASE_URL = "https://raw.githubusercontent.com/wcota/covid19br/master"
RAW_FILES = [
    "cases-brazil-states.csv",
    "cities_info.csv",
]


def download_raw_data(force: bool = False) -> None:
    """Baixa os arquivos brutos a partir da fonte estruturada (ver
    data_dictionary.md). Idempotente: não baixa de novo se o arquivo já
    existir, a menos que force=True."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename in RAW_FILES:
        dest = RAW_DIR / filename
        if dest.exists() and not force:
            print(f"[download] {filename} já existe, pulando.")
            continue
        url = f"{BASE_URL}/{filename}"
        print(f"[download] {url} -> {dest}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as fh:
            fh.write(resp.read())


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    states = pd.read_csv(
        RAW_DIR / "cases-brazil-states.csv",
        parse_dates=["date"],
        dtype={"state": "string", "city": "string", "country": "string"},
    )
    cities_info = pd.read_csv(
        RAW_DIR / "cities_info.csv",
        dtype={"state": "string", "region": "string"},
    )
    return states, cities_info


def clean_and_transform(states: pd.DataFrame, cities_info: pd.DataFrame) -> pd.DataFrame:
    """Aplica limpeza, tipagem e engenharia de métricas derivadas.
    Ver data/data_dictionary.md para a lógica de cada coluna derivada."""
    df = states.copy()

    # 1) Remove o agregado nacional "TOTAL" para evitar dupla contagem na
    #    análise por UF (ele é redundante com a soma dos 27 estados).
    df = df[df["state"] != "TOTAL"].copy()

    # 2) Tipagem explícita das colunas numéricas de interesse.
    numeric_cols = [
        "newDeaths", "deaths", "newCases", "totalCases",
        "deaths_per_100k_inhabitants", "totalCases_per_100k_inhabitants",
        "deaths_by_totalCases",
        "vaccinated_per_100_inhabitants", "vaccinated_second_per_100_inhabitants",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3) Enriquecimento com a região geográfica de cada UF (join 1:N -> moda).
    region_by_state = (
        cities_info.groupby("state")["region"]
        .agg(lambda s: s.mode().iat[0] if not s.mode().empty else np.nan)
    )
    df["region"] = df["state"].map(region_by_state)

    # 4) Métrica derivada: taxa de letalidade aparente, com proteção contra
    #    divisão por zero (casos acumulados == 0 no início da série).
    df["lethality_rate"] = np.where(
        df["totalCases"] > 0, df["deaths"] / df["totalCases"], np.nan
    )

    # 5) Médias móveis de 7 dias por estado, para suavizar efeito de
    #    subnotificação em fins de semana/feriados e evidenciar ondas.
    df = df.sort_values(["state", "date"])
    df["cases_7d_avg"] = (
        df.groupby("state")["newCases"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    )
    df["deaths_7d_avg"] = (
        df.groupby("state")["newDeaths"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    )

    # 6) Fase da campanha de vacinação: ausência de dado de vacinação é
    #    tratada como ausência estrutural (pré-campanha), nunca imputada
    #    como zero, para não distorcer médias de cobertura vacinal.
    df["wave_phase"] = np.where(
        df["vaccinated_per_100_inhabitants"].notna() & (df["vaccinated_per_100_inhabitants"] > 0),
        "pós-vacinação",
        "pré-vacinação",
    )

    # 7) Coluna auxiliar de ano para agregações anuais.
    df["year"] = df["date"].dt.year

    # 8) Ordenação final e reset de índice (reprodutibilidade determinística).
    df = df.sort_values(["state", "date"]).reset_index(drop=True)

    return df


def persist(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = PROCESSED_DIR / "covid_states_processed.parquet"
    csv_path = PROCESSED_DIR / "covid_states_processed.csv.gz"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False, compression="gzip")
    print(f"[persist] {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB)")
    print(f"[persist] {csv_path} ({csv_path.stat().st_size / 1e6:.2f} MB)")


def run(download: bool = True) -> pd.DataFrame:
    if download:
        download_raw_data()
    states, cities_info = load_raw()
    processed = clean_and_transform(states, cities_info)
    persist(processed)
    print(f"[etl] Linhas processadas: {len(processed):,}")
    print(f"[etl] UFs: {processed['state'].nunique()} | Período: "
          f"{processed['date'].min().date()} a {processed['date'].max().date()}")
    return processed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline ETL COVID-19 Brasil (por UF)")
    parser.add_argument("--no-download", action="store_true",
                         help="Não baixa os dados brutos; usa apenas o que já está em data/raw/")
    args = parser.parse_args()
    try:
        run(download=not args.no_download)
    except Exception as exc:  # noqa: BLE001
        print(f"[etl] ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
