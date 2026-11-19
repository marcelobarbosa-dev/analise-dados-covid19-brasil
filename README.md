# COVID-19 no Brasil: Padrões Temporais, Regionais e o Efeito da Vacinação

[![Licença: MIT](https://img.shields.io/badge/licença%20código-MIT-blue.svg)](LICENSE)
[![Dados: CC BY--SA 4.0](https://img.shields.io/badge/licença%20dados-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![FAIR](https://img.shields.io/badge/princípios-FAIR-2e8b8b.svg)](data/data_dictionary.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-1f4e8c.svg)](requirements.txt)

> Projeto Final da disciplina **Linguagem de Programação (Análise e
> Visualização de Dados com Python)** — Bacharelado em Sistemas de
> Informação, 6º Período.
>
> **Autor:** Marcelo Barbosa de Oliveira Junior
> **Artigo publicado:** _ver seção "Artefatos" abaixo_

## Resumo executivo

Este projeto consolida, limpa e analisa a série histórica de casos e óbitos
por COVID-19 nas 27 Unidades Federativas do Brasil (2020–2022), investigando
padrões temporais e regionais das ondas epidêmicas e a relação entre
cobertura vacinal e letalidade aparente. O pipeline é determinístico,
reprodutível e segue os princípios internacionais **FAIR** (Findable,
Accessible, Interoperable, Reusable) de ciência aberta.

## Palavras-chave

`covid-19` · `análise de dados` · `python` · `pandas` · `ciência de dados abertos` · `FAIR` · `saúde pública` · `visualização de dados`

## Perguntas de pesquisa

1. **RQ1** — Como os casos e óbitos por 100 mil habitantes evoluíram ao
   longo de 2020–2022 entre as regiões e estados brasileiros, e quais UFs
   tiveram os piores/melhores desfechos acumulados?
2. **RQ2** — Existe relação entre a cobertura vacinal (1ª dose) e a taxa de
   letalidade aparente observada nos estados?
3. **RQ3** — A chegada da vacinação está associada a uma redução
   estatisticamente visível na letalidade aparente, quando comparadas as
   fases pré- e pós-vacinação?

## Artefatos finais

| Artefato | Local |
|---|---|
| Repositório GitHub (este) | você está nele |
| Artigo acadêmico em HTML (GitHub Pages) | `docs/index.html` → publicado em `https://marcelobarbosa-dev.github.io/analise-dados-covid19-brasil/` |

## Como reproduzir

```bash
# 1. Clonar o repositório
git clone https://github.com/marcelobarbosa-dev/analise-dados-covid19-brasil.git
cd analise-dados-covid19-brasil

# 2. Criar e ativar um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar as dependências com versões travadas
pip install -r requirements.txt

# 4. Rodar o pipeline de ETL (baixa os dados brutos e gera data/processed/)
python src/etl.py

# 5. Gerar as figuras do artigo (salvas em docs/assets/)
python src/analysis.py

# 6. (Opcional) Explorar interativamente
jupyter notebook notebooks/analise_exploratoria.ipynb
```

## Estrutura do repositório

```
analise-dados-covid19-brasil/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                      # Dados brutos (baixados por src/etl.py)
│   ├── processed/                # Dados tratados (.parquet e .csv.gz)
│   └── data_dictionary.md        # Dicionário de dados (FAIR)
├── notebooks/
│   └── analise_exploratoria.ipynb
├── src/
│   ├── __init__.py
│   ├── etl.py                    # Ingestão, limpeza e métricas derivadas
│   └── analysis.py               # Estatística descritiva e geração de figuras
└── docs/                         # Artigo científico (GitHub Pages)
    ├── index.html
    └── assets/
```

## Declaração de aderência aos princípios FAIR

- **Findable:** metadados de autoria, disciplina e instituição no cabeçalho
  do artigo (`docs/index.html`); link perene para a fonte original dos dados
  em `data/data_dictionary.md`.
- **Accessible:** repositório público, sem barreiras de autenticação; artigo
  publicado via GitHub Pages com layout responsivo.
- **Interoperable:** dicionário de variáveis completo em
  `data/data_dictionary.md`; dados processados em Parquet e CSV.GZ.
- **Reusable:** licença MIT (código) e CC BY-SA 4.0 (dados), com
  `requirements.txt` de versões travadas para reprodução do ambiente.

## Fonte dos dados e licença

Dados derivados do **Brasil.IO** (dataset `covid19`/`caso_full`,
CC BY-SA 4.0) — https://brasil.io/dataset/covid19/caso_full/. Ver
`data/data_dictionary.md` para a cadeia completa de proveniência. Código
sob licença MIT (ver `LICENSE`).
