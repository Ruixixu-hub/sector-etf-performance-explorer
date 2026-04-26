import json
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from html import escape
from pathlib import Path
from textwrap import dedent

# ---------------------------------
# 1. App setup and data loading
# ---------------------------------
st.set_page_config(
    page_title="Sector ETF Performance Explorer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Store the coursework data sources in one place so the top of the file is
# easy to explain and update.
DATA_DIR = Path("data/processed")
PRICES_FILE = DATA_DIR / "etf_prices_metrics_ready.csv"
SUMMARY_FILE = DATA_DIR / "etf_metrics_summary.csv"
HOLDINGS_FILE = DATA_DIR / "holdings_top10.csv"
REP_STOCK_DIR = DATA_DIR / "representative_stock"
REP_MAPPING_FILE = REP_STOCK_DIR / "representative_stock_mapping.csv"
REP_STOCK_CLEAN_FILE = REP_STOCK_DIR / "representative_stocks_clean.csv"
REP_STOCK_METRICS_READY_FILE = REP_STOCK_DIR / "representative_stocks_metrics_ready.csv"
REP_STOCK_SUMMARY_FILE = REP_STOCK_DIR / "representative_stocks_summary.csv"

# Keep the ETF universe, display labels, and color system fixed across the app.
ETF_ORDER = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLP"]

SECTOR_MAP = {
    "XLK": "Technology",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
}

DISPLAY_NAME_MAP = {
    k: f"{k} ({v})" for k, v in SECTOR_MAP.items()
}

COLOR_MAP = {
    "XLK": "#FF7F0E",
    "XLE": "#2C7FB8",
    "XLF": "#2CA02C",
    "XLV": "#9467BD",
    "XLI": "#B85C4B",
    "XLP": "#A49A52",
}

REPRESENTATIVE_STOCK_COMPARISON_COLOR_MAP = {
    "Light": "#7A8598",
    "Dark": "#D2DAE6",
}


# Load the ETF price, summary, and holdings files used throughout the app.
@st.cache_data
def load_data():
    prices = pd.read_csv(PRICES_FILE)
    summary = pd.read_csv(SUMMARY_FILE)
    holdings = pd.read_csv(HOLDINGS_FILE)

    prices["Date"] = pd.to_datetime(prices["Date"], errors="coerce")

    if "Holdings_As_Of" in holdings.columns:
        holdings["Holdings_As_Of"] = pd.to_datetime(holdings["Holdings_As_Of"], errors="coerce")

    return prices, summary, holdings


# Load representative-stock files and standardize the processed column names
# expected by the drill-down section.
@st.cache_data
def load_representative_stock_data():
    mapping = pd.read_csv(REP_MAPPING_FILE)
    stock_clean = pd.read_csv(REP_STOCK_CLEAN_FILE)
    stock_metrics_ready = pd.read_csv(REP_STOCK_METRICS_READY_FILE)
    stock_summary = pd.read_csv(REP_STOCK_SUMMARY_FILE)

    for df in [mapping, stock_clean, stock_metrics_ready, stock_summary]:
        if "Representative_Company_Name" in df.columns and "Representative_Company" not in df.columns:
            df["Representative_Company"] = df["Representative_Company_Name"]

    stock_clean["Date"] = pd.to_datetime(stock_clean["Date"], errors="coerce")

    if "Date" in stock_metrics_ready.columns:
        stock_metrics_ready["Date"] = pd.to_datetime(stock_metrics_ready["Date"], errors="coerce")

    for col in ["Start_Date", "End_Date"]:
        if col in stock_summary.columns:
            stock_summary[col] = pd.to_datetime(stock_summary[col], errors="coerce")

    return mapping, stock_clean, stock_metrics_ready, stock_summary


prices_df, summary_df, holdings_df = load_data()
representative_mapping_df, representative_stock_clean_df, _, _ = load_representative_stock_data()

# ---------------------------------
# 2. Theme and UI system
# ---------------------------------
# Define the full light and dark theme tokens shared across Streamlit widgets,
# Plotly charts, and custom HTML components.
def get_theme(mode_name: str):
    if mode_name == "Dark":
        return {
            "mode_name": "Dark",
            "page_bg": "#051223",
            "sidebar_bg": "#0B1B34",
            "card_bg": "#08162D",
            "card_soft": "#0C1E3A",
            "card_soft_2": "#0A1830",
            "border": "#233652",
            "text": "#F8FAFC",
            "muted": "#CBD5E1",
            "subtle": "#9CAFCB",
            "hero_start": "#08101F",
            "hero_end": "#1D4ED8",
            "hero_glow": "rgba(96, 165, 250, 0.22)",
            "hero_text": "#FFFFFF",
            "hero_secondary_text": "rgba(255, 255, 255, 0.92)",
            "hero_border": "rgba(96, 165, 250, 0.16)",
            "positive": "#4ADE80",
            "negative": "#F87171",
            "positive_bg": "rgba(74, 222, 128, 0.16)",
            "negative_bg": "rgba(248, 113, 113, 0.16)",
            "input_bg": "#0A1324",
            "tag_bg": "#FF5A52",
            "tag_text": "#FFFFFF",
            "plot_bg": "#061427",
            "plot_paper": "#061427",
            "grid": "rgba(255,255,255,0.10)",
            "plot_template": "plotly_dark",
            "shadow": "0 8px 24px rgba(0,0,0,0.25)",
            "header_bg": "rgba(5, 18, 35, 0.72)",
            "modebar_bg": "rgba(8, 22, 45, 0.88)",
            "modebar_icon": "#CBD5E1",
            "modebar_active": "#FFFFFF",
            "hover_bg": "#08162D",
            "calendar_selected_bg": "#1D4ED8",
            "calendar_selected_text": "#FFFFFF",
            "expander_bg": "rgba(12, 30, 58, 0.62)",
            "range_slider_bg": "rgba(148, 163, 184, 0.22)",
            "range_slider_border": "rgba(203, 213, 225, 0.35)"
        }
    else:
        return {
            "mode_name": "Light",
            "page_bg": "#FFFFFF",
            "sidebar_bg": "#F5F7FB",
            "card_bg": "#FFFFFF",
            "card_soft": "#FFFFFF",
            "card_soft_2": "#F8FAFC",
            "border": "#E5E7EB",
            "text": "#1F2937",
            "muted": "#4B5563",
            "subtle": "#6B7280",
            "hero_start": "#FFFFFF",
            "hero_end": "#EAF2FF",
            "hero_glow": "rgba(59, 130, 246, 0.18)",
            "hero_text": "#182B52",
            "hero_secondary_text": "#3B4C6B",
            "hero_border": "rgba(191, 219, 254, 0.92)",
            "positive": "#15803D",
            "negative": "#C2410C",
            "positive_bg": "rgba(21, 128, 61, 0.10)",
            "negative_bg": "rgba(194, 65, 12, 0.10)",
            "input_bg": "#FFFFFF",
            "tag_bg": "#FF5A52",
            "tag_text": "#FFFFFF",
            "plot_bg": "#FFFFFF",
            "plot_paper": "#FFFFFF",
            "grid": "rgba(0,0,0,0.08)",
            "plot_template": "plotly_white",
            "shadow": "0 6px 18px rgba(15,23,42,0.06)",
            "header_bg": "rgba(255, 255, 255, 0.72)",
            "modebar_bg": "rgba(255, 255, 255, 0.92)",
            "modebar_icon": "#6B7280",
            "modebar_active": "#111827",
            "hover_bg": "#FFFFFF",
            "calendar_selected_bg": "#1E3A8A",
            "calendar_selected_text": "#FFFFFF",
            "expander_bg": "rgba(255, 255, 255, 0.78)",
            "range_slider_bg": "#F3F4F6",
            "range_slider_border": "#D1D5DB"
        }


# Match the Plotly range-selector controls to the active light or dark theme.
def get_time_series_range_selector_style(theme: dict):
    if theme["mode_name"] == "Dark":
        return {
            "bg": "#102742",
            "active": "#1D4ED8",
            "font": "#F8FAFC",
            "border": "#35537E",
        }
    return {
        "bg": "#F3F4F6",
        "active": "#DBEAFE",
        "font": "#1F2937",
        "border": "#D1D5DB",
    }


# Keep this hook available without changing current behavior.
def stabilize_streamlit_ui():
    return


# Hide the extra date-range footer so the control area stays visually clean.
def hide_calendar_quick_range_footer():
    components.html(
        """
        <script>
        (() => {
          try {
            const parentWindow = window.parent;
            const doc = parentWindow.document;

            const hideFooter = () => {
              const popovers = doc.querySelectorAll('div[data-baseweb="popover"]');
              popovers.forEach((popover) => {
                const nodes = Array.from(popover.querySelectorAll("*"));
                const labelNode = nodes.find((node) => node.children.length === 0 && node.textContent.trim() === "Choose a date range");
                if (!labelNode) return;

                let footerBlock = labelNode.parentElement;
                while (footerBlock && footerBlock !== popover) {
                  const hasNoneValue = Array.from(footerBlock.querySelectorAll("*")).some(
                    (child) => child !== labelNode && child.textContent.trim() === "None"
                  );
                  if (hasNoneValue) {
                    footerBlock.style.display = "none";
                    return;
                  }
                  footerBlock = footerBlock.parentElement;
                }
              });
            };

            if (parentWindow.__etfDateRangeFooterObserver) {
              parentWindow.__etfDateRangeFooterObserver.disconnect();
            }

            const observer = new MutationObserver(() => hideFooter());
            observer.observe(doc.body, { childList: true, subtree: true });

            parentWindow.__etfDateRangeFooterObserver = observer;
            parentWindow.__etfHideDateRangeFooter = hideFooter;
            hideFooter();
          } catch (error) {
            // Keep the app stable if the parent DOM is unavailable.
          }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


# Inject the app-wide CSS so Streamlit widgets and custom components follow
# one consistent visual system.
def inject_css(theme):
    st.markdown(
        f"""
        <style>
        /* ===== Keep a subtle header, but remove the right menu ===== */
        header[data-testid="stHeader"] {{
            background: {theme["header_bg"]} !important;
            backdrop-filter: blur(8px);
            border-bottom: 1px solid {theme["border"]};
        }}

        div[data-testid="stToolbar"],
        div[data-testid="stStatusWidget"],
        div[data-testid="stAppDeployButton"] {{
            display: none !important;
        }}

        div[data-testid="stDecoration"] {{
            display: none !important;
        }}

        div[data-testid="collapsedControl"] {{
            display: none !important;
        }}

        div[data-testid="collapsedControl"] button {{
            display: none !important;
        }}

        #app-sidebar-toggle {{
            display: none !important;
        }}

        #app-sidebar-toggle:hover {{
            display: none !important;
        }}

        #app-sidebar-toggle svg {{
            display: none !important;
        }}

        .stApp {{
            background: {theme["page_bg"]} !important;
            color: {theme["text"]} !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: {theme["page_bg"]} !important;
        }}

        [data-testid="stSidebar"] {{
            display: none !important;
        }}

        .block-container {{
            padding-top: 4.0rem;
            padding-bottom: 2rem;
            max-width: 1280px;
        }}

        div[data-testid="stHorizontalBlock"] > div:has(> div > .stRadio),
        div[data-testid="stHorizontalBlock"] > div:has(> div > .stMultiSelect),
        div[data-testid="stHorizontalBlock"] > div:has(> div > .stDateInput) {{
            background: {theme["card_bg"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            padding: 1rem 1rem 0.55rem 1rem;
            box-shadow: {theme["shadow"]};
            height: 100%;
        }}

        .hero-card {{
            background:
                radial-gradient(circle at top right, {theme["hero_glow"]} 0%, transparent 36%),
                linear-gradient(135deg, {theme["hero_start"]} 0%, {theme["hero_end"]} 100%);
            padding: 2.5rem 2.6rem;
            border-radius: 24px;
            color: {theme["hero_text"]} !important;
            margin-bottom: 1.15rem;
            box-shadow: {theme["shadow"]};
            border: 1px solid {theme["hero_border"]};
            overflow: hidden;
            position: relative;
        }}

        .hero-card * {{
            color: inherit !important;
        }}

        .hero-card h1 {{
            margin: 0;
            font-size: 3.2rem;
            line-height: 1.08;
            letter-spacing: -0.03em;
        }}

        .hero-card p {{
            margin-top: 0.8rem;
            margin-bottom: 0;
            font-size: 1.08rem;
            color: {theme["hero_secondary_text"]} !important;
            opacity: 1;
        }}

        .section-note {{
            color: {theme["muted"]} !important;
            font-size: 0.98rem;
            margin-top: -0.1rem;
            margin-bottom: 0.9rem;
        }}

        .small-caption {{
            color: {theme["subtle"]} !important;
            font-size: 0.93rem;
            margin-top: -0.15rem;
            margin-bottom: 0.45rem;
        }}

        div[data-testid="stExpander"] {{
            background: {theme["expander_bg"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            box-shadow: {theme["shadow"]};
            overflow: hidden;
        }}

        div[data-testid="stExpander"] details {{
            background: transparent !important;
        }}

        div[data-testid="stExpander"] summary {{
            background: transparent !important;
        }}

        .chart-title {{
            color: {theme["text"]} !important;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
            margin-top: 0.15rem;
            margin-bottom: 0.9rem;
        }}

        .overview-card {{
            background: {theme["card_bg"]};
            border: none;
            border-radius: 18px;
            padding: 1.1rem 1.1rem 1rem 1.1rem;
            min-height: 145px;
            box-shadow: {theme["shadow"]};
        }}

        .overview-label {{
            font-size: 0.96rem;
            color: {theme["muted"]};
            margin-bottom: 0.5rem;
        }}

        .overview-ticker {{
            font-size: 2.25rem;
            font-weight: 700;
            line-height: 1.05;
            color: {theme["text"]};
        }}

        .overview-sector {{
            font-size: 0.98rem;
            color: {theme["subtle"]};
            margin-top: 0.12rem;
        }}

        .drilldown-meta-card,
        .drilldown-summary-card {{
            background: {theme["card_bg"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            box-shadow: {theme["shadow"]};
        }}

        .drilldown-meta-card {{
            padding: 1rem 1.1rem;
            margin-bottom: 0.95rem;
        }}

        .drilldown-meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.95rem;
        }}

        .drilldown-meta-item {{
            min-width: 0;
        }}

        .drilldown-meta-label {{
            display: block;
            margin-bottom: 0.22rem;
            color: {theme["subtle"]};
            font-size: 0.77rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .drilldown-meta-value {{
            color: {theme["text"]};
            font-size: 0.99rem;
            font-weight: 600;
            line-height: 1.42;
        }}

        .drilldown-summary-card {{
            overflow: hidden;
            margin-top: 0.35rem;
        }}

        .drilldown-summary-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .drilldown-summary-table th,
        .drilldown-summary-table td {{
            padding: 0.95rem 1rem;
            border-bottom: 1px solid {theme["border"]};
            text-align: left;
            background: {theme["card_bg"]};
            color: {theme["text"]};
            font-size: 0.98rem;
        }}

        .drilldown-summary-table thead th {{
            background: {theme["card_soft_2"]};
            color: {theme["muted"]};
            font-weight: 700;
        }}

        .drilldown-summary-table tbody tr:last-child td {{
            border-bottom: none;
        }}

        .drilldown-summary-table td.metric-name {{
            color: {theme["text"]};
            font-weight: 700;
        }}

        .drilldown-interpretation {{
            color: {theme["text"]};
            font-size: 1.08rem;
            line-height: 1.82;
            font-weight: 500;
            margin: 0;
        }}

        .drilldown-interpretation-card {{
            background: {theme["card_soft_2"]};
            border: 1px solid {theme["border"]};
            border-radius: 18px;
            box-shadow: {theme["shadow"]};
            padding: 1rem 1.1rem;
            margin-top: 0.9rem;
        }}

        .insight-note-card {{
            background: {theme["card_soft_2"]};
            border: 1px solid {theme["border"]};
            border-radius: 16px;
            box-shadow: {theme["shadow"]};
            padding: 0.9rem 1rem;
            margin-top: 0.85rem;
        }}

        .insight-note-text {{
            color: {theme["text"]};
            font-size: 0.98rem;
            line-height: 1.68;
            margin: 0;
        }}

        .drilldown-interpretation-title {{
            display: block;
            color: {theme["text"]};
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }}

        @media (max-width: 900px) {{
            .drilldown-meta-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        .pill-positive {{
            display: inline-block;
            margin-top: 0.9rem;
            padding: 0.34rem 0.72rem;
            border-radius: 999px;
            background: {theme["positive_bg"]};
            color: {theme["positive"]};
            font-size: 0.95rem;
            font-weight: 700;
        }}

        .pill-negative {{
            display: inline-block;
            margin-top: 0.9rem;
            padding: 0.34rem 0.72rem;
            border-radius: 999px;
            background: {theme["negative_bg"]};
            color: {theme["negative"]};
            font-size: 0.95rem;
            font-weight: 700;
        }}

        div[data-baseweb="select"] > div {{
            background: {theme["input_bg"]} !important;
            border: 1px solid {theme["border"]} !important;
            color: {theme["text"]} !important;
            box-shadow: none !important;
        }}

        div[data-baseweb="select"] input {{
            color: {theme["text"]} !important;
        }}

        .stSelectbox label,
        .stMultiSelect label,
        .stDateInput label,
        .stRadio label,
        .stSelectbox [data-testid="stWidgetLabel"] p,
        .stMultiSelect [data-testid="stWidgetLabel"] p,
        .stDateInput [data-testid="stWidgetLabel"] p,
        .stRadio [data-testid="stWidgetLabel"] p {{
            color: {theme["muted"]} !important;
            opacity: 1 !important;
        }}

        .stRadio [role="radiogroup"] label,
        .stRadio [role="radiogroup"] label *,
        .stRadio [role="radiogroup"] span,
        .stRadio [role="radiogroup"] p {{
            color: {theme["text"]} !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="select"] span {{
            color: {theme["text"]} !important;
        }}

        div[data-baseweb="select"] svg,
        div[data-baseweb="input"] svg {{
            fill: {theme["text"]} !important;
            color: {theme["text"]} !important;
        }}

        div[data-baseweb="tag"] {{
            background: {theme["tag_bg"]} !important;
            border-radius: 999px !important;
        }}

        div[data-baseweb="tag"] span {{
            color: {theme["tag_text"]} !important;
        }}

        .stDateInput input,
        .stTextInput input,
        .stNumberInput input {{
            background: {theme["input_bg"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
        }}

        div[data-baseweb="input"] > div {{
            background: {theme["input_bg"]} !important;
            border: 1px solid {theme["border"]} !important;
            box-shadow: none !important;
        }}

        div[data-baseweb="input"] > div > button,
        .stDateInput button {{
            background: {theme["input_bg"]} !important;
            color: {theme["text"]} !important;
            border: none !important;
            box-shadow: none !important;
        }}

        div[data-baseweb="input"] input,
        .stDateInput input::placeholder,
        .stTextInput input::placeholder,
        .stNumberInput input::placeholder,
        div[data-baseweb="select"] input::placeholder {{
            color: {theme["subtle"]} !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="popover"] {{
            background: {theme["card_bg"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 18px !important;
            box-shadow: {theme["shadow"]} !important;
            z-index: 10001 !important;
            overflow: visible !important;
        }}

        div[data-baseweb="popover"] * {{
            color: {theme["text"]} !important;
        }}

        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] [role="listbox"],
        div[data-baseweb="popover"] [role="option"] {{
            background: {theme["card_bg"]} !important;
        }}

        div[data-baseweb="popover"] [role="option"]:hover,
        div[data-baseweb="popover"] [aria-selected="true"] {{
            background: {theme["card_soft"]} !important;
        }}

        div[data-baseweb="calendar"] {{
            background: {theme["card_bg"]} !important;
            border-radius: 18px !important;
        }}

        div[data-baseweb="calendar"] > div:first-child,
        div[data-baseweb="calendar"] > div:first-child > div,
        div[data-baseweb="calendar"] > div:first-child > div > div,
        div[data-baseweb="calendar"] > div:first-child > div > div > div {{
            background: {theme["card_soft_2"]} !important;
        }}

        div[data-baseweb="calendar"] button {{
            color: {theme["text"]} !important;
        }}

        div[data-baseweb="calendar"] button:hover {{
            background: {theme["card_soft"]} !important;
        }}

        div[data-baseweb="calendar"] select {{
            background: {theme["input_bg"]} !important;
            color: {theme["text"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 10px !important;
        }}

        div[data-baseweb="calendar"] button[aria-selected="true"],
        div[data-baseweb="calendar"] [aria-selected="true"] {{
            background: {theme["calendar_selected_bg"]} !important;
            color: {theme["calendar_selected_text"]} !important;
            border-radius: 999px !important;
        }}

        div[data-baseweb="calendar"] [aria-disabled="true"] {{
            color: {theme["subtle"]} !important;
        }}

        .js-plotly-plot .plotly .modebar {{
            background: {theme["modebar_bg"]} !important;
            border: 1px solid {theme["border"]} !important;
            border-radius: 12px !important;
            padding: 0.15rem !important;
            opacity: 1 !important;
            visibility: visible !important;
            display: flex !important;
        }}

        .js-plotly-plot .plotly .modebar-btn svg {{
            fill: {theme["modebar_icon"]} !important;
        }}

        .js-plotly-plot .plotly .modebar-btn:hover svg {{
            fill: {theme["modebar_active"]} !important;
        }}

        div.stDownloadButton > button,
        div[data-testid="stDownloadButton"] > button {{
            width: 100%;
            min-height: 3rem;
            padding: 0.75rem 1rem;
            border-radius: 16px;
            border: 1px solid {theme["border"]} !important;
            background: {theme["card_soft_2"]} !important;
            color: {theme["text"]} !important;
            box-shadow: {theme["shadow"]};
            font-weight: 700;
            line-height: 1.35;
            transition: background 140ms ease, border-color 140ms ease, transform 140ms ease;
        }}

        div.stDownloadButton > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {{
            background: {theme["card_soft"]} !important;
            border-color: {theme["modebar_active"]} !important;
            color: {theme["text"]} !important;
            transform: translateY(-1px);
        }}

        div.stDownloadButton > button:focus,
        div.stDownloadButton > button:focus-visible,
        div[data-testid="stDownloadButton"] > button:focus,
        div[data-testid="stDownloadButton"] > button:focus-visible {{
            color: {theme["text"]} !important;
            border-color: {theme["modebar_active"]} !important;
            box-shadow: 0 0 0 0.18rem {theme["hero_glow"]};
            outline: none !important;
        }}

        div.stDownloadButton > button p,
        div[data-testid="stDownloadButton"] > button p {{
            color: {theme["text"]} !important;
        }}

        hr {{
            border-color: {theme["border"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------
# 3. Analytical helpers
# ---------------------------------
# Keep ETF tickers in the coursework order across controls, charts, tables,
# and exported files.
def sort_tickers_by_default_order(tickers: list[str]) -> list[str]:
    unique_tickers = list(dict.fromkeys(str(ticker) for ticker in tickers if pd.notna(ticker)))
    ordered = [ticker for ticker in ETF_ORDER if ticker in unique_tickers]
    remaining = sorted(ticker for ticker in unique_tickers if ticker not in ETF_ORDER)
    return ordered + remaining


# Apply the fixed ETF order to a DataFrame before display or export.
def sort_dataframe_by_etf_order(
    df: pd.DataFrame,
    ticker_col: str = "Ticker",
    secondary_cols: list[str] | None = None,
):
    secondary_cols = secondary_cols or []
    order_lookup = {ticker: idx for idx, ticker in enumerate(ETF_ORDER)}

    return (
        df.assign(_etf_order=df[ticker_col].map(order_lookup).fillna(len(order_lookup)))
        .sort_values(["_etf_order", *secondary_cols])
        .drop(columns="_etf_order")
    )


# Convert tickers into the label format used in legends and tables.
def get_display_name_order(tickers: list[str]) -> list[str]:
    return [DISPLAY_NAME_MAP.get(ticker, ticker) for ticker in sort_tickers_by_default_order(tickers)]


# Build cumulative return, volatility, and drawdown metrics for the currently
# filtered ETF sample.
def build_filtered_metrics(filtered_prices: pd.DataFrame):
    if filtered_prices.empty:
        return pd.DataFrame(), pd.DataFrame()

    df = sort_dataframe_by_etf_order(
        filtered_prices.copy(),
        ticker_col="Ticker",
        secondary_cols=["Date"],
    ).reset_index(drop=True)

    df["Growth_Index_Filtered"] = (
        df.groupby("Ticker")["Return"]
        .transform(lambda s: (1 + s).cumprod())
    )
    df["Cumulative_Return_Filtered"] = df["Growth_Index_Filtered"] - 1
    df["Running_Peak_Filtered"] = (
        df.groupby("Ticker")["Growth_Index_Filtered"]
        .cummax()
    )
    df["Drawdown_Filtered"] = (
        df["Growth_Index_Filtered"] / df["Running_Peak_Filtered"] - 1
    )

    summary = (
        df.groupby("Ticker")
        .agg(
            Start_Date=("Date", "min"),
            End_Date=("Date", "max"),
            Observations=("Date", "count"),
            Final_Cumulative_Return=("Cumulative_Return_Filtered", "last"),
            Annualized_Volatility=("Return", lambda s: s.std(ddof=1) * np.sqrt(252)),
            Max_Drawdown=("Drawdown_Filtered", "min")
        )
        .reset_index()
    )

    summary["Display_Name"] = summary["Ticker"].map(DISPLAY_NAME_MAP)
    summary = sort_dataframe_by_etf_order(summary, ticker_col="Ticker").reset_index(drop=True)
    return df, summary


# Compute rolling annualized volatility for the selected ETFs.
def compute_rolling_volatility(filtered_prices: pd.DataFrame, window_size: int):
    if filtered_prices.empty:
        return pd.DataFrame()

    df = sort_dataframe_by_etf_order(
        filtered_prices[["Ticker", "Date", "Return"]]
        .dropna(subset=["Ticker", "Date", "Return"])
        .copy(),
        ticker_col="Ticker",
        secondary_cols=["Date"],
    )

    df["Rolling_Annualized_Volatility"] = (
        df.groupby("Ticker")["Return"]
        .transform(lambda s: s.rolling(window=window_size, min_periods=window_size).std(ddof=1) * np.sqrt(252))
    )
    df["Display_Name"] = df["Ticker"].map(DISPLAY_NAME_MAP)

    return (
        df.dropna(subset=["Rolling_Annualized_Volatility"])
        .reset_index(drop=True)
    )


# Align ETF return series on dates shared by every selected ETF.
def build_aligned_return_matrix(filtered_prices: pd.DataFrame, tickers: list[str]):
    if len(tickers) < 2 or filtered_prices.empty:
        return pd.DataFrame()

    aligned_returns = (
        filtered_prices[["Date", "Ticker", "Return"]]
        .dropna(subset=["Date", "Ticker", "Return"])
        .drop_duplicates(subset=["Date", "Ticker"], keep="last")
        .pivot(index="Date", columns="Ticker", values="Return")
        .reindex(columns=tickers)
        .dropna(how="any")
        .sort_index()
    )

    return aligned_returns


# Build the aligned ETF return matrix and its correlation table.
def build_correlation_matrix(filtered_prices: pd.DataFrame, tickers: list[str]):
    aligned_returns = build_aligned_return_matrix(filtered_prices, tickers)
    if aligned_returns.shape[0] < 2:
        return aligned_returns, pd.DataFrame()

    correlation_matrix = aligned_returns.corr()
    correlation_matrix = correlation_matrix.reindex(index=tickers, columns=tickers)
    return aligned_returns, correlation_matrix


# Look up the representative-stock metadata for the selected ETF.
def get_representative_stock_metadata(mapping_df: pd.DataFrame, selected_etf: str):
    match = mapping_df[mapping_df["ETF"] == selected_etf].copy()
    if match.empty:
        return None
    return match.iloc[0].to_dict()


# Align ETF and representative-stock returns on common dates so both series are
# compared over the same trading window.
def align_etf_and_stock_on_common_dates(
    etf_prices: pd.DataFrame,
    stock_prices: pd.DataFrame
):
    etf_returns = (
        etf_prices[["Date", "Return"]]
        .dropna(subset=["Date", "Return"])
        .drop_duplicates(subset=["Date"], keep="last")
        .rename(columns={"Return": "ETF_Return"})
        .copy()
    )

    stock_returns = (
        stock_prices[["Date", "Return"]]
        .dropna(subset=["Date", "Return"])
        .drop_duplicates(subset=["Date"], keep="last")
        .rename(columns={"Return": "Stock_Return"})
        .copy()
    )

    return (
        etf_returns
        .merge(stock_returns, on="Date", how="inner")
        .sort_values("Date")
        .reset_index(drop=True)
    )


# Convert daily returns into a rebased cumulative path for charting and
# window-level comparison metrics.
def build_return_based_rebased_series(aligned_df: pd.DataFrame, prefix: str):
    if aligned_df.empty:
        return pd.DataFrame(index=aligned_df.index)

    return_col = f"{prefix}_Return"
    raw_growth = (1 + aligned_df[return_col]).cumprod()

    rebased_growth = raw_growth / raw_growth.iloc[0]
    running_peak = rebased_growth.cummax()

    return pd.DataFrame(
        {
            f"{prefix}_Growth_Index_Rebased": rebased_growth,
            f"{prefix}_Cumulative_Return_Rebased": rebased_growth - 1,
            f"{prefix}_Running_Peak_Rebased": running_peak,
            f"{prefix}_Drawdown_Rebased": rebased_growth / running_peak - 1,
        },
        index=aligned_df.index,
    )


# Create the aligned ETF-versus-stock dataset used in the drill-down chart,
# summary table, and interpretation.
def build_aligned_representative_comparison_data(
    etf_prices: pd.DataFrame,
    stock_prices: pd.DataFrame
):
    aligned = align_etf_and_stock_on_common_dates(etf_prices, stock_prices)
    if aligned.empty:
        return pd.DataFrame()

    etf_path = build_return_based_rebased_series(aligned, "ETF")
    stock_path = build_return_based_rebased_series(aligned, "Stock")

    return pd.concat([aligned, etf_path, stock_path], axis=1)


# Summarize return, volatility, and drawdown for one side of the ETF-versus-
# stock comparison.
def compute_representative_comparison_metrics(comparison_df: pd.DataFrame, prefix: str):
    if comparison_df.empty:
        return {}

    actual_returns = comparison_df[f"{prefix}_Return"].dropna()
    annualized_volatility = (
        actual_returns.std(ddof=1) * np.sqrt(252)
        if len(actual_returns) >= 2 else 0.0
    )

    return {
        "Start_Date": comparison_df["Date"].iloc[0],
        "End_Date": comparison_df["Date"].iloc[-1],
        "Final_Cumulative_Return": float(comparison_df[f"{prefix}_Cumulative_Return_Rebased"].iloc[-1]),
        "Annualized_Volatility": float(annualized_volatility),
        "Max_Drawdown": float(comparison_df[f"{prefix}_Drawdown_Rebased"].min()),
    }

# ---------------------------------
# 4. Chart builders
# ---------------------------------
# Build the main cumulative return chart for the filtered ETF set.
def build_performance_figure(metrics_ready_filtered: pd.DataFrame, theme: dict):
    df = metrics_ready_filtered.copy()
    df["Display_Name"] = df["Ticker"].map(DISPLAY_NAME_MAP)
    display_order = get_display_name_order(df["Ticker"].dropna().unique().tolist())

    if theme["mode_name"] == "Dark":
        rs_bg = "#102742"
        rs_active = "#1D4ED8"
        rs_font = "#F8FAFC"
        rs_border = "#35537E"
    else:
        rs_bg = "#F3F4F6"
        rs_active = "#DBEAFE"
        rs_font = "#1F2937"
        rs_border = "#D1D5DB"

    fig = px.line(
        df,
        x="Date",
        y="Cumulative_Return_Filtered",
        color="Display_Name",
        color_discrete_map={DISPLAY_NAME_MAP[k]: v for k, v in COLOR_MAP.items()},
        category_orders={"Display_Name": display_order},
    )

    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Cumulative Return: %{y:.2%}<extra></extra>",
        line=dict(width=2.45)
    )

    x_min = df["Date"].min()
    x_max = df["Date"].max()

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        hovermode="x unified",
        height=560,
        margin=dict(l=65, r=35, t=30, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            title_text="",
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_yaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[x_min, x_max],
        rangeslider=dict(
            visible=True,
            thickness=0.10,
            bgcolor=theme["range_slider_bg"],
            bordercolor=theme["range_slider_border"],
            borderwidth=1
        ),
        rangeselector=dict(
            x=0.02,
            y=1.12,
            bgcolor=rs_bg,
            activecolor=rs_active,
            bordercolor=rs_border,
            borderwidth=1,
            font=dict(color=rs_font),
            buttons=[
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]
        )
    )

    return fig


# Build the optional absolute price reference chart.
def build_absolute_price_figure(filtered_prices: pd.DataFrame, theme: dict):
    df = filtered_prices.copy()
    df["Display_Name"] = df["Ticker"].map(DISPLAY_NAME_MAP)
    display_order = get_display_name_order(df["Ticker"].dropna().unique().tolist())
    range_style = get_time_series_range_selector_style(theme)

    fig = px.line(
        df,
        x="Date",
        y="Price",
        color="Display_Name",
        color_discrete_map={DISPLAY_NAME_MAP[k]: v for k, v in COLOR_MAP.items()},
        category_orders={"Display_Name": display_order},
    )

    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Price: $%{y:,.2f}<extra></extra>",
        line=dict(width=2.35)
    )

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
        height=470,
        margin=dict(l=65, r=35, t=30, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            title_text="",
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        tickprefix="$"
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[df["Date"].min(), df["Date"].max()],
        rangeslider=dict(
            visible=True,
            thickness=0.10,
            bgcolor=theme["range_slider_bg"],
            bordercolor=theme["range_slider_border"],
            borderwidth=1
        ),
        rangeselector=dict(
            x=0.02,
            y=1.12,
            bgcolor=range_style["bg"],
            activecolor=range_style["active"],
            bordercolor=range_style["border"],
            borderwidth=1,
            font=dict(color=range_style["font"]),
            buttons=[
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]
        )
    )

    return fig


# Build the paired bar charts for volatility and drawdown.
def build_risk_snapshot_figure(filtered_summary: pd.DataFrame, theme: dict):
    risk_df = filtered_summary.copy()

    vol_df = risk_df.sort_values("Annualized_Volatility", ascending=True).reset_index(drop=True)
    vol_df["Display_Name"] = vol_df["Ticker"].map(DISPLAY_NAME_MAP)

    dd_df = risk_df.copy()
    dd_df["Drawdown_Depth"] = dd_df["Max_Drawdown"].abs()
    dd_df = dd_df.sort_values("Drawdown_Depth", ascending=True).reset_index(drop=True)
    dd_df["Display_Name"] = dd_df["Ticker"].map(DISPLAY_NAME_MAP)

    max_vol = float(vol_df["Annualized_Volatility"].max()) if not vol_df.empty else 0
    max_dd = float(dd_df["Drawdown_Depth"].max()) if not dd_df.empty else 0

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Annualized Volatility", "Maximum Drawdown Depth"),
        horizontal_spacing=0.16
    )

    fig.add_trace(
        go.Bar(
            x=vol_df["Annualized_Volatility"],
            y=vol_df["Display_Name"],
            orientation="h",
            text=[f"{x:.1%}" for x in vol_df["Annualized_Volatility"]],
            textposition="outside",
            cliponaxis=False,
            marker=dict(
                color=[COLOR_MAP[t] for t in vol_df["Ticker"]],
                line=dict(color=theme["text"], width=0.7)
            ),
            hovertemplate="<b>%{y}</b><br>Annualized Volatility: %{x:.2%}<extra></extra>",
            showlegend=False
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(
            x=dd_df["Drawdown_Depth"],
            y=dd_df["Display_Name"],
            orientation="h",
            text=[f"{x:.1%}" for x in dd_df["Drawdown_Depth"]],
            textposition="outside",
            cliponaxis=False,
            marker=dict(
                color=[COLOR_MAP[t] for t in dd_df["Ticker"]],
                line=dict(color=theme["text"], width=0.7)
            ),
            hovertemplate="<b>%{y}</b><br>Maximum Drawdown Depth: %{x:.2%}<extra></extra>",
            showlegend=False
        ),
        row=1, col=2
    )

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        height=470,
        margin=dict(l=90, r=95, t=55, b=25),
        bargap=0.42,
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_xaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        range=[0, max_vol * 1.22 if max_vol > 0 else 1],
        automargin=True,
        row=1, col=1
    )

    fig.update_xaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        range=[0, max_dd * 1.22 if max_dd > 0 else 1],
        automargin=True,
        row=1, col=2
    )

    fig.update_yaxes(title_text="", automargin=True, row=1, col=1)
    fig.update_yaxes(title_text="", automargin=True, row=1, col=2)

    return fig


# Build the rolling volatility line chart for the chosen window length.
def build_rolling_volatility_figure(rolling_volatility_df: pd.DataFrame, theme: dict, window_label: str):
    df = rolling_volatility_df.copy()
    display_order = get_display_name_order(df["Ticker"].dropna().unique().tolist())
    range_style = get_time_series_range_selector_style(theme)

    fig = px.line(
        df,
        x="Date",
        y="Rolling_Annualized_Volatility",
        color="Display_Name",
        color_discrete_map={DISPLAY_NAME_MAP[k]: v for k, v in COLOR_MAP.items()},
        category_orders={"Display_Name": display_order},
    )

    fig.update_traces(
        hovertemplate=f"<b>%{{fullData.name}}</b><br>Date: %{{x|%Y-%m-%d}}<br>{window_label} Rolling Volatility: %{{y:.2%}}<extra></extra>",
        line=dict(width=2.3)
    )

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Date",
        yaxis_title="Annualized Volatility",
        hovermode="x unified",
        height=470,
        margin=dict(l=65, r=35, t=30, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            title_text="",
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_yaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[df["Date"].min(), df["Date"].max()],
        rangeslider=dict(
            visible=True,
            thickness=0.10,
            bgcolor=theme["range_slider_bg"],
            bordercolor=theme["range_slider_border"],
            borderwidth=1
        ),
        rangeselector=dict(
            x=0.02,
            y=1.12,
            bgcolor=range_style["bg"],
            activecolor=range_style["active"],
            bordercolor=range_style["border"],
            borderwidth=1,
            font=dict(color=range_style["font"]),
            buttons=[
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]
        )
    )

    return fig


# Build the risk-return scatter used to compare summary outcomes across ETFs.
def build_risk_return_scatter_figure(filtered_summary: pd.DataFrame, theme: dict):
    scatter_df = filtered_summary.copy()
    scatter_df["Sector"] = scatter_df["Ticker"].map(SECTOR_MAP)
    median_volatility = scatter_df["Annualized_Volatility"].median()
    median_return = scatter_df["Final_Cumulative_Return"].median()

    def get_text_position(row):
        if row["Annualized_Volatility"] >= median_volatility and row["Final_Cumulative_Return"] >= median_return:
            return "top right"
        if row["Annualized_Volatility"] < median_volatility and row["Final_Cumulative_Return"] >= median_return:
            return "top left"
        if row["Annualized_Volatility"] >= median_volatility and row["Final_Cumulative_Return"] < median_return:
            return "bottom right"
        return "bottom left"

    scatter_df["Text_Position"] = scatter_df.apply(get_text_position, axis=1)
    hover_text = scatter_df.apply(
        lambda row: (
            f"<b>{row['Ticker']}</b><br>"
            f"Sector: {row['Sector']}<br>"
            f"Cumulative Return: {row['Final_Cumulative_Return']:.2%}<br>"
            f"Annualized Volatility: {row['Annualized_Volatility']:.2%}<br>"
            f"Maximum Drawdown: {row['Max_Drawdown']:.2%}"
        ),
        axis=1,
    )

    fig = go.Figure(
        data=[
            go.Scatter(
                x=scatter_df["Annualized_Volatility"],
                y=scatter_df["Final_Cumulative_Return"],
                mode="markers+text",
                text=scatter_df["Ticker"],
                textposition=scatter_df["Text_Position"],
                textfont=dict(size=13, color=theme["text"]),
                hovertext=hover_text,
                hovertemplate="%{hovertext}<extra></extra>",
                marker=dict(
                    size=24,
                    opacity=0.95,
                    color=[COLOR_MAP[ticker] for ticker in scatter_df["Ticker"]],
                    line=dict(color=theme["border"], width=2.1)
                ),
                cliponaxis=False,
                showlegend=False,
            )
        ]
    )

    min_volatility = float(scatter_df["Annualized_Volatility"].min())
    max_volatility = float(scatter_df["Annualized_Volatility"].max())
    min_return = float(scatter_df["Final_Cumulative_Return"].min())
    max_return = float(scatter_df["Final_Cumulative_Return"].max())
    volatility_span = max_volatility - min_volatility
    return_span = max_return - min_return
    volatility_padding = max(volatility_span * 0.14, 0.012)
    return_padding = max(return_span * 0.16, 0.03)

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Annualized Volatility",
        yaxis_title="Cumulative Return",
        height=470,
        margin=dict(l=68, r=20, t=25, b=45),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        ),
        shapes=[
            dict(
                type="line",
                x0=median_volatility,
                x1=median_volatility,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color=theme["border"], width=1, dash="dot")
            ),
            dict(
                type="line",
                x0=0,
                x1=1,
                y0=median_return,
                y1=median_return,
                xref="paper",
                yref="y",
                line=dict(color=theme["border"], width=1, dash="dot")
            ),
        ] if len(scatter_df) >= 2 else []
    )

    fig.update_xaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[max(0, min_volatility - volatility_padding), max_volatility + volatility_padding]
    )
    fig.update_yaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[min_return - return_padding, max_return + return_padding]
    )

    return fig


# Build the ETF correlation heatmap used for diversification discussion.
def build_correlation_heatmap_figure(correlation_matrix: pd.DataFrame, theme: dict):
    x_labels = [DISPLAY_NAME_MAP.get(ticker, ticker) for ticker in correlation_matrix.columns]
    y_labels = [DISPLAY_NAME_MAP.get(ticker, ticker) for ticker in correlation_matrix.index]

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=correlation_matrix.values,
                x=x_labels,
                y=y_labels,
                zmin=-1,
                zmax=1,
                zmid=0,
                colorscale=[
                    [0.0, "#B91C1C"],
                    [0.5, theme["card_soft_2"]],
                    [1.0, "#1D4ED8"],
                ],
                xgap=3,
                ygap=3,
                colorbar=dict(title="Correlation"),
                hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Correlation: %{z:.2f}<extra></extra>",
            )
        ]
    )

    for row_idx, row_label in enumerate(y_labels):
        for col_idx, col_label in enumerate(x_labels):
            cell_value = correlation_matrix.iloc[row_idx, col_idx]
            text_color = "#F8FAFC" if abs(cell_value) >= 0.55 else theme["text"]
            fig.add_annotation(
                x=col_label,
                y=row_label,
                text=f"{cell_value:.2f}",
                showarrow=False,
                font=dict(color=text_color, size=12, family="sans-serif")
            )

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        height=500,
        margin=dict(l=90, r=30, t=25, b=40),
    )

    fig.update_xaxes(side="bottom", automargin=True)
    fig.update_yaxes(automargin=True)

    return fig


# Build the top-holdings bar chart for the selected ETF.
def build_holdings_figure(selected_holdings: pd.DataFrame, holdings_etf: str, theme: dict):
    chart_df = selected_holdings.sort_values("Weight", ascending=True).copy()
    chart_df["Weight_Label"] = chart_df["Weight"].map(lambda x: f"{x:.1f}%")

    fig = px.bar(
        chart_df,
        x="Weight",
        y="Holding_Ticker",
        orientation="h",
        text="Weight_Label",
        color_discrete_sequence=[COLOR_MAP[holdings_etf]],
        title=f"Top 10 Holdings of {DISPLAY_NAME_MAP[holdings_etf]}"
    )

    fig.update_traces(textposition="outside", cliponaxis=False)

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Portfolio Weight (%)",
        yaxis_title="Holding Ticker",
        showlegend=False,
        height=470,
        margin=dict(l=60, r=70, t=70, b=35),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_xaxes(showgrid=True, gridcolor=theme["grid"], automargin=True)
    fig.update_yaxes(showgrid=False, automargin=True)

    return fig


# Build the ETF-versus-representative-stock cumulative return comparison chart.
def build_representative_comparison_figure(
    comparison_df: pd.DataFrame,
    selected_etf: str,
    stock_metadata: dict,
    theme: dict
):
    stock_ticker = stock_metadata["Representative_Stock_Ticker"]
    stock_label = f"{stock_ticker} ({stock_metadata['Representative_Company']})"
    combined_dates = comparison_df["Date"]
    stock_line_color = REPRESENTATIVE_STOCK_COMPARISON_COLOR_MAP.get(
        theme["mode_name"],
        REPRESENTATIVE_STOCK_COMPARISON_COLOR_MAP["Light"],
    )

    if theme["mode_name"] == "Dark":
        rs_bg = "#102742"
        rs_active = "#1D4ED8"
        rs_font = "#F8FAFC"
        rs_border = "#35537E"
    else:
        rs_bg = "#F3F4F6"
        rs_active = "#DBEAFE"
        rs_font = "#1F2937"
        rs_border = "#D1D5DB"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=comparison_df["Date"],
            y=comparison_df["ETF_Cumulative_Return_Rebased"],
            mode="lines",
            name=DISPLAY_NAME_MAP[selected_etf],
            line=dict(color=COLOR_MAP[selected_etf], width=2.8),
            hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Cumulative Return: %{y:.2%}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=comparison_df["Date"],
            y=comparison_df["Stock_Cumulative_Return_Rebased"],
            mode="lines",
            name=stock_label,
            line=dict(
                color=stock_line_color,
                width=2.8,
                dash="dash"
            ),
            hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%Y-%m-%d}<br>Cumulative Return: %{y:.2%}<extra></extra>",
        )
    )

    fig.update_layout(
        template=theme["plot_template"],
        paper_bgcolor=theme["plot_paper"],
        plot_bgcolor=theme["plot_bg"],
        font=dict(color=theme["text"]),
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        hovermode="x unified",
        height=470,
        margin=dict(l=65, r=35, t=30, b=45),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="left",
            x=0.0,
            title_text="Comparison",
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["border"],
            font=dict(color=theme["text"])
        )
    )

    fig.update_yaxes(
        tickformat=".0%",
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        automargin=True,
        range=[combined_dates.min(), combined_dates.max()],
        rangeslider=dict(
            visible=True,
            thickness=0.10,
            bgcolor=theme["range_slider_bg"],
            bordercolor=theme["range_slider_border"],
            borderwidth=1
        ),
        rangeselector=dict(
            x=0.02,
            y=1.12,
            bgcolor=rs_bg,
            activecolor=rs_active,
            bordercolor=rs_border,
            borderwidth=1,
            font=dict(color=rs_font),
            buttons=[
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]
        )
    )

    return fig

# ---------------------------------
# 5. HTML / text / export helpers
# ---------------------------------
# Render one quick-overview card with consistent styling.
def overview_card(label, ticker, sector, value_text, value_positive=True):
    pill_class = "pill-positive" if value_positive else "pill-negative"
    arrow = "↑" if value_positive else "↓"

    st.markdown(
        f"""
        <div class="overview-card">
            <div class="overview-label">{label}</div>
            <div class="overview-ticker">{ticker}</div>
            <div class="overview-sector">{sector}</div>
            <div class="{pill_class}">{arrow} {value_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# Render the holdings table as a custom HTML component with search,
# fullscreen, and CSV download support.
def render_holdings_table_component(table_df: pd.DataFrame, theme: dict):
    rows_html = "".join(
        """
        <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>
        """.format(
            escape(str(row["Holding Name"])),
            escape(str(row["Ticker"])),
            escape(str(row["Portfolio Weight"]))
        )
        for _, row in table_df.iterrows()
    )

    csv_payload = json.dumps(table_df.to_csv(index=False))
    table_height = min(max(180 + 56 * len(table_df), 360), 760)

    table_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        :root {{
          color-scheme: {"dark" if theme["mode_name"] == "Dark" else "light"};
          --card-bg: {theme["card_bg"]};
          --card-soft: {theme["card_soft_2"]};
          --border: {theme["border"]};
          --text: {theme["text"]};
          --muted: {theme["muted"]};
          --page-bg: {theme["page_bg"]};
          --shadow: {theme["shadow"]};
          --toolbar-bg: {theme["modebar_bg"]};
          --toolbar-active: {theme["modebar_active"]};
        }}

        * {{
          box-sizing: border-box;
        }}

        html, body {{
          background: var(--page-bg);
        }}

        body {{
          margin: 0;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--text);
        }}

        .holdings-shell {{
          position: relative;
          padding-top: 0.9rem;
          background: var(--page-bg);
        }}

        .holdings-toolbar {{
          position: absolute;
          top: 0;
          right: 0;
          display: flex;
          align-items: center;
          gap: 0.6rem;
          z-index: 5;
        }}

        .search-wrap {{
          width: 0;
          opacity: 0;
          overflow: hidden;
          transition: width 140ms ease, opacity 140ms ease;
        }}

        .search-wrap.active {{
          width: 180px;
          opacity: 1;
        }}

        .search-input {{
          width: 100%;
          height: 2.55rem;
          border-radius: 999px;
          border: 1px solid var(--border);
          background: var(--card-bg);
          color: var(--text);
          padding: 0 0.9rem;
          outline: none;
          font-size: 0.95rem;
          box-shadow: var(--shadow);
        }}

        .toolbar-group {{
          display: flex;
          align-items: center;
          gap: 0.2rem;
          padding: 0.25rem;
          border-radius: 16px;
          background: var(--toolbar-bg);
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
        }}

        .tool-btn {{
          width: 2.3rem;
          height: 2.3rem;
          border: none;
          border-radius: 12px;
          background: transparent;
          color: var(--muted);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }}

        .tool-btn:hover {{
          color: var(--toolbar-active);
          background: rgba(148, 163, 184, 0.12);
        }}

        .tool-btn svg {{
          width: 1.15rem;
          height: 1.15rem;
          stroke: currentColor;
        }}

        .table-card {{
          background: var(--card-bg);
          border: 1px solid var(--border);
          border-radius: 22px;
          overflow: hidden;
          box-shadow: var(--shadow);
        }}

        .table-scroll {{
          overflow-x: auto;
        }}

        table {{
          width: 100%;
          border-collapse: collapse;
          table-layout: fixed;
        }}

        th, td {{
          border: 1px solid var(--border);
          padding: 1.2rem 1.35rem;
          text-align: left;
          font-size: 1rem;
          line-height: 1.35;
          background: var(--card-bg);
        }}

        th {{
          background: var(--card-soft);
          color: var(--muted);
          font-weight: 600;
        }}

        th:nth-child(1), td:nth-child(1) {{
          width: 52%;
        }}

        th:nth-child(2), td:nth-child(2) {{
          width: 18%;
        }}

        th:nth-child(3), td:nth-child(3) {{
          width: 30%;
        }}

        tbody tr.hidden {{
          display: none;
        }}

        .empty-state {{
          display: none;
          padding: 1.2rem 1.35rem 1.35rem 1.35rem;
          color: var(--muted);
          font-size: 0.96rem;
        }}

        .table-card.show-empty .empty-state {{
          display: block;
        }}

        .table-card.show-empty table {{
          display: none;
        }}

        .holdings-shell:fullscreen {{
          min-height: 100vh;
          padding: 1rem;
          background: var(--page-bg);
        }}

        .holdings-shell:fullscreen .holdings-toolbar {{
          top: 1rem;
          right: 1rem;
          z-index: 12;
        }}

        .holdings-shell:fullscreen .table-card {{
          border-radius: 22px;
        }}

        .holdings-shell:fullscreen .table-scroll {{
          max-height: calc(100vh - 7rem);
          overflow-y: auto;
        }}
      </style>
    </head>
    <body>
      <div class="holdings-shell" id="holdings-shell">
        <div class="holdings-toolbar">
          <div class="search-wrap" id="search-wrap">
            <input id="search-input" class="search-input" type="text" placeholder="Search holdings" />
          </div>
          <div class="toolbar-group">
            <button class="tool-btn" id="download-btn" type="button" title="Download CSV" aria-label="Download CSV">
              <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3v12"></path>
                <path d="m7 10 5 5 5-5"></path>
                <path d="M5 21h14"></path>
              </svg>
            </button>
            <button class="tool-btn" id="search-btn" type="button" title="Search" aria-label="Search">
              <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="m20 20-3.5-3.5"></path>
              </svg>
            </button>
            <button class="tool-btn" id="fullscreen-btn" type="button" title="Fullscreen" aria-label="Fullscreen">
              <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 3H3v5"></path>
                <path d="M16 3h5v5"></path>
                <path d="M21 16v5h-5"></path>
                <path d="M8 21H3v-5"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="table-card" id="table-card">
          <div class="table-scroll">
            <table id="holdings-table">
              <thead>
                <tr>
                  <th>Holding Name</th>
                  <th>Ticker</th>
                  <th>Portfolio Weight</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </div>
          <div class="empty-state" id="empty-state">No holdings match the current search.</div>
        </div>
      </div>

      <script>
        const csvText = {csv_payload};
        const holdingsShell = document.getElementById("holdings-shell");
        const tableCard = document.getElementById("table-card");
        const searchWrap = document.getElementById("search-wrap");
        const searchInput = document.getElementById("search-input");
        const searchButton = document.getElementById("search-btn");
        const downloadButton = document.getElementById("download-btn");
        const fullscreenButton = document.getElementById("fullscreen-btn");
        const rows = Array.from(document.querySelectorAll("#holdings-table tbody tr"));
        const enterFullscreenIcon = `
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H3v5"></path>
            <path d="M16 3h5v5"></path>
            <path d="M21 16v5h-5"></path>
            <path d="M8 21H3v-5"></path>
          </svg>
        `;
        const exitFullscreenIcon = `
          <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 9H4V4"></path>
            <path d="M15 9h5V4"></path>
            <path d="M9 15H4v5"></path>
            <path d="M15 15h5v5"></path>
          </svg>
        `;

        const resizeFrame = () => {{
          if (window.frameElement && !document.fullscreenElement) {{
            const nextHeight = Math.ceil(document.documentElement.scrollHeight);
            window.frameElement.style.height = `${{nextHeight}}px`;
          }}
        }};

        const applySearch = () => {{
          const query = searchInput.value.trim().toLowerCase();
          let visibleCount = 0;

          rows.forEach((row) => {{
            const matches = row.textContent.toLowerCase().includes(query);
            row.classList.toggle("hidden", !matches);
            if (matches) visibleCount += 1;
          }});

          tableCard.classList.toggle("show-empty", visibleCount === 0);
          resizeFrame();
        }};

        const syncFullscreenButton = () => {{
          const isFullscreen = document.fullscreenElement === holdingsShell;
          fullscreenButton.innerHTML = isFullscreen ? exitFullscreenIcon : enterFullscreenIcon;
          fullscreenButton.setAttribute("title", isFullscreen ? "Exit fullscreen" : "Fullscreen");
          fullscreenButton.setAttribute("aria-label", isFullscreen ? "Exit fullscreen" : "Fullscreen");
        }};

        searchButton.addEventListener("click", () => {{
          const willOpen = !searchWrap.classList.contains("active");
          searchWrap.classList.toggle("active", willOpen);

          if (willOpen) {{
            searchInput.focus();
          }} else {{
            searchInput.value = "";
            applySearch();
          }}

          resizeFrame();
        }});

        searchInput.addEventListener("input", applySearch);

        downloadButton.addEventListener("click", () => {{
          const blob = new Blob([csvText], {{ type: "text/csv;charset=utf-8;" }});
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = "holdings_table.csv";
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
        }});

        fullscreenButton.addEventListener("click", async () => {{
          if (document.fullscreenElement === holdingsShell) {{
            await document.exitFullscreen();
          }} else {{
            await holdingsShell.requestFullscreen();
          }}
        }});

        document.addEventListener("fullscreenchange", () => {{
          syncFullscreenButton();
          resizeFrame();
        }});

        if (window.ResizeObserver) {{
          const resizeObserver = new ResizeObserver(() => resizeFrame());
          resizeObserver.observe(document.body);
        }}

        syncFullscreenButton();
        [0, 80, 240].forEach((delay) => setTimeout(resizeFrame, delay));
      </script>
    </body>
    </html>
    """

    components.html(table_html, height=table_height, scrolling=False)


# Format percentage values consistently across tables and narrative text.
def format_pct(value, decimals: int = 1):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}%}"


# Prepare the filtered ETF summary export.
def build_metrics_download_df(filtered_summary: pd.DataFrame):
    if filtered_summary.empty:
        return pd.DataFrame()

    download_df = filtered_summary.copy()
    download_df["Sector"] = download_df["Ticker"].map(SECTOR_MAP)

    return download_df[
        [
            "Ticker",
            "Display_Name",
            "Sector",
            "Start_Date",
            "End_Date",
            "Observations",
            "Final_Cumulative_Return",
            "Annualized_Volatility",
            "Max_Drawdown",
        ]
    ].copy()


# Prepare the ETF correlation matrix export.
def build_correlation_download_df(correlation_matrix: pd.DataFrame):
    if correlation_matrix.empty:
        return pd.DataFrame()

    download_df = correlation_matrix.copy()
    download_df.index.name = "ETF"
    return download_df.reset_index()


# Prepare the representative stock comparison export.
def build_representative_download_df(
    comparison_df: pd.DataFrame,
    selected_etf: str,
    stock_metadata: dict | None
):
    if comparison_df.empty or stock_metadata is None:
        return pd.DataFrame()

    download_df = comparison_df.copy()
    download_df.insert(0, "Representative_Stock_Ticker", stock_metadata["Representative_Stock_Ticker"])
    download_df.insert(0, "Representative_Company", stock_metadata["Representative_Company"])
    download_df.insert(0, "ETF", selected_etf)
    return download_df


# Build the representative-stock metadata panel shown above the drill-down chart.
def build_representative_metadata_html(selected_etf: str, stock_metadata: dict):
    items = [
        ("Selected ETF", DISPLAY_NAME_MAP[selected_etf]),
        ("Representative Stock", stock_metadata["Representative_Stock_Ticker"]),
        ("Company", stock_metadata["Representative_Company"]),
        ("Why Selected", stock_metadata["Why_Selected"]),
    ]

    item_html = "".join(
        dedent(
            f"""
            <div class="drilldown-meta-item">
                <span class="drilldown-meta-label">{escape(label)}</span>
                <div class="drilldown-meta-value">{escape(str(value))}</div>
            </div>
            """
        ).strip()
        for label, value in items
    )

    return dedent(
        f"""
        <div class="drilldown-meta-card">
            <div class="drilldown-meta-grid">
                {item_html}
            </div>
        </div>
        """
    ).strip()


# Build the side-by-side summary table for the ETF and its representative stock.
def build_representative_summary_html(
    selected_etf: str,
    stock_metadata: dict,
    etf_summary: dict,
    stock_summary: dict
):
    stock_label = f"{stock_metadata['Representative_Stock_Ticker']} ({stock_metadata['Representative_Company']})"
    rows = [
        (
            "Final cumulative return",
            format_pct(etf_summary["Final_Cumulative_Return"]),
            format_pct(stock_summary["Final_Cumulative_Return"]),
        ),
        (
            "Annualized volatility",
            format_pct(etf_summary["Annualized_Volatility"]),
            format_pct(stock_summary["Annualized_Volatility"]),
        ),
        (
            "Maximum drawdown",
            format_pct(etf_summary["Max_Drawdown"]),
            format_pct(stock_summary["Max_Drawdown"]),
        ),
    ]

    row_html = "".join(
        dedent(
            f"""
            <tr>
                <td class="metric-name">{escape(metric_name)}</td>
                <td>{escape(etf_value)}</td>
                <td>{escape(stock_value)}</td>
            </tr>
            """
        ).strip()
        for metric_name, etf_value, stock_value in rows
    )

    return dedent(
        f"""
        <div class="drilldown-summary-card">
            <table class="drilldown-summary-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>{escape(DISPLAY_NAME_MAP[selected_etf])}</th>
                        <th>{escape(stock_label)}</th>
                    </tr>
                </thead>
                <tbody>
                    {row_html}
                </tbody>
            </table>
        </div>
        """
    ).strip()


# Turn the ETF-versus-stock metric gaps into a plain-language interpretation.
def build_representative_interpretation(
    selected_etf: str,
    stock_metadata: dict,
    etf_summary: dict,
    stock_summary: dict
):
    stock_ticker = stock_metadata["Representative_Stock_Ticker"]
    etf_label = DISPLAY_NAME_MAP[selected_etf]

    return_gap = stock_summary["Final_Cumulative_Return"] - etf_summary["Final_Cumulative_Return"]
    vol_gap = stock_summary["Annualized_Volatility"] - etf_summary["Annualized_Volatility"]
    drawdown_gap = stock_summary["Max_Drawdown"] - etf_summary["Max_Drawdown"]

    if abs(return_gap) < 1e-9:
        return_text = f"{stock_ticker} and {selected_etf} delivered almost the same cumulative return."
    elif return_gap > 0:
        return_text = f"{stock_ticker} outperformed {selected_etf} on cumulative return over the selected period."
    else:
        return_text = f"{stock_ticker} underperformed {selected_etf} on cumulative return over the selected period."

    slight_volatility_gap_threshold = 0.02

    if abs(vol_gap) < 1e-9:
        volatility_text = "Its annualized volatility was very similar to the ETF."
    elif 0 < vol_gap <= slight_volatility_gap_threshold:
        volatility_text = "It also showed slightly higher volatility than the ETF."
    elif -slight_volatility_gap_threshold <= vol_gap < 0:
        volatility_text = "It showed slightly lower volatility than the ETF."
    elif vol_gap > 0:
        volatility_text = "It also showed higher volatility than the ETF."
    else:
        volatility_text = "It showed lower volatility than the ETF."

    if abs(drawdown_gap) < 1e-9:
        drawdown_text = "Its maximum drawdown was also very similar."
    elif drawdown_gap < 0:
        drawdown_text = "Its drawdown was deeper than the ETF's."
    else:
        drawdown_text = "Its drawdown was shallower than the ETF's."

    if vol_gap > 0 or drawdown_gap < 0:
        diversification_text = (
            f"This comparison suggests that {etf_label} offered a smoother ride because diversification softened "
            f"some of the single-stock risk carried by {stock_ticker}."
        )
    elif return_gap > 0 and vol_gap <= 0 and drawdown_gap >= 0:
        diversification_text = (
            f"In this window, {stock_ticker} looked stronger on both return and downside measures, but it still "
            f"represents concentrated company-specific risk that the ETF spreads across multiple holdings."
        )
    else:
        diversification_text = (
            f"The result highlights the trade-off between the focused upside of one sector-typical stock and the "
            f"broader diversification of an ETF basket."
        )

    return f"{return_text} {volatility_text} {drawdown_text} {diversification_text}"


# Wrap the representative interpretation in the card used on the page.
def build_representative_interpretation_html(interpretation_text: str):
    return dedent(
        f"""
        <div class="drilldown-interpretation-card">
            <span class="drilldown-interpretation-title">Interpretation</span>
            <div class="drilldown-interpretation">{escape(interpretation_text)}</div>
        </div>
        """
    ).strip()


# Build a small note card used for short explanatory insights.
def build_insight_note_html(note_text: str):
    return dedent(
        f"""
        <div class="insight-note-card">
            <div class="insight-note-text">{escape(note_text)}</div>
        </div>
        """
    ).strip()

# ---------------------------------
# 6. Data filtering
# ---------------------------------
# Prepare control defaults from the loaded ETF dataset.
all_etfs = sort_tickers_by_default_order(prices_df["Ticker"].dropna().unique().tolist())
min_date = prices_df["Date"].min().date()
max_date = prices_df["Date"].max().date()

# Collect the user selections that drive the filtered views below.
st.markdown("### Controls")
controls_col1, controls_col2, controls_col3 = st.columns([1.05, 1.7, 1.35])

with controls_col1:
    mode = st.radio(
        "Display mode",
        options=["Light", "Dark"],
        index=1,
        horizontal=True
    )

with controls_col2:
    selected_etfs = st.multiselect(
        "Select ETFs",
        options=all_etfs,
        default=all_etfs
    )
    selected_etfs = sort_tickers_by_default_order(selected_etfs)

with controls_col3:
    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

if len(selected_etfs) == 0:
    st.warning("Please select at least one ETF in Controls.")
    st.stop()

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Apply the selected theme before rendering the page content.
theme = get_theme(mode)
inject_css(theme)
stabilize_streamlit_ui()
hide_calendar_quick_range_footer()

# Build the filtered datasets reused across every section of the page.
filtered_prices = prices_df[
    (prices_df["Ticker"].isin(selected_etfs)) &
    (prices_df["Date"] >= pd.to_datetime(start_date)) &
    (prices_df["Date"] <= pd.to_datetime(end_date))
].copy()

metrics_ready_filtered, filtered_summary = build_filtered_metrics(filtered_prices)
aligned_etf_returns_df, correlation_matrix_df = build_correlation_matrix(filtered_prices, selected_etfs)

# ---------------------------------
# 7. Page rendering
# ---------------------------------
# Hero section
st.markdown(
    """
    <div class="hero-card">
        <h1>Sector ETF Performance Explorer</h1>
        <p>
            ETFs are baskets of stocks that make it easier to compare how different sectors behave in the market.
        </p>
        <p>
            This tool helps users explore sector ETF performance through cumulative return, volatility, drawdown, risk-return trade-off, correlation, holdings, and representative stock comparison in one clear and interactive view.
        </p>
        <p>
            Built for beginner investors and finance students using WRDS/CRSP price data and official SPDR holdings files.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="section-note">
        <strong>Focus:</strong> performance, risk, diversification, holdings, and representative stock comparison.
    </div>
    """,
    unsafe_allow_html=True
)

# Quick guide
with st.expander("First time here? Open a quick guide"):
    st.markdown(
        """
1. A comparison group of **4 ETFs** is usually the clearest starting point; too many ETFs at once can make charts look messy.  
2. Use **Display mode** to switch between **Light** and **Dark** views.  
3. Choose the ETFs you want to compare, then adjust the **date range** in Controls.  
4. Use chart **zoom**, mouse-wheel scrolling, and the **range slider** to inspect shorter periods more closely.  
5. Use the chart toolbar icons for **zoom reset**, downloads, and **fullscreen** when you want a larger view.  
6. Open **expanders** for extra explanation without cluttering the page, and use the **download buttons** near the bottom to export the filtered results.
        """
    )

# Quick overview
st.subheader("Quick Overview")

if not filtered_summary.empty:
    best_return = filtered_summary.loc[filtered_summary["Final_Cumulative_Return"].idxmax()]
    lowest_vol = filtered_summary.loc[filtered_summary["Annualized_Volatility"].idxmin()]
    deepest_dd = filtered_summary.loc[filtered_summary["Max_Drawdown"].idxmin()]
    shallowest_dd = filtered_summary.loc[filtered_summary["Max_Drawdown"].idxmax()]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        overview_card(
            "Best Cumulative Return",
            best_return["Ticker"],
            SECTOR_MAP[best_return["Ticker"]],
            f"{best_return['Final_Cumulative_Return']:.1%}",
            value_positive=True
        )

    with col2:
        overview_card(
            "Lowest Volatility",
            lowest_vol["Ticker"],
            SECTOR_MAP[lowest_vol["Ticker"]],
            f"{lowest_vol['Annualized_Volatility']:.1%}",
            value_positive=True
        )

    with col3:
        overview_card(
            "Deepest Drawdown",
            deepest_dd["Ticker"],
            SECTOR_MAP[deepest_dd["Ticker"]],
            f"{deepest_dd['Max_Drawdown']:.1%}",
            value_positive=False
        )

    with col4:
        overview_card(
            "Shallowest Drawdown",
            shallowest_dd["Ticker"],
            SECTOR_MAP[shallowest_dd["Ticker"]],
            f"{shallowest_dd['Max_Drawdown']:.1%}",
            value_positive=False
        )

st.divider()

# Performance section
st.subheader("Performance")
st.markdown(
    """
    <div class="small-caption">
        Use zoom, pan, and the range slider to inspect shorter periods in more detail.
        Quick buttons (6M / 1Y / 3Y / All) are relative to the selected end date in Controls.
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("Absolute Price (Optional)", expanded=False):
    st.markdown(
        """
        Absolute ETF price can be useful as a reference view, but price level alone is less informative for comparing performance strength or risk across ETFs. Also, raw price may reflect split-related level changes.

        Cumulative return is still the better main comparison tool because it shows how much each ETF actually grew or fell over the selected window.
        """
    )

    if not filtered_prices.empty:
        absolute_price_fig = build_absolute_price_figure(filtered_prices, theme)
        st.plotly_chart(
            absolute_price_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "displayModeBar": True,
                "scrollZoom": True
            },
            theme=None
        )
    else:
        st.info("Absolute price data is unavailable for the current ETF selection and date range.")

st.markdown(
    '<div class="chart-title">Cumulative Return of Selected Sector ETFs</div>',
    unsafe_allow_html=True
)

if not metrics_ready_filtered.empty:
    perf_fig = build_performance_figure(metrics_ready_filtered, theme)
    st.plotly_chart(
        perf_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True,
            "scrollZoom": True
        },
        theme=None
    )

st.divider()

# Risk section
st.subheader("Risk")
st.markdown(
    f"""
    <div class="section-note">
        Review both a static risk summary and a time-varying risk view for the current ETF selection.
        Based on selected range: <strong>{pd.to_datetime(start_date).date()} to {pd.to_datetime(end_date).date()}</strong>.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="chart-title">Risk Snapshot</div>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="small-caption">
        This section compares annualized volatility and maximum drawdown across the selected ETFs.
    </div>
    """,
    unsafe_allow_html=True
)

if not filtered_summary.empty:
    risk_fig = build_risk_snapshot_figure(filtered_summary, theme)
    st.plotly_chart(
        risk_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True,
            "scrollZoom": False
        },
        theme=None
    )

st.markdown(
    '<div class="chart-title">Rolling Volatility</div>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="small-caption">
        Rolling volatility shows how short-term risk changes over time instead of reducing the whole period to one number.
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("What does the rolling window mean?"):
    st.markdown(
        """
A 21D window uses the most recent 21 trading days to estimate volatility.  
A shorter window reacts faster to new market moves.  
A longer window is smoother and highlights broader risk trends.
        """
    )

rolling_window_label = st.radio(
    "Rolling window",
    options=["21D", "30D", "60D"],
    index=2,
    horizontal=True,
    key="rolling_volatility_window"
)
rolling_window_days = int(rolling_window_label.replace("D", ""))
rolling_volatility_df = compute_rolling_volatility(filtered_prices, rolling_window_days)

if rolling_volatility_df.empty:
    st.info(
        f"Rolling volatility needs at least {rolling_window_days} trading days in the selected range. "
        "Try a longer date range or a shorter rolling window."
    )
else:
    rolling_volatility_fig = build_rolling_volatility_figure(
        rolling_volatility_df,
        theme,
        rolling_window_label
    )
    st.plotly_chart(
        rolling_volatility_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True,
            "scrollZoom": True
        },
        theme=None
    )

st.divider()

# ETF comparison section
st.subheader("ETF Comparison")

st.markdown(
    '<div class="chart-title">Risk-return Scatter</div>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="small-caption">
        Each point summarizes the trade-off between cumulative return and annualized volatility for one ETF.
    </div>
    """,
    unsafe_allow_html=True
)

if not filtered_summary.empty:
    risk_return_fig = build_risk_return_scatter_figure(filtered_summary, theme)
    st.plotly_chart(
        risk_return_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True,
            "scrollZoom": False
        },
        theme=None
    )
    st.markdown(
        build_insight_note_html(
            "Higher points indicate stronger cumulative return, while points farther to the right indicate higher volatility. A point that is both higher and farther left would represent a stronger return-risk trade-off over this window."
        ),
        unsafe_allow_html=True
    )

st.markdown(
    '<div class="chart-title">Correlation Heatmap</div>',
    unsafe_allow_html=True
)

with st.expander("How to read diversification here"):
    st.markdown(
        """
Lower correlation means two ETFs moved less alike over the selected period.  
ETFs that move less alike may provide stronger diversification when combined.  
That can help reduce the impact of one single market move or sector swing on the whole portfolio.  
High correlation means the ETFs often moved in a similar direction.
        """
    )

if len(selected_etfs) < 2:
    st.info("Correlation analysis requires at least two ETFs.")
elif correlation_matrix_df.empty:
    st.info("Not enough overlapping return observations are available to compute the current correlation heatmap.")
else:
    correlation_heatmap_fig = build_correlation_heatmap_figure(correlation_matrix_df, theme)
    st.plotly_chart(
        correlation_heatmap_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True,
            "scrollZoom": False
        },
        theme=None
    )

st.divider()

# Holdings explanation section
st.subheader("Holdings Explanation")

holdings_etf = st.selectbox(
    "Select one ETF for holdings view",
    options=selected_etfs,
    index=0
)

selected_holdings = holdings_df[holdings_df["ETF"] == holdings_etf].copy()
selected_holdings = selected_holdings.sort_values("Weight", ascending=False).reset_index(drop=True)

if not selected_holdings.empty:
    holdings_as_of = None
    if "Holdings_As_Of" in selected_holdings.columns and selected_holdings["Holdings_As_Of"].notna().any():
        holdings_as_of = pd.to_datetime(selected_holdings["Holdings_As_Of"].iloc[0]).date()

    if holdings_as_of is not None:
        st.markdown(
            f"""
            <div class="small-caption">
                Holdings shown below are based on the latest available snapshot in this project:
                <strong>{holdings_as_of}</strong>. They do not change with the selected price date range.
            </div>
            """,
            unsafe_allow_html=True
        )

    top_holding = selected_holdings.iloc[0]

    st.markdown(
        f"""
        **Largest holding:** {top_holding['Holding_Name']} ({top_holding['Holding_Ticker']})  
        **Portfolio weight:** {top_holding['Weight']:.2f}%
        """
    )

    holdings_fig = build_holdings_figure(selected_holdings, holdings_etf, theme)
    st.plotly_chart(
        holdings_fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "displayModeBar": True
        },
        theme=None
    )

    table_df = selected_holdings[["Holding_Name", "Holding_Ticker", "Weight"]].copy()
    table_df["Weight"] = table_df["Weight"].map(lambda x: f"{x:.2f}%")
    table_df.columns = ["Holding Name", "Ticker", "Portfolio Weight"]
    render_holdings_table_component(table_df, theme)

st.divider()

# Representative stock drill-down section
st.subheader("Representative Stock Drill-down")
st.markdown(
    """
    <div class="small-caption">
        Compare one selected ETF with a large, intuitive, sector-typical company over the same user-selected date range and shared trading dates. It is not necessarily the ETF’s largest holding.
    </div>
    """,
    unsafe_allow_html=True
)

representative_etf = st.selectbox(
    "Select one ETF for representative stock drill-down",
    options=selected_etfs,
    index=0,
    key="representative_drilldown_etf"
)

representative_comparison_df = pd.DataFrame()
representative_stock_ticker = None
representative_metadata = get_representative_stock_metadata(
    representative_mapping_df,
    representative_etf
)

if representative_metadata is not None:
    st.markdown(
        build_representative_metadata_html(representative_etf, representative_metadata),
        unsafe_allow_html=True
    )

    representative_stock_ticker = representative_metadata["Representative_Stock_Ticker"]
    representative_stock_prices = representative_stock_clean_df[
        (representative_stock_clean_df["ETF"] == representative_etf) &
        (representative_stock_clean_df["Representative_Stock_Ticker"] == representative_stock_ticker) &
        (representative_stock_clean_df["Date"] >= pd.to_datetime(start_date)) &
        (representative_stock_clean_df["Date"] <= pd.to_datetime(end_date))
    ].copy()

    representative_etf_prices = filtered_prices[
        filtered_prices["Ticker"] == representative_etf
    ].copy()

    representative_comparison_df = build_aligned_representative_comparison_data(
        representative_etf_prices,
        representative_stock_prices
    )

    if representative_comparison_df.empty:
        st.info("Representative stock comparison is unavailable for the selected ETF and date range.")
    else:
        st.markdown(
            f'<div class="chart-title">{DISPLAY_NAME_MAP[representative_etf]} vs {representative_stock_ticker} Cumulative Return</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div class="small-caption">
                Both lines are reset to 0% at the selected start date so performance can be compared over the same window. Zooming inside the chart changes the view only.
            </div>
            """,
            unsafe_allow_html=True
        )

        representative_fig = build_representative_comparison_figure(
            representative_comparison_df,
            representative_etf,
            representative_metadata,
            theme
        )
        st.plotly_chart(
            representative_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "displayModeBar": True,
                "scrollZoom": True
            },
            theme=None
        )

        representative_etf_summary = compute_representative_comparison_metrics(
            representative_comparison_df,
            "ETF"
        )
        representative_stock_summary = compute_representative_comparison_metrics(
            representative_comparison_df,
            "Stock"
        )

        st.markdown(
            build_representative_summary_html(
                representative_etf,
                representative_metadata,
                representative_etf_summary,
                representative_stock_summary
            ),
            unsafe_allow_html=True
        )

        interpretation_text = build_representative_interpretation(
            representative_etf,
            representative_metadata,
            representative_etf_summary,
            representative_stock_summary
        )
        st.markdown(
            build_representative_interpretation_html(interpretation_text),
            unsafe_allow_html=True
        )
else:
    st.info("Representative stock mapping is unavailable for the selected ETF.")

st.divider()

# Download section
st.subheader("Download Filtered Results")
st.markdown(
    """
    <div class="small-caption">
        Export the currently filtered ETF data, summary metrics, correlation matrix, and representative stock comparison output.
    </div>
    """,
    unsafe_allow_html=True
)

download_date_label = f"{pd.to_datetime(start_date).date()}_to_{pd.to_datetime(end_date).date()}"
filtered_prices_download_df = (
    sort_dataframe_by_etf_order(
        filtered_prices.copy(),
        ticker_col="Ticker",
        secondary_cols=["Date"],
    )
    .reset_index(drop=True)
)
metrics_download_df = build_metrics_download_df(filtered_summary)
correlation_download_df = build_correlation_download_df(correlation_matrix_df)
representative_download_df = build_representative_download_df(
    representative_comparison_df,
    representative_etf,
    representative_metadata
)

download_col1, download_col2 = st.columns(2)

with download_col1:
    st.download_button(
        "Download Filtered ETF Time Series",
        data=filtered_prices_download_df.to_csv(index=False),
        file_name=f"filtered_etf_prices_{download_date_label}.csv",
        mime="text/csv"
    )
    st.download_button(
        "Download ETF Metrics Summary",
        data=metrics_download_df.to_csv(index=False),
        file_name=f"filtered_etf_metrics_summary_{download_date_label}.csv",
        mime="text/csv"
    )

with download_col2:
    if not correlation_download_df.empty:
        st.download_button(
            "Download ETF Correlation Matrix",
            data=correlation_download_df.to_csv(index=False),
            file_name=f"etf_correlation_matrix_{download_date_label}.csv",
            mime="text/csv"
        )
    else:
        st.caption("Correlation matrix download becomes available when at least two ETFs share overlapping return data.")

    if not representative_download_df.empty and representative_stock_ticker is not None:
        st.download_button(
            "Download Representative Stock Comparison",
            data=representative_download_df.to_csv(index=False),
            file_name=f"representative_comparison_{representative_etf}_vs_{representative_stock_ticker}_{download_date_label}.csv",
            mime="text/csv"
        )
    else:
        st.caption("Representative comparison download becomes available when the current ETF and stock share valid dates.")

st.divider()

# Key takeaways section
st.subheader("Key Takeaways")

if not filtered_summary.empty and not selected_holdings.empty:
    best_return = filtered_summary.loc[filtered_summary["Final_Cumulative_Return"].idxmax()]
    lowest_vol = filtered_summary.loc[filtered_summary["Annualized_Volatility"].idxmin()]
    deepest_dd = filtered_summary.loc[filtered_summary["Max_Drawdown"].idxmin()]
    top_holding = selected_holdings.iloc[0]
    lowest_avg_correlation_ticker = None

    if not correlation_matrix_df.empty and len(correlation_matrix_df.index) >= 2:
        avg_correlation_by_etf = (
            correlation_matrix_df.where(~np.eye(len(correlation_matrix_df), dtype=bool))
            .mean(axis=1)
            .dropna()
        )
        if not avg_correlation_by_etf.empty:
            lowest_avg_correlation_ticker = avg_correlation_by_etf.idxmin()

    representative_takeaway = None
    if (
        representative_metadata is not None and
        not representative_comparison_df.empty and
        representative_stock_ticker is not None
    ):
        representative_etf_summary = compute_representative_comparison_metrics(
            representative_comparison_df,
            "ETF"
        )
        representative_stock_summary = compute_representative_comparison_metrics(
            representative_comparison_df,
            "Stock"
        )

        rep_return_gap = (
            representative_stock_summary["Final_Cumulative_Return"] -
            representative_etf_summary["Final_Cumulative_Return"]
        )

        if abs(rep_return_gap) < 1e-9:
            representative_takeaway = (
                f"In the representative-stock view, **{representative_stock_ticker}** and "
                f"**{DISPLAY_NAME_MAP[representative_etf]}** delivered almost the same cumulative return over the selected window."
            )
        elif rep_return_gap > 0:
            representative_takeaway = (
                f"In the representative-stock view, **{representative_stock_ticker}** outperformed "
                f"**{DISPLAY_NAME_MAP[representative_etf]}** on cumulative return over the selected window."
            )
        else:
            representative_takeaway = (
                f"In the representative-stock view, **{DISPLAY_NAME_MAP[representative_etf]}** outperformed "
                f"**{representative_stock_ticker}** on cumulative return over the selected window."
            )

    st.markdown(
        f"""
- Over the selected period, **{DISPLAY_NAME_MAP[best_return['Ticker']]}** delivered the strongest cumulative return at **{best_return['Final_Cumulative_Return']:.1%}**.
- **{DISPLAY_NAME_MAP[lowest_vol['Ticker']]}** recorded the lowest annualized volatility at **{lowest_vol['Annualized_Volatility']:.1%}**, suggesting relatively more stable price movement.
- **{DISPLAY_NAME_MAP[deepest_dd['Ticker']]}** experienced the deepest drawdown at **{deepest_dd['Max_Drawdown']:.1%}**, indicating the highest downside pressure during market declines.
- {f"**{DISPLAY_NAME_MAP[lowest_avg_correlation_ticker]}** had the lowest average correlation with the other selected ETFs, which may suggest relatively stronger diversification potential in this comparison set." if lowest_avg_correlation_ticker is not None else "Diversification is easiest to compare in the correlation heatmap, where lower correlation means the selected ETFs moved less alike over the period."}
- {representative_takeaway if representative_takeaway is not None else "The representative-stock comparison shows how one sector-typical company can behave differently from the broader ETF basket over the same window."}
- In the holdings snapshot for **{DISPLAY_NAME_MAP[holdings_etf]}**, the largest position is **{top_holding['Holding_Name']} ({top_holding['Holding_Ticker']})**, with a portfolio weight of **{top_holding['Weight']:.2f}%**.
- This tool is designed to support **educational sector comparison** rather than investment advice.
        """
    )
