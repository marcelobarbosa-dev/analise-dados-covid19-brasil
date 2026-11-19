# Dicionário de Dados

Este documento descreve, em conformidade com o princípio **Interoperable** dos
FAIR Guiding Principles, as variáveis utilizadas no pipeline de análise. Todas
as variáveis abaixo pertencem ao arquivo processado final
`data/processed/covid_states_processed.parquet`, gerado por `src/etl.py` a
partir dos dados brutos em `data/raw/`.

## Proveniência dos dados

| Item | Descrição |
|---|---|
| Fonte primária oficial | Brasil.IO — dataset `covid19`, tabela `caso_full` (boletins das Secretarias Estaduais de Saúde) |
| URL da fonte primária | https://brasil.io/dataset/covid19/caso_full/ |
| Cópia estruturada utilizada | wcota/covid19br — compilação que consolida Brasil.IO, Ministério da Saúde e demais fontes nos arquivos `cases-brazil-states.csv`, `cases-brazil-cities.csv` e `cities_info.csv` |
| URL da cópia estruturada | https://github.com/wcota/covid19br |
| Motivo da cópia estruturada | O arquivo bruto `caso_full.csv.gz` possui ~88 MB e granularidade diária por município (>50 MB), o que — conforme a norma da disciplina — dispensa seu versionamento direto; optou-se por uma camada já agregada, auditável e com a mesma licença, mantendo a rastreabilidade até a fonte original |
| Licença dos dados | CC BY-SA 4.0 (dados oriundos do Brasil.IO) / CC BY 4.0 (demais colunas agregadas) |
| Cobertura temporal | 2020-02-25 a 2022-03 (ver `data/raw/cases-brazil-states.csv`) |
| Cobertura geográfica | 27 Unidades Federativas do Brasil (26 estados + Distrito Federal) |
| Script de download | `src/etl.py`, função `download_raw_data()` |

## Tabela bruta: `data/raw/cases-brazil-states.csv`

| Variável | Tipo primitivo | Descrição |
|---|---|---|
| `epi_week` | int | Número da semana epidemiológica (Ministério da Saúde) |
| `date` | date (ISO 8601) | Data de divulgação do boletim |
| `country` | string | Sempre `Brazil` |
| `state` | string (categórico) | Sigla da Unidade Federativa (ex.: `SP`, `RJ`) ou `TOTAL` (agregado nacional, descartado no ETL) |
| `city` | string | Sempre `TOTAL` neste arquivo (nível estadual) |
| `newDeaths` | int | Novos óbitos divulgados no dia |
| `deaths` | int | Óbitos acumulados |
| `newCases` | int | Novos casos confirmados divulgados no dia |
| `totalCases` | int | Casos confirmados acumulados |
| `deaths_per_100k_inhabitants` | float | Óbitos acumulados por 100 mil habitantes |
| `totalCases_per_100k_inhabitants` | float | Casos acumulados por 100 mil habitantes |
| `deaths_by_totalCases` | float | Taxa de letalidade aparente (`deaths` / `totalCases`) |
| `vaccinated_per_100_inhabitants` | float | % da população com 1ª dose aplicada |
| `vaccinated_second_per_100_inhabitants` | float | % da população com 2ª dose / esquema completo |

## Tabela auxiliar: `data/raw/cities_info.csv`

| Variável | Tipo primitivo | Descrição |
|---|---|---|
| `state` | string | Sigla da UF |
| `region` | string (categórico) | Região geográfica (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) |
| `pop2021` | int | População estimada (IBGE, 2021), usada para reagregar população por estado |

## Variáveis derivadas (criadas em `src/etl.py`)

| Variável | Tipo | Fórmula / Lógica | Finalidade de pesquisa |
|---|---|---|---|
| `region` | string (categórico) | *join* de `state` com `cities_info.csv` (moda por UF) | Permite agregações regionais (RQ1, RQ3) |
| `lethality_rate` | float | `deaths / totalCases`, com proteção para divisão por zero (`NaN` quando `totalCases == 0`) | Mede a gravidade clínica aparente ao longo do tempo (RQ2) |
| `cases_7d_avg` | float | Média móvel de 7 dias de `newCases`, por estado | Suaviza ruído de subnotificação em finais de semana/feriados para identificar ondas (RQ1, RQ3) |
| `deaths_7d_avg` | float | Média móvel de 7 dias de `newDeaths`, por estado | Idem, para óbitos |
| `wave_phase` | string (categórico) | `pré-vacinação` se `vaccinated_per_100_inhabitants` ausente/zero; `pós-vacinação` caso contrário | Compara letalidade antes/depois do início da campanha de vacinação (RQ2, RQ3) |
| `year` | int | Extraído de `date` | Agregações anuais |

## Tratamento de valores ausentes

- Colunas de vacinação (`vaccinated*`) são `NaN` antes do início da campanha
  (jan/2021): tratadas como **ausência estrutural**, não como erro — mantidas
  como `NaN` e tipadas como `wave_phase = "pré-vacinação"`, nunca imputadas
  com zero para não distorcer médias.
- Linhas com `state == "TOTAL"` (agregado nacional, já redundante com a soma
  dos estados) são **descartadas** no ETL para evitar dupla contagem.
- `newDeaths`/`newCases` negativos (retificações de boletins, raras no
  conjunto) são preservados e documentados — **não são zerados**, pois
  representam correções oficiais e sua remoção violaria a rastreabilidade
  exigida pelos princípios FAIR.

## Formato de persistência

Os dados processados são persistidos em `data/processed/` em dois formatos
abertos, conforme exigido pelo princípio *Interoperable*:

- `covid_states_processed.parquet` — Apache Parquet (tipagem colunar preservada, leitura eficiente)
- `covid_states_processed.csv.gz` — CSV comprimido (compatibilidade universal)
