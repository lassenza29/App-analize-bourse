import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import feedparser
import urllib.parse
import time
import html
from numbers import Real

st.set_page_config(
    page_title="Analyseur Bourse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --bg: #050607;
        --panel: #0d1113;
        --text: #f5f7f2;
        --muted: #90999a;
        --line: rgba(255,255,255,0.10);
        --accent: #2f80ff;
        --accent-strong: #1f6fff;
        --accent-soft: rgba(47,128,255,0.20);
        --green: #53ff9a;
        --red: #ff5757;
        --yellow: #ffd166;
    }

    html, body, [class*="css"] {
        font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 8%, rgba(47,128,255,0.34), transparent 31%),
            radial-gradient(circle at 86% 5%, rgba(30,95,255,0.30), transparent 35%),
            linear-gradient(180deg, #07142a 0%, #050914 44%, #030405 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 5.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1280px;
    }

    [data-testid="stHeader"] {
        background: rgba(5,8,14,0.74);
        backdrop-filter: blur(18px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    h1, h2, h3, h4, h5 {
        color: var(--text) !important;
        font-weight: 700 !important;
        letter-spacing: 0 !important;
        text-transform: none !important;
    }

    h2 {
        font-size: 1.85rem !important;
        margin-bottom: 0.9rem !important;
    }

    .terminal-shell {
        background:
            radial-gradient(circle at 80% 20%, rgba(47,128,255,0.24), transparent 35%),
            linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02)),
            rgba(13,17,19,0.86);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 22px;
        padding: 22px 24px;
        box-shadow: 0 26px 80px rgba(0,0,0,0.42);
        margin-bottom: 24px;
    }

    .terminal-topline {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 16px;
        margin-bottom: 14px;
    }

    .status-pill {
        color: #f5f7f2;
        background: var(--accent);
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 0.72rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        white-space: nowrap;
        box-shadow: 0 10px 30px rgba(47,128,255,0.35);
    }

    .hero-title {
        font-size: clamp(2.2rem, 5vw, 4.8rem);
        line-height: 0.95;
        font-weight: 850;
        color: var(--text);
        margin: 0;
    }

    .hero-subtitle {
        max-width: 780px;
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.55;
        margin-top: 14px;
    }

    .element-container,
    [data-testid="column"],
    .stColumn {
        overflow: visible !important;
    }

    .fin-card {
        position: relative;
        overflow: visible;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
            rgba(13,17,19,0.92);
        border: 1px solid var(--line);
        padding: 18px;
        margin-bottom: 16px;
        border-radius: 18px;
        box-shadow: 0 18px 46px rgba(0,0,0,0.24);
        min-height: 112px;
        cursor: default;
    }

    .fin-card:hover {
        border-color: rgba(47,128,255,0.48);
        background:
            linear-gradient(180deg, rgba(47,128,255,0.11), rgba(255,255,255,0.018)),
            rgba(13,17,19,0.96);
    }

    .fin-card[data-tooltip]:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        z-index: 999999;
        left: 14px;
        top: calc(100% + 10px);
        width: min(360px, 80vw);
        padding: 13px 14px;
        border-radius: 14px;
        background: rgba(3,7,12,0.98);
        border: 1px solid rgba(47,128,255,0.45);
        box-shadow: 0 20px 55px rgba(0,0,0,0.55);
        color: #f5f7f2;
        font-size: 0.82rem;
        line-height: 1.45;
        font-weight: 650;
        white-space: normal;
        text-transform: none;
        letter-spacing: 0;
        pointer-events: none;
    }

    .fin-card.metric-positive {
        border-color: rgba(83,255,154,0.42);
        background:
            linear-gradient(180deg, rgba(83,255,154,0.08), rgba(255,255,255,0.018)),
            rgba(13,17,19,0.94);
    }

    .fin-card.metric-negative {
        border-color: rgba(255,87,87,0.42);
        background:
            linear-gradient(180deg, rgba(255,87,87,0.08), rgba(255,255,255,0.018)),
            rgba(13,17,19,0.94);
    }

    .fin-title {
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .fin-val {
        color: var(--text);
        font-size: 1.45rem;
        font-weight: 850;
        line-height: 1.15;
    }

    .fin-val.metric-positive {
        color: var(--green);
    }

    .fin-val.metric-negative {
        color: var(--red);
    }

    .fin-na {
        color: #5f6869;
        font-size: 1.2rem;
    }

    .fin-cash {
        color: var(--green);
        font-size: 1.05rem;
        font-weight: 900;
    }

    .score-container {
        position: relative;
        overflow: hidden;
        text-align: left;
        padding: 24px;
        background:
            radial-gradient(circle at 80% 20%, rgba(47,128,255,0.32), transparent 34%),
            linear-gradient(145deg, #17294a, #07142a 72%);
        border: 1px solid rgba(47,128,255,0.42);
        border-radius: 24px;
        min-height: 240px;
        box-shadow: 0 28px 70px rgba(0,0,0,0.34);
    }

    .score-container.metric-positive {
        border-color: rgba(83,255,154,0.42);
    }

    .score-container.metric-negative {
        border-color: rgba(255,87,87,0.42);
    }

    .score-title {
        color: rgba(245,247,242,0.72);
        font-size: 0.75rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .score-val {
        color: var(--text);
        font-size: 5.4rem;
        line-height: 0.95;
        font-weight: 900;
        margin-top: 22px;
    }

    .score-val.metric-positive {
        color: var(--green);
    }

    .score-val.metric-negative {
        color: var(--red);
    }

    .score-caption {
        color: rgba(245,247,242,0.72);
        font-size: 0.86rem;
        margin-top: 12px;
    }

    .expert-verdict {
        border: 1px solid var(--line);
        border-left: 6px solid #777;
        border-radius: 18px;
        padding: 20px;
        background: rgba(13,17,19,0.88);
        margin-bottom: 24px;
    }

    .buy-verdict { border-left-color: var(--green); }
    .hold-verdict { border-left-color: var(--yellow); }
    .sell-verdict { border-left-color: var(--red); }

    .expert-verdict h4 {
        margin: 0 0 8px 0;
        color: var(--text) !important;
    }

    .expert-verdict p {
        color: #b8c0c0;
        line-height: 1.6;
        font-size: 0.95rem;
        margin: 0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--line);
        margin-bottom: 18px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-bottom: none;
        border-radius: 16px 16px 0 0;
        padding: 13px 20px;
        color: var(--muted);
        font-weight: 850;
    }

    .stTabs [aria-selected="true"] {
        background: var(--accent-soft);
        color: var(--text);
        border-color: rgba(47,128,255,0.52);
    }

    .stRadio [role="radiogroup"] {
        background: rgba(13,17,19,0.78);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 8px;
        gap: 8px;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        background: rgba(13,17,19,0.96) !important;
        color: var(--text) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important;
        min-height: 48px;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(47,128,255,0.75) !important;
        box-shadow: 0 0 0 3px rgba(47,128,255,0.18) !important;
    }

    .stButton button,
    .stDownloadButton button {
        background: var(--accent);
        color: #f5f7f2;
        border: 0;
        border-radius: 999px;
        padding: 0.75rem 1.25rem;
        font-weight: 950;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        box-shadow: 0 12px 30px rgba(47,128,255,0.28);
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        background: #5b9dff;
        color: #ffffff;
    }

    .stDataFrame {
        border: 1px solid var(--line);
        border-radius: 18px;
        overflow: hidden;
        background: rgba(13,17,19,0.9);
    }

    hr {
        border: none;
        border-top: 1px solid var(--line);
        margin: 30px 0;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 5.8rem !important;
        }

        .terminal-shell {
            padding: 18px;
            border-radius: 18px;
        }

        .hero-title {
            font-size: 2.45rem;
        }

        .score-val {
            font-size: 4rem;
        }
    }
</style>
""", unsafe_allow_html=True)

TOP_ACTIONS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "BRK-B", "JPM", "V", "MA",
    "LLY", "UNH", "XOM", "PG", "COST", "HD", "ASML", "SAP", "RMS.PA", "MC.PA",
    "OR.PA", "TTE.PA", "AIR.PA", "SU.PA", "SAN.PA", "AI.PA", "KER.PA", "BNP.PA"
]

TOP_SMALL_CAPS = [
    "CELH", "ENPH", "FIVE", "HALO", "UFPI", "MEDP", "SPSC", "QLYS", "MMSI", "BOOT",
    "EXLS", "LNTH", "TMDX", "ALRM", "ITRI", "WING", "NXT", "FN", "CVLT", "IPAR",
    "AKE.PA", "BEN.PA", "VIRP.PA", "ALCJ.PA", "IDL.PA"
]

TOP_ETFS = [
    "SPY", "QQQ", "VTI", "VOO", "SCHD", "VEA", "VWO", "IWM", "XLK", "XLF",
    "IWDA.AS", "VWCE.DE", "CSPX.L", "ESE.PA", "CW8.PA", "WPEA.PA", "PANX.PA",
    "PAEEM.PA", "PUST.PA", "MSE.PA"
]

MODULES = ["ANALYSE INDIVIDUELLE", "TOP SELECTION", "Comparer"]

if "module_choice" not in st.session_state:
    st.session_state.module_choice = "ANALYSE INDIVIDUELLE"

if "analysis_ticker" not in st.session_state:
    st.session_state.analysis_ticker = ""

RATIO_TOOLTIPS = {
    "PER": "PER - Prix vs profits. Repere : 10 a 20. Tech accepte jusqu'a 30+. Cher si > 35.",
    "PEG": "PEG - PER ajuste a la croissance. Repere : <= 1. Sous-evalue si < 1. Cher si > 2.",
    "PRICE / BOOK": "P/B - Prix vs valeur du patrimoine. Repere : 1 a 2. Tres bas si < 1. Cher si > 3.",
    "P/B": "P/B - Prix vs valeur du patrimoine. Repere : 1 a 2. Tres bas si < 1. Cher si > 3.",
    "PRICE / SALES": "P/S - Prix vs chiffre d'affaires. Repere : < 2. Surevalue si > 5.",
    "P/S": "P/S - Prix vs chiffre d'affaires. Repere : < 2. Surevalue si > 5.",
    "EV / EBITDA": "EV / EBITDA - Valeur totale avec dette vs rentabilite brute. Repere : < 10. Plus c'est bas, mieux c'est.",
    "MARGE OP": "Marge Operationnelle - Efficacite du business. Repere : > 15%.",
    "MARGE OPERATIONNELLE": "Marge Operationnelle - Efficacite du business. Repere : > 15%.",
    "MARGE NETTE": "Marge Nette - Benefice reel restant. Repere : > 10%. Luxe et Tech visent > 20%.",
    "ROE": "ROE - Rendement de l'argent des actionnaires. Repere : > 15%.",
    "ROCE": "ROCE / ROIC - Rendement global actionnaires + dettes. Repere : > 12%.",
    "ROIC": "ROCE / ROIC - Rendement global actionnaires + dettes. Repere : > 12%.",
    "ROA": "ROA - Rentabilite de toutes les machines/actifs. Repere : > 5%.",
    "LEVIER DETTE": "Dette Nette / EBITDA - Annees pour rembourser la dette. Repere : < 2.5x. Danger si > 4x.",
    "DETTE NETTE": "Dette Nette / EBITDA - Annees pour rembourser la dette. Repere : < 2.5x. Danger si > 4x.",
    "DEBT / EQUITY": "Dette / Capitaux Propres - Poids des banques vs actionnaires. Repere : < 1 ou < 100%.",
    "DETTE / CAPITAUX": "Dette / Capitaux Propres - Poids des banques vs actionnaires. Repere : < 1 ou < 100%.",
    "CURRENT RATIO": "Current Ratio - Liquidite pour payer les factures a court terme. Repere : > 1.5. Alerte si < 1.",
    "COUVERTURE": "Couverture des Interets - Capacite a payer les interets de la dette. Repere : > 5x.",
    "PAYOUT": "Payout Ratio - Part du profit versee en dividende. Repere : 30% a 60%. Danger de coupure si > 80%.",
    "DIVIDEND YIELD": "Dividend Yield - Rendement annuel du dividende. Repere : 2% a 5%. Piege si > 8%, cours souvent en chute.",
    "FCF YIELD": "FCF Yield - Rendement du cash reel disponible. Repere : > 5%."
}


def get_ratio_tooltip(title):
    normalized = str(title).upper()
    for key, tooltip in RATIO_TOOLTIPS.items():
        if key in normalized:
            return tooltip
    return None


def resolve_fx_rate(currency_code):
    if not currency_code or not isinstance(currency_code, str):
        return 1.0

    raw = currency_code.strip()
    curr = raw.upper()
    is_pence = curr == "GBX" or raw == "GBp"

    if curr in ["GBX", "GBP=X", "GBP"] or raw == "GBp":
        curr = "GBP"

    if curr == "EUR":
        return 0.01 if is_pence else 1.0

    fallbacks = {
        "USD": 0.92,
        "GBP": 1.17,
        "CHF": 1.03,
        "CAD": 0.68,
        "JPY": 0.006,
        "AUD": 0.60,
        "CNY": 0.13
    }

    try:
        data = yf.Ticker(f"{curr}EUR=X").history(period="1d")
        if not data.empty:
            rate = float(data["Close"].iloc[-1])
            return rate * 0.01 if is_pence else rate
    except Exception:
        pass

    rate = fallbacks.get(curr, 1.0)
    return rate * 0.01 if is_pence else rate


@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    return resolve_fx_rate(currency_code)


def get_fx_rate_live(currency_code):
    return resolve_fx_rate(currency_code)


def safe_float(val, multiplier=1.0, precision=2):
    if val is None or val == "":
        return None
    try:
        if pd.isna(val):
            return None
        return round(float(val) * multiplier, precision)
    except Exception:
        return None


def safe_str(val):
    if val is None or val == "":
        return "N/A"
    try:
        if pd.isna(val):
            return "N/A"
    except Exception:
        pass
    return str(val)


def is_num(val):
    return isinstance(val, Real) and not isinstance(val, bool) and not pd.isna(val)


def format_metric(val, suffix=""):
    if val is None:
        return "<span class='fin-na'>-</span>"
    if isinstance(val, str) and val.lower() == "cash positif":
        return "<span class='fin-cash'>CASH POSITIF</span>"
    if isinstance(val, str):
        return val
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"{formatted} {suffix}".strip()


def tone_score(value):
    if not is_num(value):
        return None
    return "positive" if value >= 50 else "negative"


def tone_higher(value, threshold=0):
    if not is_num(value):
        return None
    return "positive" if value > threshold else "negative"


def tone_lower(value, threshold):
    if not is_num(value):
        return None
    return "positive" if value < threshold else "negative"


def tone_between(value, low, high):
    if not is_num(value):
        return None
    return "positive" if low < value < high else "negative"


def tone_leverage(value):
    if isinstance(value, str) and value.lower() == "cash positif":
        return "positive"
    if not is_num(value):
        return None
    return "positive" if value < 2 else "negative"


def tone_target(target, price):
    if not is_num(target) or not is_num(price):
        return None
    return "positive" if target > price else "negative"


def tone_graham(graham, price):
    if not is_num(graham) or not is_num(price):
        return None
    return "positive" if graham > price else "negative"


def render_metric_card(title, html_value, tone=None, tooltip=None):
    tooltip_text = tooltip if tooltip is not None else get_ratio_tooltip(title)
    tooltip_attr = f' data-tooltip="{html.escape(tooltip_text, quote=True)}"' if tooltip_text else ""
    tone_class = f" metric-{tone}" if tone in ["positive", "negative"] else ""

    st.markdown(
        f"""
        <div class="fin-card{tone_class}"{tooltip_attr}>
            <div class="fin-title">{title}</div>
            <div class="fin-val{tone_class}">{html_value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def calculer_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def numeric_df_for_display(df):
    clean = df.copy()
    text_cols = ["Ticker", "TICKER", "Nom", "NOM", "Type", "TYPE", "Régime", "Regime"]
    for col in clean.columns:
        if col not in text_cols:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
    return clean


def cell_color(value, col_name):
    if not is_num(value):
        return ""

    col = col_name.upper()

    if "SCORE" in col:
        good = value >= 50
    elif "PER" in col:
        good = 0 < value < 25
    elif "ROE" in col or "MARGE" in col:
        good = value > 0
    elif "DETTE/EBITDA" in col:
        good = value < 2
    elif "FRAIS" in col or "TER" in col:
        good = value < 0.30
    else:
        return ""

    color = "#53ff9a" if good else "#ff5757"
    return f"color: {color}; font-weight: 900;"


def format_dataframe(df):
    formatters = {}

    for col in df.columns:
        if col.upper() == "SCORE":
            formatters[col] = "{:.0f}"
        elif any(key in col for key in ["Prix", "PRIX", "PER", "ROE", "Marge", "MARGE", "FRAIS", "TER", "DETTE"]):
            formatters[col] = "{:.2f}"
        elif any(key in col for key in ["Market", "MARKET", "AUM", "Cap", "CAP"]):
            formatters[col] = "{:.0f}"

    styled = df.style.format(formatters, na_rep="-")

    def color_column(column):
        return [cell_color(value, column.name) for value in column]

    return styled.apply(color_column, axis=0)


def open_asset_in_analysis(ticker):
    st.session_state.analysis_ticker = str(ticker).upper().strip()
    st.session_state.module_choice = "ANALYSE INDIVIDUELLE"
    st.rerun()


def render_open_asset_buttons(df, key_prefix):
    if df.empty:
        return

    st.markdown("#### Ouvrir en analyse individuelle")
    cols = st.columns(2)

    for i, (_, row) in enumerate(df.iterrows()):
        ticker = str(row.get("Ticker", row.get("TICKER", ""))).upper().strip()
        name = str(row.get("Nom", row.get("NOM", ""))).strip()

        if not ticker:
            continue

        label = f"{ticker} - {name}" if name else ticker

        with cols[i % 2]:
            if st.button(label, key=f"{key_prefix}_{i}_{ticker}"):
                open_asset_in_analysis(ticker)


def fetch_info_live(ticker_symbol, retries=3, backoff=1):
    for attempt in range(retries):
        try:
            tk = yf.Ticker(ticker_symbol)
            info = tk.info

            if info and (
                "symbol" in info
                or "regularMarketPrice" in info
                or "currentPrice" in info
                or "previousClose" in info
            ):
                return info

            time.sleep(backoff)
            backoff *= 2
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(backoff)
            backoff *= 2

    return None


@st.cache_data(ttl=600)
def fetch_info_with_retry(ticker_symbol, retries=3, backoff=1):
    return fetch_info_live(ticker_symbol, retries, backoff)


def extract_stock_data(info, fx_rate):
    d = {}

    d["Prix"] = safe_float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"), fx_rate)
    d["MarketCap"] = safe_float(info.get("marketCap"), fx_rate / 1_000_000)
    d["PER_Actuel"] = safe_float(info.get("trailingPE"))
    d["PER_Futur"] = safe_float(info.get("forwardPE"))
    d["PS"] = safe_float(info.get("priceToSalesTrailing12Months"))
    d["PB"] = safe_float(info.get("priceToBook"))
    d["EV_EBITDA"] = safe_float(info.get("enterpriseToEbitda"))
    d["BPA"] = safe_float(info.get("trailingEps"), fx_rate)
    d["BVPS"] = safe_float(info.get("bookValue"), fx_rate)

    if d["BPA"] and d["BVPS"] and (d["BPA"] * d["BVPS"]) > 0:
        d["Graham"] = round(math.sqrt(22.5 * d["BPA"] * d["BVPS"]), 2)
    else:
        d["Graham"] = None

    d["Marge_Brute"] = safe_float(info.get("grossMargins"), 100)
    d["Marge_Op"] = safe_float(info.get("operatingMargins"), 100)
    d["Marge_Nette"] = safe_float(info.get("profitMargins"), 100)
    d["ROE"] = safe_float(info.get("returnOnEquity"), 100)
    d["ROA"] = safe_float(info.get("returnOnAssets"), 100)

    treso = safe_float(info.get("totalCash"), fx_rate / 1_000_000)
    dette_totale = safe_float(info.get("totalDebt"), fx_rate / 1_000_000)
    d["EBITDA"] = safe_float(info.get("ebitda"), fx_rate / 1_000_000)

    d["Dette_Nette"] = dette_totale - treso if treso is not None and dette_totale is not None else None

    if d["Dette_Nette"] is not None and d["EBITDA"] and d["EBITDA"] > 0:
        d["Levier"] = "Cash Positif" if d["Dette_Nette"] < 0 else round(d["Dette_Nette"] / d["EBITDA"], 2)
    else:
        d["Levier"] = None

    d["Current_Ratio"] = safe_float(info.get("currentRatio"))
    d["Quick_Ratio"] = safe_float(info.get("quickRatio"))
    d["Debt_Equity"] = safe_float(info.get("debtToEquity"))
    d["Rev_Growth"] = safe_float(info.get("revenueGrowth"), 100)
    d["Payout"] = safe_float(info.get("payoutRatio"), 100)
    d["Target"] = safe_float(info.get("targetMeanPrice"), fx_rate)
    d["Analystes"] = info.get("numberOfAnalystOpinions", "N/A")

    reco_raw = info.get("recommendationKey", "N/A")
    d["Reco"] = reco_raw.replace("_", " ").upper() if isinstance(reco_raw, str) else "N/A"

    score = 0

    if isinstance(d["Levier"], float) and d["Levier"] < 2:
        score += 15
    elif isinstance(d["Levier"], str) and d["Levier"] == "Cash Positif":
        score += 15

    if d["ROE"] is not None and d["ROE"] > 15:
        score += 15
    if d["Marge_Nette"] is not None and d["Marge_Nette"] > 12:
        score += 15
    if d["Graham"] is not None and d["Prix"] is not None and d["Graham"] > d["Prix"]:
        score += 15
    if d["PER_Actuel"] is not None and 0 < d["PER_Actuel"] < 20:
        score += 10
    if d["Current_Ratio"] is not None and d["Current_Ratio"] > 1.2:
        score += 10
    if d["Rev_Growth"] is not None and d["Rev_Growth"] > 5:
        score += 10
    if d["Payout"] is not None and 0 < d["Payout"] < 60:
        score += 10

    d["Score"] = min(score, 100)
    d["Sector"] = safe_str(info.get("sector")).upper()
    d["Industry"] = safe_str(info.get("industry")).upper()

    return d


def extract_etf_data(info, ticker_symbol, fx_rate):
    d = {}

    d["Prix"] = safe_float(info.get("navPrice") or info.get("previousClose") or info.get("regularMarketPrice"), fx_rate)
    d["TER"] = safe_float(info.get("annualReportExpenseRatio"), 100)
    d["AUM"] = safe_float(info.get("totalAssets"), fx_rate / 1_000_000)

    name = str(info.get("longName", "")).upper()
    category = str(info.get("category", "")).upper()

    d["Distribution"] = "ACCUMULATION" if " ACC" in name or "ACCUM" in name else "DISTRIBUTION"
    d["Replication"] = "SYNTHETIQUE (SWAP)" if "SWAP" in name else "PHYSIQUE"

    is_pea = any(x in name for x in ["AMUNDI", "LYXOR", "BNP", "ISHARES"]) and ".PA" in ticker_symbol.upper()
    d["PEA"] = "ELIGIBLE PEA" if is_pea else "COMPTE-TITRES"

    score = 0

    if d["AUM"] is not None and d["AUM"] > 500:
        score += 30
    elif d["AUM"] is not None and d["AUM"] > 100:
        score += 20

    if d["TER"] is not None and d["TER"] < 0.15:
        score += 30
    elif d["TER"] is not None and d["TER"] < 0.30:
        score += 22
    elif d["TER"] is not None and d["TER"] < 0.50:
        score += 12

    if d["Distribution"] == "ACCUMULATION":
        score += 15
    if d["Replication"] == "PHYSIQUE":
        score += 10
    if "WORLD" in name or "S&P" in name or "MSCI" in name or "NASDAQ" in name or "GLOBAL" in category:
        score += 15

    d["Score"] = min(score, 100)

    return d


@st.cache_data(ttl=1800)
def get_press_news(ticker_symbol, company_name):
    news = []

    try:
        clean_ticker = ticker_symbol.split(".")[0]
        query = f'"{clean_ticker}" "{company_name}" finance'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"

        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:5]:
            title = entry.title.rsplit(" - ", 1)[0] if " - " in entry.title else entry.title
            news.append({
                "title": title,
                "link": entry.link,
                "publisher": entry.source.title if hasattr(entry, "source") and hasattr(entry.source, "title") else "Presse",
                "published": entry.published[5:16] if hasattr(entry, "published") else "Recent"
            })
    except Exception:
        pass

    if not news:
        try:
            tk_news = yf.Ticker(ticker_symbol).news
            if tk_news:
                for n in tk_news[:5]:
                    news.append({
                        "title": n.get("title", "Actualite de marche"),
                        "link": n.get("link", "#"),
                        "publisher": n.get("publisher", "Data Feed"),
                        "published": "Recent"
                    })
        except Exception:
            pass

    return news


def generate_consensus_and_verdict(data, is_etf):
    if is_etf:
        score = data.get("Score", 0)

        if score >= 70:
            verdict = "ACHAT"
            color = "buy-verdict"
        elif score >= 50:
            verdict = "CONSERVATION"
            color = "hold-verdict"
        else:
            verdict = "SOUS SURVEILLANCE"
            color = "sell-verdict"

        return f"""
        <div class="expert-verdict {color}">
            <h4>Verdict strategique : {verdict}</h4>
            <p>Score ETF : {score}/100. Actifs sous gestion : {format_metric(data.get("AUM"), "M€")}. Frais : {format_metric(data.get("TER"), "%")}. Replication : {data.get("Replication", "N/A")}. Fiscalite : {data.get("PEA", "N/A")}.</p>
        </div>
        """

    score = data.get("Score", 0)
    reco = data.get("Reco", "N/A").upper()

    if score >= 65 and "BUY" in reco:
        verdict = "ACHAT FORT"
        color = "buy-verdict"
    elif score >= 50:
        verdict = "ACCUMULATION"
        color = "buy-verdict"
    elif score >= 35:
        verdict = "CONSERVATION"
        color = "hold-verdict"
    else:
        verdict = "LIQUIDATION"
        color = "sell-verdict"

    valorisation = "attractive" if data.get("Graham") and data.get("Prix") and data["Graham"] > data["Prix"] else "tendue"

    return f"""
    <div class="expert-verdict {color}">
        <h4>Verdict strategique : {verdict}</h4>
        <p>Score d'integrite : {score}/100. Valorisation {valorisation}. ROE : {format_metric(data.get("ROE"), "%")}. Levier : {format_metric(data.get("Levier"), "x")}. Secteur : {data.get("Sector", "N/A")}. Distribution : {format_metric(data.get("Payout"), "%")}.</p>
    </div>
    """


def rank_universe(asset_type, limit=12):
    if asset_type == "ACTIONS":
        universe = TOP_ACTIONS
    elif asset_type == "SMALL CAPS":
        universe = TOP_SMALL_CAPS
    else:
        universe = TOP_ETFS

    rows = []

    for ticker in universe:
        try:
            info = fetch_info_live(ticker)

            if not info:
                continue

            fx = get_fx_rate_live(info.get("currency", "USD"))
            quote_type = info.get("quoteType", "")

            if asset_type == "ETF" or quote_type == "ETF":
                d = extract_etf_data(info, ticker, fx)

                rows.append({
                    "Ticker": ticker,
                    "Nom": info.get("shortName", ticker),
                    "Type": "ETF",
                    "Score": d["Score"],
                    "Prix €": d["Prix"],
                    "AUM M€": d["AUM"],
                    "TER %": d["TER"],
                    "Régime": d["PEA"]
                })
            else:
                d = extract_stock_data(info, fx)

                if asset_type == "SMALL CAPS":
                    market_cap = d.get("MarketCap")
                    if market_cap is not None and market_cap > 10_000:
                        continue

                rows.append({
                    "Ticker": ticker,
                    "Nom": info.get("shortName", ticker),
                    "Type": "Equity",
                    "Score": d["Score"],
                    "Prix €": d["Prix"],
                    "Market Cap M€": d["MarketCap"],
                    "PER": d["PER_Actuel"],
                    "ROE %": d["ROE"],
                    "Marge nette %": d["Marge_Nette"]
                })
        except Exception:
            continue

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    return df.sort_values("Score", ascending=False).head(limit)


@st.cache_data(ttl=3600)
def get_financial_metric_history(ticker_symbol, fx_rate):
    tk = yf.Ticker(ticker_symbol)

    try:
        financials = tk.quarterly_financials
    except Exception:
        financials = pd.DataFrame()

    try:
        balance = tk.quarterly_balance_sheet
    except Exception:
        balance = pd.DataFrame()

    if financials.empty:
        return pd.DataFrame()

    df = pd.DataFrame(index=financials.columns)

    metric_map = {
        "Chiffre d'affaires": ["Total Revenue", "Operating Revenue"],
        "Resultat brut": ["Gross Profit"],
        "EBITDA": ["EBITDA", "Normalized EBITDA"],
        "Resultat operationnel": ["Operating Income"],
        "Resultat net": ["Net Income", "Net Income Common Stockholders"]
    }

    for label, possible_rows in metric_map.items():
        for row_name in possible_rows:
            if row_name in financials.index:
                df[label] = financials.loc[row_name].astype(float) * fx_rate / 1_000_000
                break

    if not balance.empty:
        balance_map = {
            "Cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
            "Dette totale": ["Total Debt"]
        }

        for label, possible_rows in balance_map.items():
            for row_name in possible_rows:
                if row_name in balance.index:
                    df[label] = balance.loc[row_name].astype(float) * fx_rate / 1_000_000
                    break

    if "Chiffre d'affaires" in df.columns and "Resultat net" in df.columns:
        df["Marge nette %"] = (df["Resultat net"] / df["Chiffre d'affaires"]) * 100

    if "Dette totale" in df.columns and "Cash" in df.columns:
        df["Dette nette"] = df["Dette totale"] - df["Cash"]

    df = df.sort_index()
    df.index = pd.to_datetime(df.index)

    return df.dropna(how="all")


st.markdown("""
<div class="terminal-shell">
    <div class="terminal-topline">
        <div class="status-pill">Live Market Data</div>
    </div>
    <div class="hero-title">Finance cockpit.</div>
    <div class="hero-subtitle">
        Analyse fondamentale, scoring proprietaire, graphiques techniques, presse financiere et comparateur multi-actifs.
    </div>
</div>
""", unsafe_allow_html=True)

mode = st.radio(
    "Module",
    MODULES,
    index=MODULES.index(st.session_state.module_choice),
    label_visibility="collapsed",
    horizontal=True
)

st.session_state.module_choice = mode
st.markdown("<br>", unsafe_allow_html=True)

if mode == "ANALYSE INDIVIDUELLE":
    ticker_input = st.text_input(
        "",
        placeholder="Rechercher un actif : AAPL, MSFT, LVMH.PA, CW8.PA...",
        label_visibility="collapsed",
        key="analysis_ticker"
    ).upper().strip()

    if ticker_input:
        with st.spinner("Acquisition des donnees en cours..."):
            info = fetch_info_with_retry(ticker_input)

            if not info:
                st.error("Impossible de recuperer les donnees. Verifie le ticker ou reessaie dans quelques minutes.")
                st.stop()

            nom = info.get("longName", info.get("shortName", ticker_input)).upper()
            devise = info.get("currency", "USD").upper()
            fx_rate = get_fx_rate(devise)
            is_etf = info.get("quoteType") == "ETF" or "totalAssets" in info

            st.markdown(
                f"<h2>{nom} <span style='color:#2f80ff; font-size:1.05rem;'>// {ticker_input}</span></h2>",
                unsafe_allow_html=True
            )

            tabs = st.tabs(["FONDAMENTAUX", "TECHNIQUE", "EVOLUTION METRIQUES", "PRESSE"])

            with tabs[0]:
                if is_etf:
                    data = extract_etf_data(info, ticker_input, fx_rate)

                    if data["AUM"] and data["AUM"] < 100:
                        st.warning("Liquidite faible : AUM inferieur a 100 M€.")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        render_metric_card("Score ETF", format_metric(data["Score"], "/100"), tone_score(data["Score"]))
                    with c2:
                        render_metric_card("Net Asset Value", format_metric(data["Prix"], "€"))
                    with c3:
                        render_metric_card("Total Expense Ratio", format_metric(data["TER"], "%"), tone_lower(data["TER"], 0.30))
                    with c4:
                        render_metric_card("Assets Under Management", format_metric(data["AUM"], "M€"), tone_higher(data["AUM"], 100))

                    c5, c6, c7 = st.columns(3)
                    with c5:
                        render_metric_card("Regime fiscal", data["PEA"], "positive" if data["PEA"] == "ELIGIBLE PEA" else None)
                    with c6:
                        render_metric_card("Politique dividende", data["Distribution"])
                    with c7:
                        render_metric_card("Replication", data["Replication"], "positive" if data["Replication"] == "PHYSIQUE" else None)

                else:
                    data = extract_stock_data(info, fx_rate)
                    score_tone = tone_score(data["Score"])

                    c1, c2, c3 = st.columns([1.15, 2, 2])

                    with c1:
                        st.markdown(
                            f"""
                            <div class="score-container metric-{score_tone}">
                                <div class="score-title">Score d'integrite</div>
                                <div class="score-val metric-{score_tone}">{data["Score"]}</div>
                                <div class="score-caption">Notation fondamentale sur 100</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with c2:
                        render_metric_card("Prix marche", format_metric(data["Prix"], "€"))
                        render_metric_card(
                            "Consensus target",
                            f"{format_metric(data['Target'], '€')} // {data['Reco']}",
                            tone_target(data["Target"], data["Prix"])
                        )

                    with c3:
                        render_metric_card("Capitalisation", format_metric(data["MarketCap"], "M€"))
                        render_metric_card("Croissance CA", format_metric(data["Rev_Growth"], "%"), tone_higher(data["Rev_Growth"], 0))

                    st.markdown("<hr>", unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.markdown("#### Valorisation")
                        render_metric_card("PER trailing", format_metric(data["PER_Actuel"], "x"), tone_between(data["PER_Actuel"], 0, 25))
                        render_metric_card("PER forward", format_metric(data["PER_Futur"], "x"), tone_between(data["PER_Futur"], 0, 25))
                        render_metric_card("Price / Sales", format_metric(data["PS"], "x"), tone_between(data["PS"], 0, 6))
                        render_metric_card("Price / Book", format_metric(data["PB"], "x"), tone_between(data["PB"], 0, 5))
                        render_metric_card("EV / EBITDA", format_metric(data["EV_EBITDA"], "x"), tone_between(data["EV_EBITDA"], 0, 15))
                        render_metric_card("Valeur Graham", format_metric(data["Graham"], "€"), tone_graham(data["Graham"], data["Prix"]))

                    with col_b:
                        st.markdown("#### Rentabilite")
                        render_metric_card("Marge brute", format_metric(data["Marge_Brute"], "%"), tone_higher(data["Marge_Brute"], 0))
                        render_metric_card("Marge operationnelle", format_metric(data["Marge_Op"], "%"), tone_higher(data["Marge_Op"], 0))
                        render_metric_card("Marge nette", format_metric(data["Marge_Nette"], "%"), tone_higher(data["Marge_Nette"], 0))
                        render_metric_card("ROE", format_metric(data["ROE"], "%"), tone_higher(data["ROE"], 0))
                        render_metric_card("ROA", format_metric(data["ROA"], "%"), tone_higher(data["ROA"], 0))
                        render_metric_card("Payout ratio", format_metric(data["Payout"], "%"), tone_between(data["Payout"], 0, 70))

                    with col_c:
                        st.markdown("#### Bilan")
                        render_metric_card("Dette nette globale", format_metric(data["Dette_Nette"], "M€"), tone_lower(data["Dette_Nette"], 0))
                        render_metric_card("EBITDA", format_metric(data["EBITDA"], "M€"), tone_higher(data["EBITDA"], 0))
                        render_metric_card("Levier dette / EBITDA", format_metric(data["Levier"], "x"), tone_leverage(data["Levier"]))
                        render_metric_card("Current ratio", format_metric(data["Current_Ratio"]), tone_higher(data["Current_Ratio"], 1.2))
                        render_metric_card("Quick ratio", format_metric(data["Quick_Ratio"]), tone_higher(data["Quick_Ratio"], 1.0))
                        render_metric_card("Debt / Equity", format_metric(data["Debt_Equity"], "%"), tone_lower(data["Debt_Equity"], 100))

            with tabs[1]:
                tk_obj = yf.Ticker(ticker_input)
                hist = tk_obj.history(period="5y")

                if len(hist) > 200:
                    hist["Close_EUR"] = hist["Close"] * fx_rate
                    hist["SMA50"] = hist["Close_EUR"].rolling(50).mean()
                    hist["SMA200"] = hist["Close_EUR"].rolling(200).mean()
                    hist["RSI"] = calculer_rsi(hist["Close"])

                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        row_heights=[0.72, 0.28],
                        vertical_spacing=0.04
                    )

                    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close_EUR"], name="Prix", line=dict(color="#f5f7f2", width=2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="MM50", line=dict(color="#2f80ff", width=1.3)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="MM200", line=dict(color="#53ff9a", width=1.3)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], name="RSI", line=dict(color="#b8c0c0", width=1.2)), row=2, col=1)

                    fig.add_hline(y=70, line_color="#ff5757", line_width=1, row=2, col=1)
                    fig.add_hline(y=30, line_color="#53ff9a", line_width=1, row=2, col=1)

                    fig.update_layout(
                        height=650,
                        template="plotly_dark",
                        margin=dict(l=0, r=0, t=30, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(13,17,19,0.72)",
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
                        xaxis2=dict(showgrid=False),
                        yaxis2=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Serie temporelle insuffisante.")

            with tabs[2]:
                if is_etf:
                    st.info("L'evolution des metriques fondamentales est disponible pour les actions. Pour les ETF, utilise l'onglet Technique.")
                else:
                    metrics_df = get_financial_metric_history(ticker_input, fx_rate)

                    if metrics_df.empty:
                        st.error("Donnees financieres trimestrielles indisponibles pour cet actif.")
                    else:
                        available_metrics = list(metrics_df.columns)
                        default_metrics = [
                            m for m in ["Chiffre d'affaires", "Resultat net", "EBITDA", "Dette nette"]
                            if m in available_metrics
                        ]

                        selected_metrics = st.multiselect("Metriques a afficher", available_metrics, default=default_metrics)

                        if selected_metrics:
                            fig_metrics = go.Figure()
                            colors = ["#2f80ff", "#53ff9a", "#ffd166", "#ff5757", "#f5f7f2", "#9b8cff"]

                            for i, metric in enumerate(selected_metrics):
                                fig_metrics.add_trace(
                                    go.Scatter(
                                        x=metrics_df.index,
                                        y=metrics_df[metric],
                                        mode="lines+markers",
                                        name=metric,
                                        line=dict(width=2.4, color=colors[i % len(colors)])
                                    )
                                )

                            fig_metrics.update_layout(
                                height=560,
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(13,17,19,0.72)",
                                margin=dict(l=0, r=0, t=30, b=0),
                                xaxis=dict(showgrid=False),
                                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", title="M€ / % selon metrique"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )

                            st.plotly_chart(fig_metrics, use_container_width=True)

                        st.dataframe(format_dataframe(metrics_df.sort_index(ascending=False)), use_container_width=True)

            with tabs[3]:
                st.markdown(generate_consensus_and_verdict(data, is_etf), unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("#### Presse financiere")

                news = get_press_news(ticker_input, nom)

                if news:
                    for n in news:
                        st.markdown(
                            f"""
                            <div style="background:rgba(13,17,19,0.88); padding:18px; border:1px solid rgba(255,255,255,0.10); border-radius:18px; margin-bottom:14px;">
                                <a href="{n['link']}" target="_blank" style="color:#f5f7f2; font-weight:800; text-decoration:none; font-size:1rem;">{n['title']}</a><br>
                                <span style="color:#90999a; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; display:inline-block; margin-top:10px;">{n['publisher']} // {n['published']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Flux de presse indisponible.")

elif mode == "TOP SELECTION":
    st.markdown("#### Selection algorithmique")

    c1, c2 = st.columns([1, 1])

    with c1:
        asset_type = st.selectbox("Univers", ["ACTIONS", "SMALL CAPS", "ETF"])

    with c2:
        top_limit = st.slider("Nombre de resultats", 5, 20, 10)

    st.caption(f"Actualisation live a chaque rechargement de page : {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")

    with st.spinner("Scan live du marche en cours..."):
        ranking = rank_universe(asset_type, top_limit)

    if ranking.empty:
        st.error("Aucune donnee exploitable pour cet univers.")
    else:
        ranking = numeric_df_for_display(ranking)
        best = ranking.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            render_metric_card("Meilleur actif", f"{best['Ticker']}")

        with c2:
            render_metric_card("Score", format_metric(best["Score"], "/100"), tone_score(best["Score"]))

        with c3:
            render_metric_card("Prix", format_metric(best.get("Prix €"), "€"))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(format_dataframe(ranking), use_container_width=True, height=430)

        render_open_asset_buttons(ranking, "top_selection_open")

        fig_rank = go.Figure()

        fig_rank.add_trace(
            go.Bar(
                x=ranking["Ticker"],
                y=ranking["Score"],
                marker=dict(
                    color=ranking["Score"],
                    colorscale=[
                        [0, "#ff5757"],
                        [0.5, "#ffd166"],
                        [1, "#53ff9a"]
                    ],
                    cmin=0,
                    cmax=100
                ),
                text=ranking["Score"].round(0),
                textposition="outside"
            )
        )

        fig_rank.update_layout(
            height=420,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,19,0.72)",
            margin=dict(l=0, r=0, t=24, b=0),
            yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.07)", title="Score /100"),
            xaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig_rank, use_container_width=True)

elif mode == "Comparer":
    st.markdown("#### Comparer")

    tickers_input = st.text_area(
        "",
        placeholder="Entre tes tickers separes par une virgule : AAPL, MSFT, LVMH.PA, CW8.PA",
        label_visibility="collapsed",
        height=90
    ).upper()

    c1, c2, c3 = st.columns(3)

    with c1:
        sort_metric = st.selectbox("Tri principal", ["SCORE", "PRIX (€)", "PER", "ROE (%)", "MARGE NETTE (%)"])

    with c2:
        min_score = st.slider("Score minimum", 0, 100, 0)

    with c3:
        show_chart = st.selectbox("Vue graphique", ["Score", "Score vs PER", "Score vs marge nette"])

    if tickers_input:
        if st.button("Comparer les actifs"):
            with st.spinner("Acquisition et comparaison des donnees..."):
                t_list = [t.strip().upper() for t in tickers_input.replace("\n", ",").split(",") if t.strip()]
                res = []

                progress_bar = st.progress(0)

                for i, t in enumerate(t_list):
                    try:
                        info = fetch_info_with_retry(t)

                        if not info:
                            progress_bar.progress((i + 1) / len(t_list))
                            continue

                        fx = get_fx_rate(info.get("currency", "USD"))
                        is_etf = info.get("quoteType") == "ETF" or "totalAssets" in info

                        if is_etf:
                            d = extract_etf_data(info, t, fx)

                            res.append({
                                "TICKER": t,
                                "NOM": info.get("shortName", t),
                                "TYPE": "ETF",
                                "SCORE": d["Score"],
                                "PRIX (€)": d["Prix"],
                                "MARKET CAP / AUM (M€)": d["AUM"],
                                "PER": None,
                                "ROE (%)": None,
                                "MARGE NETTE (%)": None,
                                "DETTE/EBITDA": None,
                                "FRAIS (%)": d["TER"]
                            })
                        else:
                            d = extract_stock_data(info, fx)

                            res.append({
                                "TICKER": t,
                                "NOM": info.get("shortName", t),
                                "TYPE": "EQUITY",
                                "SCORE": d["Score"],
                                "PRIX (€)": d["Prix"],
                                "MARKET CAP / AUM (M€)": d["MarketCap"],
                                "PER": d["PER_Actuel"],
                                "ROE (%)": d["ROE"],
                                "MARGE NETTE (%)": d["Marge_Nette"],
                                "DETTE/EBITDA": d["Levier"] if isinstance(d["Levier"], (int, float)) else None,
                                "FRAIS (%)": None
                            })
                    except Exception:
                        pass

                    progress_bar.progress((i + 1) / len(t_list))

                progress_bar.empty()

                if res:
                    df = pd.DataFrame(res)
                    df = numeric_df_for_display(df)
                    df = df[df["SCORE"] >= min_score]

                    if df.empty:
                        st.warning("Aucun actif ne passe le filtre de score minimum.")
                        st.stop()

                    if sort_metric in df.columns:
                        df = df.sort_values(by=sort_metric, ascending=False, na_position="last")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        render_metric_card("Actifs compares", str(len(df)))
                    with c2:
                        render_metric_card("Meilleur score", format_metric(df["SCORE"].max(), "/100"), tone_score(df["SCORE"].max()))
                    with c3:
                        render_metric_card("Score moyen", format_metric(df["SCORE"].mean(), "/100"), tone_score(df["SCORE"].mean()))
                    with c4:
                        render_metric_card("Leader", str(df.iloc[0]["TICKER"]))

                    st.dataframe(format_dataframe(df), use_container_width=True, height=460)

                    button_df = df.rename(columns={"TICKER": "Ticker", "NOM": "Nom"})
                    render_open_asset_buttons(button_df, "comparer_open")

                    if show_chart == "Score":
                        fig = go.Figure()
                        fig.add_trace(
                            go.Bar(
                                x=df["TICKER"],
                                y=df["SCORE"],
                                marker=dict(
                                    color=df["SCORE"],
                                    colorscale=[
                                        [0, "#ff5757"],
                                        [0.5, "#ffd166"],
                                        [1, "#53ff9a"]
                                    ],
                                    cmin=0,
                                    cmax=100
                                )
                            )
                        )
                        fig.update_yaxes(range=[0, 100], title="Score /100")

                    elif show_chart == "Score vs PER":
                        chart_df = df.dropna(subset=["PER"])
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df["PER"],
                                y=chart_df["SCORE"],
                                mode="markers+text",
                                text=chart_df["TICKER"],
                                textposition="top center",
                                marker=dict(size=16, color="#2f80ff", line=dict(color="#f5f7f2", width=1))
                            )
                        )
                        fig.update_xaxes(title="PER")
                        fig.update_yaxes(range=[0, 100], title="Score /100")

                    else:
                        chart_df = df.dropna(subset=["MARGE NETTE (%)"])
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=chart_df["MARGE NETTE (%)"],
                                y=chart_df["SCORE"],
                                mode="markers+text",
                                text=chart_df["TICKER"],
                                textposition="top center",
                                marker=dict(size=16, color="#2f80ff", line=dict(color="#f5f7f2", width=1))
                            )
                        )
                        fig.update_xaxes(title="Marge nette (%)")
                        fig.update_yaxes(range=[0, 100], title="Score /100")

                    fig.update_layout(
                        height=440,
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(13,17,19,0.72)",
                        margin=dict(l=0, r=0, t=24, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.07)")
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    csv = df.to_csv(index=False).encode("utf-8")

                    st.download_button(
                        "Exporter la matrice CSV",
                        data=csv,
                        file_name="alpha_matrix.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Echec total de l'extraction.")
