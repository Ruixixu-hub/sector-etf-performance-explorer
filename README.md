# Sector ETF Performance Explorer

## Quick Links
- Demo video: `https://video.xjtlu.edu.cn/Mediasite/Play/3e6cbfb2a6d944a6aba30fd584be40bb1d`
- Streamlit product: `<add Streamlit app link here>`

## Project overview
**Sector ETF Performance Explorer** is an interactive Streamlit tool that helps users compare how major U.S. market sectors behaved over time through sector ETFs. It is designed for **beginner investors** who need a clearer way to read historical sector behaviour and **finance students** who want a practical way to connect portfolio concepts to real data.

The core problem behind the project is that individual stocks can be **fragmented, noisy, and highly volatile**, which makes broader market patterns difficult to interpret. This project therefore uses **sector ETFs** as a more structured lens for comparing performance, risk, diversification, holdings, and representative stock behaviour across time.

The final product focuses on six SPDR sector ETFs:
- **XLK** — Technology
- **XLE** — Energy
- **XLF** — Financials
- **XLV** — Health Care
- **XLI** — Industrials
- **XLP** — Consumer Staples

The app allows users to compare ETFs over a chosen date range and explore:
- cumulative return and optional absolute price;
- annualized volatility, maximum drawdown, and rolling volatility;
- risk-return trade-offs and return correlation;
- holdings structure and full holdings tables;
- representative stock drill-down;
- downloadable filtered outputs.

---

## 1. Problem and target user
This project asks: **how can non-expert users compare sector behaviour more clearly when individual stock price paths are often too messy to interpret directly?**

The intended users are:
- **Beginner investors**, who need a cleaner historical comparison tool rather than a collection of separate stock charts;
- **Finance students**, who want a practical way to study return, volatility, drawdown, diversification, holdings structure, and ETF-versus-stock behaviour using real market data.

The aim is educational and analytical rather than predictive. The tool is designed to support **historical sector comparison**, not investment advice.

---

## 2. Data
### Data sources
This project uses two main data sources.

**1. WRDS - CRSP** for ETF and representative stock price data  
Tables used:
- `crsp.stocknames_v2`
- `crsp.dsf_v2`

**2. Official SPDR holdings files** for ETF holdings snapshots  
Downloaded manually from official SPDR holdings pages and saved as Excel files.

### Access dates
- **WRDS - CRSP ETF and representative stock data:** accessed on **2026-04-19** ,and **2026-04-22** for additional **XLI, XLP**
- **Official SPDR holdings files:**
  - **XLK, XLE, XLF, XLV:** downloaded on **2026-04-19**
  - **XLI, XLP:** downloaded on **2026-04-22**

### Main fields used
**ETF / representative stock price data**
- ticker
- permno
- date
- daily close / price
- daily return
- daily volume

**Holdings data**
- holding name
- holding ticker
- portfolio weight
- sector
- shares held
- local currency

### Representative stock mapping
- **XLK → NVDA**
- **XLE → XOM**
- **XLF → JPM**
- **XLV → LLY**
- **XLI → CAT**
- **XLP → PG**

---

## 3. Methods
The full analytical workflow is documented in [`notebook.ipynb`](notebook.ipynb), and the user-facing product is implemented in [`app.py`](app.py).

### Main Python workflow
1. **Retrieve WRDS / CRSP data with SQL**
   - query ETF identifiers and daily price data;
   - query representative stock identifiers and daily price data.

2. **Clean and validate ETF price data**
   - rename columns and standardize data types;
   - parse dates and sort observations;
   - check duplicates, missing values, and date coverage;
   - compute cumulative return, annualized volatility, maximum drawdown, rolling volatility, and correlation-ready outputs.

3. **Clean and validate holdings files**
   - parse six manually downloaded SPDR Excel files;
   - remove non-tabular text and inconsistent formatting;
   - standardize holdings columns;
   - build both full holdings outputs and top-10 holdings outputs.

4. **Build representative stock comparison outputs**
   - align each ETF with one sector-typical company;
   - clean daily stock price data;
   - calculate price-based metrics;
   - prepare comparison-ready files for the app.

5. **Create app-facing processed files**
   - save validated ETF outputs;
   - save validated representative stock outputs;
   - save holdings summaries and validation summaries used directly by the app.

### Main Python tools
- `streamlit`
- `pandas`
- `numpy`
- `plotly`
- `matplotlib`
- `wrds`
- `openpyxl`

---

## 4. Key findings
- **XLE (Energy)** delivered the strongest cumulative return over the project period, at approximately **184.7%**.
- **XLP (Consumer Staples)** showed the **lowest annualized volatility** and the **shallowest drawdown**, giving the most defensive historical profile among the six ETFs.
- **XLK (Technology)** performed strongly but still experienced the **deepest maximum drawdown**, showing that volatility and downside severity did not rank in exactly the same way across sectors.
- Correlation results show that some sector pairs moved much more similarly than others, so sector selection affects **diversification potential**, not only return.
- Representative stock comparisons show that a large company may reflect part of a sector story, but the ETF usually provides a smoother risk profile because it spreads firm-specific shocks across multiple holdings.

---

## 5. Repository structure
```text
ETF_Sector_Explorer/
├── app.py
├── notebook.ipynb
├── README.md
├── requirements.txt
└── data/
    ├── processed/
    │   ├── dataset_validation_summary.txt
    │   ├── etf_metrics_summary.csv
    │   ├── etf_prices_clean.csv
    │   ├── etf_prices_cleaning_summary.txt
    │   ├── etf_prices_metrics_ready.csv
    │   ├── holdings_all_clean.csv
    │   ├── holdings_cleaning_summary.txt
    │   ├── holdings_top10.csv
    │   └── representative_stock/
    │       ├── representative_stock_mapping.csv
    │       ├── representative_stocks_clean.csv
    │       ├── representative_stocks_metrics_ready.csv
    │       ├── representative_stocks_summary.csv
    │       └── representative_stocks_validation_summary.txt
    ├── raw/
    │   └── representative_stock/
    ├── raw_holdings/
    └── raw_wrds/
```

### File roles
- [`app.py`](app.py): final Streamlit application
- [`notebook.ipynb`](notebook.ipynb): full analytical workflow and reproducibility notebook
- [`requirements.txt`](requirements.txt): project dependencies
- `data/processed/`: final processed files used directly by the app
- `data/raw_wrds/`: raw ETF WRDS / CRSP outputs
- `data/raw/representative_stock/`: raw WRDS representative stock outputs
- `data/raw_holdings/`: original SPDR holdings Excel files


---

## 6. How to run locally
### Option A: Run the final app directly
This is the fastest way to reproduce the finished product.

1. Clone or download the repository.
2. Open a terminal in the project root.
3. Create and activate a virtual environment.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the app:
   ```bash
   streamlit run app.py
   ```

The app reads the already-prepared files in `data/processed/`, so a WRDS login is **not required** to run the final product.

### Option B: Rebuild the workflow from the notebook
Use this if you want to inspect or reproduce the analytical workflow behind the app.

Before running the notebook from top to bottom, make sure the repository still includes the manually downloaded SPDR holdings files in `data/raw_holdings/`.
The notebook uses the holdings Excel files in `data/raw_holdings/` as inputs for the holdings cleaning pipeline, so these files must be present if the workflow is rebuilt.

1. Open [`notebook.ipynb`](notebook.ipynb).
2. Make sure dependencies from `requirements.txt` are installed.
3. Run the notebook from top to bottom.
4. For WRDS sections, use your own WRDS username when prompted.
5. The notebook saves cleaned outputs into `data/processed/`.

> Full notebook reproduction requires **WRDS access**. The final app itself does not.

---

## 7. Demo and Access
- **Demo video link:** `https://video.xjtlu.edu.cn/Mediasite/Play/3e6cbfb2a6d944a6aba30fd584be40bb1d`
- **Streamlit product link:** `<add Streamlit app link here>`

If the app is not available, the project can still be fully viewed locally by running:

```bash
streamlit run app.py
```

---

## 8. Limitations and next steps
### Limitations
- The holdings analysis uses **snapshot files**, not a full historical holdings time series.
- The project focuses on six SPDR sector ETFs, so it is a **targeted educational comparison tool**, not a full market-screening platform.
- Representative stocks are chosen for educational clarity and sector intuition; they are **not necessarily the ETF’s largest holding**.
- The notebook’s full raw-data rebuild depends on WRDS access, which may limit complete reproduction for users without credentials.

### Possible next steps
- add broader benchmark ETFs or more sector ETFs for context;
- extend holdings analysis to historical snapshot comparison;
- add more beginner-oriented explanation of ETF concepts and diversification;
- introduce additional portfolio-style metrics such as Sharpe ratio or downside deviation;
- deploy a polished public version with permanent product and demo links.

---

## 9. Submission note
This repository is structured so that a marker can:
- run the app locally from the root folder;
- inspect the notebook workflow from data access to final output;
- trace how processed files are used by the product;
- understand the problem, methods, findings, and reproduction steps from this README.

The project is intended for **educational sector comparison and historical analysis**, not investment advice.
