import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import urllib.parse
import time
import html
import textwrap
from numbers import Real

try:
    import feedparser
except ImportError:
    feedparser = None


st.set_page_config(
    page_title="Analyseur Bourse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --bg:#050607;
        --text:#f5f7f2;
        --muted:#90999a;
        --line:rgba(255,255,255,.10);
        --accent:#2f80ff;
        --accent-soft:rgba(47,128,255,.20);
        --green:#53ff9a;
        --red:#ff5757;
        --yellow:#ffd166;
    }

    html, body, [class*="css"] {
        font-family:"Avenir Next","Helvetica Neue",Helvetica,Arial,sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 8%, rgba(47,128,255,.34), transparent 31%),
            radial-gradient(circle at 86% 5%, rgba(30,95,255,.30), transparent 35%),
            linear-gradient(180deg,#07142a 0%,#050914 44%,#030405 100%);
        color:var(--text);
    }

    .block-container {
        padding-top:5.2rem!important;
        padding-bottom:4rem!important;
        max-width:1280px;
    }

    [data-testid="stHeader"] {
        background:rgba(5,8,14,.74);
        backdrop-filter:blur(18px);
        border-bottom:1px solid rgba(255,255,255,.06);
    }

    h1,h2,h3,h4,h5 {
        color:var(--text)!important;
        font-weight:700!important;
        letter-spacing:0!important;
        text-transform:none!important;
    }

    .terminal-shell {
        background:
            radial-gradient(circle at 80% 20%, rgba(47,128,255,.24), transparent 35%),
            linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,.02)),
            rgba(13,17,19,.86);
        border:1px solid rgba(255,255,255,.12);
        border-radius:22px;
        padding:22px 24px;
        box-shadow:0 26px 80px rgba(0,0,0,.42);
        margin-bottom:24px;
    }

    .terminal-topline {
        display:flex;
        align-items:center;
        justify-content:flex-end;
        gap:16px;
        margin-bottom:14px;
    }

    .status-pill {
        color:#f5f7f2;
        background:var(--accent);
        border-radius:999px;
        padding:7px 12px;
        font-size:.72rem;
        font-weight:900;
        text-transform:uppercase;
        letter-spacing:.06em;
        white-space:nowrap;
        box-shadow:0 10px 30px rgba(47,128,255,.35);
    }

    .hero-title {
        font-size:clamp(2.2rem,5vw,4.8rem);
        line-height:.95;
        font-weight:850;
        color:var(--text);
        margin:0;
    }

    .hero-subtitle {
        max-width:820px;
        color:var(--muted);
        font-size:1rem;
        line-height:1.55;
        margin-top:14px;
    }

    .element-container,[data-testid="column"],.stColumn {
        overflow:visible!important;
    }

    .fin-card {
        position:relative;
        overflow:visible;
        background:
            linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.018)),
            rgba(13,17,19,.92);
        border:1px solid var(--line);
        padding:18px;
        margin-bottom:16px;
        border-radius:18px;
        box-shadow:0 18px 46px rgba(0,0,0,.24);
        min-height:112px;
        cursor:default;
    }

    .fin-card:hover {
        border-color:rgba(47,128,255,.48);
        background:
            linear-gradient(180deg,rgba(47,128,255,.11),rgba(255,255,255,.018)),
            rgba(13,17,19,.96);
    }

    .fin-card[data-tooltip]:hover::after {
        content:attr(data-tooltip);
        position:absolute;
        z-index:999999;
        left:14px;
        top:calc(100% + 10px);
        width:min(440px,82vw);
        padding:13px 14px;
        border-radius:14px;
        background:rgba(3,7,12,.98);
        border:1px solid rgba(47,128,255,.52);
        box-shadow:0 20px 55px rgba(0,0,0,.55);
        color:#f5f7f2;
        font-size:.82rem;
        line-height:1.45;
        font-weight:650;
        white-space:normal;
        pointer-events:none;
    }

    .fin-card.metric-positive {
        border-color:rgba(83,255,154,.42);
        background:
            linear-gradient(180deg,rgba(83,255,154,.08),rgba(255,255,255,.018)),
            rgba(13,17,19,.94);
    }

    .fin-card.metric-negative {
        border-color:rgba(255,87,87,.42);
        background:
            linear-gradient(180deg,rgba(255,87,87,.08),rgba(255,255,255,.018)),
            rgba(13,17,19,.94);
    }

    .fin-title {
        color:var(--muted);
        font-size:.72rem;
        font-weight:800;
        letter-spacing:.08em;
        text-transform:uppercase;
        margin-bottom:12px;
    }

    .fin-val {
        color:var(--text);
        font-size:1.45rem;
        font-weight:850;
        line-height:1.15;
    }

    .fin-val.metric-positive { color:var(--green); }
    .fin-val.metric-negative { color:var(--red); }

    .fin-na {
        color:#5f6869;
        font-size:1.2rem;
    }

    .fin-cash {
        color:var(--green);
        font-size:1.05rem;
        font-weight:900;
    }

    .score-container {
        position:relative;
        overflow:hidden;
        text-align:left;
        padding:24px;
        background:
            radial-gradient(circle at 80% 20%,rgba(47,128,255,.32),transparent 34%),
            linear-gradient(145deg,#17294a,#07142a 72%);
        border:1px solid rgba(47,128,255,.42);
        border-radius:24px;
        min-height:240px;
        box-shadow:0 28px 70px rgba(0,0,0,.34);
    }

    .score-container.metric-positive { border-color:rgba(83,255,154,.42); }
    .score-container.metric-negative { border-color:rgba(255,87,87,.42); }

    .score-title {
        color:rgba(245,247,242,.72);
        font-size:.75rem;
        font-weight:900;
        text-transform:uppercase;
        letter-spacing:.08em;
    }

    .score-val {
        color:var(--text);
        font-size:5.4rem;
        line-height:.95;
        font-weight:900;
        margin-top:22px;
    }

    .score-val.metric-positive { color:var(--green); }
    .score-val.metric-negative { color:var(--red); }

    .score-caption {
        color:rgba(245,247,242,.72);
        font-size:.86rem;
        margin-top:12px;
    }

    .metric-help-grid {
        display:flex;
        flex-wrap:wrap;
        gap:10px;
        margin:8px 0 18px 0;
        overflow:visible;
    }

    .metric-help {
        position:relative;
        display:inline-flex;
        align-items:center;
        padding:8px 12px;
        border-radius:999px;
        background:rgba(47,128,255,.14);
        border:1px solid rgba(47,128,255,.38);
        color:#f5f7f2;
        font-size:.8rem;
        font-weight:850;
        cursor:default;
    }

    .metric-help[data-tooltip]:hover::after {
        content:attr(data-tooltip);
        position:absolute;
        z-index:999999;
        left:0;
        top:calc(100% + 10px);
        width:min(440px,82vw);
        padding:13px 14px;
        border-radius:14px;
        background:rgba(3,7,12,.98);
        border:1px solid rgba(47,128,255,.52);
        box-shadow:0 20px 55px rgba(0,0,0,.55);
        color:#f5f7f2;
        font-size:.82rem;
        line-height:1.45;
        font-weight:650;
        white-space:normal;
    }

    .expert-verdict {
        border:1px solid var(--line);
        border-left:6px solid #777;
        border-radius:18px;
        padding:20px;
        background:rgba(13,17,19,.88);
        margin-bottom:24px;
    }

    .buy-verdict { border-left-color:var(--green); }
    .hold-verdict { border-left-color:var(--yellow); }
    .sell-verdict { border-left-color:var(--red); }

    .expert-verdict h4 {
        margin:0 0 8px 0;
        color:var(--text)!important;
    }

    .expert-verdict p {
        color:#b8c0c0;
        line-height:1.6;
        font-size:.95rem;
        margin:0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap:8px;
        border-bottom:1px solid var(--line);
        margin-bottom:18px;
    }

    .stTabs [data-baseweb="tab"] {
        background:rgba(255,255,255,.04);
        border:1px solid rgba(255,255,255,.08);
        border-bottom:none;
        border-radius:16px 16px 0 0;
        padding:13px 20px;
        color:var(--muted);
        font-weight:850;
    }

    .stTabs [aria-selected="true"] {
        background:var(--accent-soft);
        color:var(--text);
        border-color:rgba(47,128,255,.52);
    }

    .stRadio [role="radiogroup"] {
        background:rgba(13,17,19,.78);
        border:1px solid var(--line);
        border-radius:18px;
        padding:8px;
        gap:8px;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        background:rgba(13,17,19,.96)!important;
        color:var(--text)!important;
        border:1px solid rgba(255,255,255,.12)!important;
        border-radius:16px!important;
        min-height:48px;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color:rgba(47,128,255,.75)!important;
        box-shadow:0 0 0 3px rgba(47,128,255,.18)!important;
    }

    .stButton button,
    .stDownloadButton button {
        background:var(--accent);
        color:#f5f7f2;
        border:0;
        border-radius:999px;
        padding:.75rem 1.25rem;
        font-weight:950;
        letter-spacing:.02em;
        text-transform:uppercase;
        box-shadow:0 12px 30px rgba(47,128,255,.28);
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        background:#5b9dff;
        color:#fff;
    }

    .stDataFrame {
        border:1px solid var(--line);
        border-radius:18px;
        overflow:hidden;
        background:rgba(13,17,19,.9);
    }

    hr {
        border:none;
        border-top:1px solid var(--line);
        margin:30px 0;
    }

    @media(max-width:768px) {
        .block-container { padding-top:5.8rem!important; }
        .terminal-shell { padding:18px; border-radius:18px; }
        .hero-title { font-size:2.45rem; }
        .score-val { font-size:4rem; }
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

TICKER_ALIASES = {
    "2FE.MU": ["RACE.MI", "RACE"],
    "2FE.F": ["RACE.MI", "RACE"],
    "2FE.BE": ["RACE.MI", "RACE"],
    "2FE.DE": ["RACE.MI", "RACE"],
}

SECTOR_PEERS = {
    "TECHNOLOGY": ["MSFT", "AAPL", "GOOGL", "NVDA", "META", "ORCL", "ADBE"],
    "COMMUNICATION SERVICES": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ"],
    "CONSUMER CYCLICAL": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "RACE.MI"],
    "CONSUMER DEFENSIVE": ["PG", "KO", "PEP", "COST", "WMT", "UL"],
    "HEALTHCARE": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "TMO"],
    "FINANCIAL SERVICES": ["JPM", "BAC", "V", "MA", "MS", "GS"],
    "ENERGY": ["XOM", "CVX", "TTE.PA", "SHEL", "COP", "BP"],
    "INDUSTRIALS": ["AIR.PA", "CAT", "GE", "HON", "UPS", "RTX"],
    "BASIC MATERIALS": ["LIN", "RIO", "BHP", "NEM", "FCX", "AI.PA"],
    "UTILITIES": ["NEE", "DUK", "SO", "AEP", "D", "ENGI.PA"],
    "REAL ESTATE": ["PLD", "AMT", "EQIX", "O", "SPG", "WELL"],
    "LUXURY": ["RACE.MI", "MC.PA", "RMS.PA", "KER.PA", "OR.PA", "RI.PA"]
}

MODULES = ["ANALYSE INDIVIDUELLE", "TOP SÉLECTION", "COMPARER"]

if "module_choice" not in st.session_state:
    st.session_state.module_choice = "ANALYSE INDIVIDUELLE"

if st.session_state.module_choice in ["TOP SELECTION", "TOP SÉLECTION"]:
    st.session_state.module_choice = "TOP SÉLECTION"

if st.session_state.module_choice == "Comparer":
    st.session_state.module_choice = "COMPARER"

if st.session_state.module_choice not in MODULES:
    st.session_state.module_choice = "ANALYSE INDIVIDUELLE"

if "analysis_ticker" not in st.session_state:
    st.session_state.analysis_ticker = ""

if "compare_raw_df" not in st.session_state:
    st.session_state.compare_raw_df = None


RATIO_TOOLTIPS = {
    "PER": "PER - Prix vs profits. Calcul : prix de l'action / bénéfice par action. Repère : 10 à 20. Tech accepté jusqu'à 30+. Cher si > 35.",
    "PEG": "PEG - PER ajusté à la croissance. Calcul : PER / croissance annuelle des profits. Repère : inférieur ou égal à 1. Sous-évalué si < 1. Cher si > 2.",
    "PRICE / BOOK": "P/B - Prix vs valeur du patrimoine. Calcul : prix de l'action / valeur comptable par action. Repère : 1 à 2. Très bas si < 1. Cher si > 3.",
    "PRICE / SALES": "P/S - Prix vs chiffre d'affaires. Calcul : capitalisation boursière / chiffre d'affaires. Repère : < 2. Surévalué si > 5.",
    "EV / EBITDA": "EV / EBITDA - Valeur totale avec dette vs rentabilité brute. Calcul : valeur d'entreprise / EBITDA. Repère : < 10. Plus c'est bas, mieux c'est.",
    "MARGE BRUTE": "Marge brute - Rentabilité avant charges opérationnelles. Calcul : chiffre d'affaires moins coût des ventes, divisé par chiffre d'affaires, puis x 100. Repère : plus elle est élevée, mieux c'est, à comparer au secteur.",
    "MARGE OPÉRATIONNELLE": "Marge opérationnelle - Efficacité du business. Calcul : résultat opérationnel / chiffre d'affaires x 100. Repère : > 15%.",
    "MARGE NETTE": "Marge nette - Bénéfice réel restant. Calcul : résultat net / chiffre d'affaires x 100. Repère : > 10%. Luxe et Tech visent > 20%.",
    "ROE": "ROE - Rendement de l'argent des actionnaires. Calcul : résultat net / capitaux propres x 100. Repère : > 15%.",
    "ROA": "ROA - Rentabilité de tous les actifs. Calcul : résultat net / total des actifs x 100. Repère : > 5%.",
    "LEVIER DETTE / EBITDA": "Dette nette / EBITDA - Années théoriques pour rembourser la dette. Calcul : dette nette / EBITDA. Repère : < 2,5x. Danger si > 4x.",
    "DETTE NETTE": "Dette nette - Dette après déduction du cash. Calcul : dette totale - trésorerie.",
    "DEBT / EQUITY": "Dette / capitaux propres - Poids des banques vs actionnaires. Calcul : dette totale / capitaux propres x 100. Repère : < 100%.",
    "CURRENT RATIO": "Current Ratio - Liquidité court terme. Calcul : actifs courants / passifs courants. Repère : > 1,5. Alerte si < 1.",
    "QUICK RATIO": "Quick Ratio - Liquidité immédiate. Calcul : actifs courants hors stocks / passifs courants. Repère : > 1.",
    "PAYOUT RATIO": "Payout Ratio - Part du profit versée en dividende. Calcul : dividendes / résultat net x 100. Repère : 30% à 60%. Danger de coupure si > 80%.",
    "DIVIDEND YIELD": "Rendement du dividende - Rendement annuel du dividende. Calcul : dividende annuel par action / prix de l'action x 100. Repère : 2% à 5%. Piège possible si > 8%.",
    "FCF YIELD": "Rendement FCF - Rendement du cash réel disponible. Calcul : free cash flow / capitalisation boursière x 100. Repère : > 5%.",
    "FCF": "Free cash flow - Cash réel restant après investissements. Calcul : cash-flow opérationnel - dépenses d'investissement. Plus il est positif et régulier, mieux c'est.",
    "EBITDA": "EBITDA - Rentabilité brute avant amortissements, financement et impôts. Calcul : résultat opérationnel + amortissements et dépréciations. Sert à mesurer la performance pure de l'activité."
}

METRIC_TOOLTIPS = {
    "Chiffre d'affaires": "Chiffre d'affaires - Ventes totales de l'entreprise sur la période. Calcul : somme des revenus générés par l'activité.",
    "Résultat brut": "Résultat brut - Profit après coût direct des ventes. Calcul : chiffre d'affaires - coût des ventes.",
    "EBITDA": "EBITDA - Rentabilité brute avant amortissements, financement et impôts. Calcul : résultat opérationnel + amortissements et dépréciations.",
    "Résultat opérationnel": "Résultat opérationnel - Profit du cœur d'activité. Calcul : chiffre d'affaires - charges opérationnelles.",
    "Résultat net": "Résultat net - Bénéfice final pour les actionnaires. Calcul : résultat opérationnel - intérêts - impôts - éléments exceptionnels.",
    "Marge nette %": "Marge nette - Bénéfice réel restant. Calcul : résultat net / chiffre d'affaires x 100.",
    "Cash": "Cash - Trésorerie disponible. Calcul : cash et équivalents de trésorerie au bilan.",
    "Dette totale": "Dette totale - Ensemble des dettes financières. Calcul : dette court terme + dette long terme.",
    "Dette nette": "Dette nette - Dette après déduction du cash. Calcul : dette totale - trésorerie.",
    "Free cash flow": "Free cash flow - Cash réel restant après investissements. Calcul : cash-flow opérationnel - dépenses d'investissement.",
    "Cash-flow opérationnel": "Cash-flow opérationnel - Cash généré par l'activité courante.",
    "Capex": "Capex - Dépenses d'investissement dans les actifs long terme.",
    "Rendement FCF %": "Rendement FCF - Free cash flow / capitalisation boursière x 100. Repère : > 5%."
}


def get_ratio_tooltip(title):
    normalized = str(title).upper()
    aliases = {
        "EV / EBITDA": "EV / EBITDA",
        "LEVIER DETTE": "LEVIER DETTE / EBITDA",
        "DETTE / EBITDA": "LEVIER DETTE / EBITDA",
        "PER TRAILING": "PER",
        "PER FORWARD": "PER",
        "PRICE / BOOK": "PRICE / BOOK",
        "PRICE / SALES": "PRICE / SALES",
        "MARGE BRUTE": "MARGE BRUTE",
        "MARGE OP": "MARGE OPÉRATIONNELLE",
        "MARGE OPÉRATIONNELLE": "MARGE OPÉRATIONNELLE",
        "MARGE OPERATIONNELLE": "MARGE OPÉRATIONNELLE",
        "MARGE NETTE": "MARGE NETTE",
        "PAYOUT": "PAYOUT RATIO",
        "DIVIDEND": "DIVIDEND YIELD",
        "RENDEMENT DU DIVIDENDE": "DIVIDEND YIELD",
        "RENDEMENT FCF": "FCF YIELD",
        "FCF YIELD": "FCF YIELD",
        "FREE CASH FLOW": "FCF",
        "DEBT / EQUITY": "DEBT / EQUITY",
        "EBITDA": "EBITDA"
    }

    for alias, key in aliases.items():
        if alias in normalized:
            return RATIO_TOOLTIPS.get(key)

    for key, tooltip in RATIO_TOOLTIPS.items():
        if key in normalized:
            return tooltip

    return None


def get_metric_tooltip(metric_name):
    return METRIC_TOOLTIPS.get(str(metric_name), None)


def has_value(val):
    if val is None or val == "":
        return False
    try:
        if pd.isna(val):
            return False
    except Exception:
        pass
    return True


def info_completeness(info):
    if not info:
        return 0

    keys = [
        "currentPrice", "regularMarketPrice", "previousClose", "marketCap",
        "trailingPE", "forwardPE", "priceToSalesTrailing12Months", "priceToBook",
        "enterpriseToEbitda", "grossMargins", "operatingMargins", "profitMargins",
        "returnOnEquity", "returnOnAssets", "totalDebt", "totalCash", "ebitda",
        "freeCashflow", "currentRatio", "quickRatio", "debtToEquity",
        "revenueGrowth", "earningsGrowth", "payoutRatio", "dividendYield"
    ]

    return sum(1 for key in keys if has_value(info.get(key)))


def resolve_analysis_ticker(ticker_symbol):
    ticker = ticker_symbol.upper().strip()
    candidates = [ticker] + TICKER_ALIASES.get(ticker, [])

    best_info = None
    best_ticker = ticker
    best_score = -1

    for candidate in candidates:
        info = fetch_info_with_retry(candidate)
        score = info_completeness(info)

        if score > best_score:
            best_info = info
            best_ticker = candidate
            best_score = score

    if not best_info:
        return None, ticker, None

    note = None
    if best_ticker != ticker:
        note = f"Données fondamentales enrichies via {best_ticker}, car {ticker} est une cotation secondaire avec données Yahoo incomplètes."

    return best_info, best_ticker, note


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


def safe_float(val, multiplier=1.0, precision=2):
    if val is None or val == "":
        return None
    try:
        if pd.isna(val):
            return None
        return round(float(val) * multiplier, precision)
    except Exception:
        return None


def safe_percent(val, precision=2):
    if val is None or val == "":
        return None
    try:
        if pd.isna(val):
            return None

        number = float(val)

        if abs(number) <= 1:
            number *= 100

        return round(number, precision)
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
    formatted = f"{val:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} {suffix}".strip()


def tone_score(value):
    if not is_num(value):
        return None
    return "positive" if value >= 50 else "negative"


def tone_higher(value, threshold=0):
    if not is_num(value) or not is_num(threshold):
        return None
    return "positive" if value > threshold else "negative"


def tone_lower(value, threshold):
    if not is_num(value) or not is_num(threshold):
        return None
    return "positive" if value < threshold else "negative"


def tone_between(value, low, high):
    if not is_num(value) or not is_num(low) or not is_num(high):
        return None
    return "positive" if low < value < high else "negative"


def tone_leverage(value):
    if isinstance(value, str) and value.lower() == "cash positif":
        return "positive"
    if not is_num(value):
        return None
    return "positive" if value < 2.5 else "negative"


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


def render_metric_help_chips(metric_names):
    chips = []

    for metric in metric_names:
        tooltip = get_metric_tooltip(metric)
        if tooltip:
            chips.append(
                f'<span class="metric-help" data-tooltip="{html.escape(tooltip, quote=True)}">{html.escape(str(metric))}</span>'
            )

    if chips:
        st.markdown(
            f'<div class="metric-help-grid">{"".join(chips)}</div>',
            unsafe_allow_html=True
        )


def calculer_rsi(data, window=14):
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def compute_cagr(first, last, years):
    if not is_num(first) or not is_num(last) or not is_num(years):
        return None
    if first <= 0 or last <= 0 or years <= 0:
        return None
    return ((last / first) ** (1 / years) - 1) * 100


def numeric_df_for_display(df):
    clean = df.copy()
    text_cols = ["Symbole", "SYMBOLE", "Nom", "NOM", "Catégorie", "CATÉGORIE", "Régime", "Secteur"]
    for col in clean.columns:
        if col not in text_cols:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
    return clean


def cell_color(value, col_name):
    if not is_num(value):
        return ""

    col = col_name.upper()

    if "NOTE" in col:
        good = value >= 50
    elif "PER" in col:
        good = 0 < value < 25
    elif "ROE" in col or "MARGE" in col:
        good = value > 0
    elif "DETTE/EBITDA" in col:
        good = value < 2.5
    elif "FRAIS" in col:
        good = value < 0.30
    elif "FCF" in col:
        good = value > 0
    else:
        return ""

    color = "#53ff9a" if good else "#ff5757"
    return f"color: {color}; font-weight: 900;"


def format_dataframe(df):
    formatters = {}

    for col in df.columns:
        col_upper = col.upper()
        if col_upper == "NOTE":
            formatters[col] = "{:.0f}"
        elif any(key in col_upper for key in ["PRIX", "PER", "ROE", "MARGE", "FRAIS", "DETTE", "FCF", "RENDEMENT", "P/S", "P/B"]):
            formatters[col] = "{:.2f}"
        elif any(key in col_upper for key in ["CAPITALISATION", "ACTIFS", "AUM"]):
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
        ticker = str(row.get("Symbole", row.get("SYMBOLE", ""))).upper().strip()
        name = str(row.get("Nom", row.get("NOM", ""))).strip()

        if not ticker:
            continue

        label = f"{ticker} - {name}" if name else ticker

        with cols[i % 2]:
            if st.button(label, key=f"{key_prefix}_{i}_{ticker}"):
                open_asset_in_analysis(ticker)


def score_stock(data):
    valuation = 0
    if data.get("PER_Actuel") is not None and 0 < data["PER_Actuel"] < 20:
        valuation += 5
    if data.get("PS") is not None and 0 < data["PS"] < 2:
        valuation += 4
    if data.get("PB") is not None and 0 < data["PB"] < 3:
        valuation += 4
    if data.get("EV_EBITDA") is not None and 0 < data["EV_EBITDA"] < 10:
        valuation += 4
    if data.get("Graham") is not None and data.get("Prix") is not None and data["Graham"] > data["Prix"]:
        valuation += 3
    if data.get("FCF_Yield") is not None and data["FCF_Yield"] > 5:
        valuation += 4
    valuation = min(valuation, 20)

    rentabilite = 0
    if data.get("Marge_Brute") is not None and data["Marge_Brute"] > 30:
        rentabilite += 3
    if data.get("Marge_Op") is not None and data["Marge_Op"] > 15:
        rentabilite += 5
    if data.get("Marge_Nette") is not None and data["Marge_Nette"] > 10:
        rentabilite += 4
    if data.get("ROE") is not None and data["ROE"] > 15:
        rentabilite += 5
    if data.get("ROA") is not None and data["ROA"] > 5:
        rentabilite += 3
    rentabilite = min(rentabilite, 20)

    bilan = 0
    levier = data.get("Levier")
    if isinstance(levier, str) and levier.lower() == "cash positif":
        bilan += 7
    elif isinstance(levier, (int, float)) and levier < 2.5:
        bilan += 7
    if data.get("Current_Ratio") is not None and data["Current_Ratio"] > 1.5:
        bilan += 5
    if data.get("Quick_Ratio") is not None and data["Quick_Ratio"] > 1:
        bilan += 4
    if data.get("Debt_Equity") is not None and data["Debt_Equity"] < 100:
        bilan += 4
    bilan = min(bilan, 20)

    croissance = 0
    if data.get("Rev_Growth") is not None and data["Rev_Growth"] > 5:
        croissance += 7
    if data.get("Earnings_Growth") is not None and data["Earnings_Growth"] > 5:
        croissance += 5
    if data.get("FCF") is not None and data["FCF"] > 0:
        croissance += 4
    if data.get("FCF_Yield") is not None and data["FCF_Yield"] > 5:
        croissance += 4
    croissance = min(croissance, 20)

    momentum = 0
    price = data.get("Prix_Source")
    avg50 = data.get("Fifty_Day_Avg")
    avg200 = data.get("Two_Hundred_Day_Avg")
    change52 = data.get("Perf_52w")

    if price is not None and avg50 is not None and price > avg50:
        momentum += 7
    if price is not None and avg200 is not None and price > avg200:
        momentum += 7
    if change52 is not None and change52 > 0:
        momentum += 6
    momentum = min(momentum, 20)

    details = {
        "Valorisation": valuation,
        "Rentabilité": rentabilite,
        "Bilan": bilan,
        "Croissance": croissance,
        "Momentum": momentum
    }

    return details, sum(details.values())


def render_score_breakdown(score_detail):
    st.markdown("#### Note détaillée")
    cols = st.columns(5)

    for i, (name, value) in enumerate(score_detail.items()):
        with cols[i]:
            render_metric_card(name, format_metric(value, "/20"), tone_higher(value, 10))


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
                or "shortName" in info
                or "longName" in info
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


@st.cache_data(ttl=900)
def get_price_history(ticker_symbol, period):
    try:
        return yf.Ticker(ticker_symbol).history(period=period)
    except Exception:
        return pd.DataFrame()


def get_price_history_with_fallback(primary_ticker, data_ticker, period):
    hist = get_price_history(primary_ticker, period)
    used = primary_ticker

    if hist.empty and data_ticker != primary_ticker:
        hist = get_price_history(data_ticker, period)
        used = data_ticker

    return hist, used


@st.cache_data(ttl=1800)
def get_cashflow_metrics(ticker_symbol, fx_rate):
    tk = yf.Ticker(ticker_symbol)

    try:
        cashflow = tk.cashflow
    except Exception:
        cashflow = pd.DataFrame()

    if cashflow.empty:
        try:
            cashflow = tk.quarterly_cashflow
        except Exception:
            cashflow = pd.DataFrame()

    if cashflow.empty:
        return pd.DataFrame()

    df = pd.DataFrame(index=pd.to_datetime(cashflow.columns))

    if "Operating Cash Flow" in cashflow.index:
        df["Cash-flow opérationnel"] = cashflow.loc["Operating Cash Flow"].astype(float) * fx_rate / 1_000_000

    if "Capital Expenditure" in cashflow.index:
        df["Capex"] = cashflow.loc["Capital Expenditure"].astype(float) * fx_rate / 1_000_000

    if "Free Cash Flow" in cashflow.index:
        df["Free cash flow"] = cashflow.loc["Free Cash Flow"].astype(float) * fx_rate / 1_000_000
    elif "Cash-flow opérationnel" in df.columns and "Capex" in df.columns:
        df["Free cash flow"] = df["Cash-flow opérationnel"] + df["Capex"]

    df = df.sort_index()
    return df.dropna(how="all")


@st.cache_data(ttl=1800)
def get_dividend_history(ticker_symbol):
    try:
        div = yf.Ticker(ticker_symbol).dividends
        if div is None or div.empty:
            return pd.DataFrame()

        annual = div.groupby(div.index.year).sum().tail(8)
        df = pd.DataFrame({
            "Année": annual.index.astype(int),
            "Dividende annuel": annual.values
        })
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800)
def get_share_count_trend(ticker_symbol):
    try:
        bs = yf.Ticker(ticker_symbol).balance_sheet
        if bs.empty:
            return None

        possible_rows = ["Ordinary Shares Number", "Share Issued", "Common Stock Shares Outstanding"]
        for row in possible_rows:
            if row in bs.index:
                serie = bs.loc[row].dropna().astype(float).sort_index()
                if len(serie) >= 2:
                    old = float(serie.iloc[0])
                    new = float(serie.iloc[-1])
                    if old > 0:
                        return ((new / old) - 1) * 100
    except Exception:
        pass

    return None


def latest_value_from_df(df, col):
    if df is None or df.empty or col not in df.columns:
        return None
    serie = df[col].dropna()
    if serie.empty:
        return None
    return float(serie.iloc[-1])


def extract_stock_data(info, fx_rate, ticker_symbol=None):
    d = {}

    raw_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    d["Prix_Source"] = safe_float(raw_price)
    d["Prix"] = safe_float(raw_price, fx_rate)
    d["MarketCap"] = safe_float(info.get("marketCap"), fx_rate / 1_000_000)
    d["Shares"] = safe_float(info.get("sharesOutstanding"), 1, 0)

    d["PER_Actuel"] = safe_float(info.get("trailingPE"))
    d["PER_Futur"] = safe_float(info.get("forwardPE"))
    d["PEG"] = safe_float(info.get("pegRatio"))
    d["PS"] = safe_float(info.get("priceToSalesTrailing12Months"))
    d["PB"] = safe_float(info.get("priceToBook"))
    d["EV_EBITDA"] = safe_float(info.get("enterpriseToEbitda"))
    d["BPA"] = safe_float(info.get("trailingEps"), fx_rate)
    d["BVPS"] = safe_float(info.get("bookValue"), fx_rate)

    if d["BPA"] and d["BVPS"] and (d["BPA"] * d["BVPS"]) > 0:
        d["Graham"] = round(math.sqrt(22.5 * d["BPA"] * d["BVPS"]), 2)
    else:
        d["Graham"] = None

    d["Marge_Brute"] = safe_percent(info.get("grossMargins"))
    d["Marge_Op"] = safe_percent(info.get("operatingMargins"))
    d["Marge_Nette"] = safe_percent(info.get("profitMargins"))
    d["ROE"] = safe_percent(info.get("returnOnEquity"))
    d["ROA"] = safe_percent(info.get("returnOnAssets"))

    treso = safe_float(info.get("totalCash"), fx_rate / 1_000_000)
    dette_totale = safe_float(info.get("totalDebt"), fx_rate / 1_000_000)
    d["EBITDA"] = safe_float(info.get("ebitda"), fx_rate / 1_000_000)
    d["FCF"] = safe_float(info.get("freeCashflow"), fx_rate / 1_000_000)

    d["Dette_Nette"] = dette_totale - treso if treso is not None and dette_totale is not None else None

    if d["Dette_Nette"] is not None and d["EBITDA"] and d["EBITDA"] > 0:
        d["Levier"] = "Cash Positif" if d["Dette_Nette"] < 0 else round(d["Dette_Nette"] / d["EBITDA"], 2)
    else:
        d["Levier"] = None

    d["Current_Ratio"] = safe_float(info.get("currentRatio"))
    d["Quick_Ratio"] = safe_float(info.get("quickRatio"))
    d["Debt_Equity"] = safe_float(info.get("debtToEquity"))
    d["Rev_Growth"] = safe_percent(info.get("revenueGrowth"))
    d["Earnings_Growth"] = safe_percent(info.get("earningsGrowth"))
    d["Payout"] = safe_percent(info.get("payoutRatio"))
    d["Dividend_Yield"] = safe_percent(info.get("dividendYield"))
    d["Dividend_Rate"] = safe_float(info.get("dividendRate"), fx_rate)
    d["Target"] = safe_float(info.get("targetMeanPrice"), fx_rate)
    d["Analystes"] = info.get("numberOfAnalystOpinions", "N/A")

    d["Fifty_Day_Avg"] = safe_float(info.get("fiftyDayAverage"))
    d["Two_Hundred_Day_Avg"] = safe_float(info.get("twoHundredDayAverage"))
    d["Perf_52w"] = safe_percent(info.get("52WeekChange"))

    reco_raw = info.get("recommendationKey", "N/A")
    d["Reco"] = reco_raw.replace("_", " ").upper() if isinstance(reco_raw, str) else "N/A"

    d["Sector"] = safe_str(info.get("sector")).upper()
    d["Industry"] = safe_str(info.get("industry")).upper()

    if ticker_symbol:
        cashflow_df = get_cashflow_metrics(ticker_symbol, fx_rate)
        if d["FCF"] is None:
            latest_fcf = latest_value_from_df(cashflow_df, "Free cash flow")
            if latest_fcf is not None:
                d["FCF"] = round(latest_fcf, 2)

    if d["FCF"] is not None and d["MarketCap"] is not None and d["MarketCap"] > 0:
        d["FCF_Yield"] = round((d["FCF"] / d["MarketCap"]) * 100, 2)
    else:
        d["FCF_Yield"] = None

    score_detail, score = score_stock(d)
    d["Score_Detail"] = score_detail
    d["Score"] = min(score, 100)

    return d


def extract_etf_data(info, ticker_symbol, fx_rate):
    d = {}

    d["Prix"] = safe_float(info.get("navPrice") or info.get("previousClose") or info.get("regularMarketPrice"), fx_rate)
    d["TER"] = safe_percent(info.get("annualReportExpenseRatio"))
    d["AUM"] = safe_float(info.get("totalAssets"), fx_rate / 1_000_000)

    name = str(info.get("longName", "")).upper()
    category = str(info.get("category", "")).upper()

    d["Distribution"] = "ACCUMULATION" if " ACC" in name or "ACCUM" in name else "DISTRIBUTION"
    d["Replication"] = "SYNTHÉTIQUE (SWAP)" if "SWAP" in name else "PHYSIQUE"

    is_pea = any(x in name for x in ["AMUNDI", "LYXOR", "BNP", "ISHARES"]) and ".PA" in ticker_symbol.upper()
    d["PEA"] = "ÉLIGIBLE PEA" if is_pea else "COMPTE-TITRES"

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

    if feedparser is not None:
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
                    "published": entry.published[5:16] if hasattr(entry, "published") else "Récent"
                })
        except Exception:
            pass

    if not news:
        try:
            tk_news = yf.Ticker(ticker_symbol).news
            if tk_news:
                for n in tk_news[:5]:
                    news.append({
                        "title": n.get("title", "Actualité de marché"),
                        "link": n.get("link", "#"),
                        "publisher": n.get("publisher", "Flux de données"),
                        "published": "Récent"
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
            <h4>Verdict stratégique : {verdict}</h4>
            <p>Note ETF : {score}/100. Actifs sous gestion : {format_metric(data.get("AUM"), "M€")}. Frais : {format_metric(data.get("TER"), "%")}. Réplication : {data.get("Replication", "N/A")}. Fiscalité : {data.get("PEA", "N/A")}.</p>
        </div>
        """

    score = data.get("Score", 0)
    reco = data.get("Reco", "N/A").upper()

    if score >= 70 and "BUY" in reco:
        verdict = "ACHAT FORT"
        color = "buy-verdict"
    elif score >= 55:
        verdict = "ACCUMULATION"
        color = "buy-verdict"
    elif score >= 40:
        verdict = "CONSERVATION"
        color = "hold-verdict"
    else:
        verdict = "LIQUIDATION"
        color = "sell-verdict"

    valorisation = "attractive" if data.get("Graham") and data.get("Prix") and data["Graham"] > data["Prix"] else "tendue"

    return f"""
    <div class="expert-verdict {color}">
        <h4>Verdict stratégique : {verdict}</h4>
        <p>Note globale : {score}/100. Valorisation {valorisation}. ROE : {format_metric(data.get("ROE"), "%")}. Levier : {format_metric(data.get("Levier"), "x")}. Rendement FCF : {format_metric(data.get("FCF_Yield"), "%")}. Secteur : {data.get("Sector", "N/A")}.</p>
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
            info, data_ticker, _ = resolve_analysis_ticker(ticker)

            if not info:
                continue

            fx = get_fx_rate(info.get("currency", "USD"))
            quote_type = info.get("quoteType", "")

            if asset_type == "ETF" or quote_type == "ETF":
                d = extract_etf_data(info, data_ticker, fx)

                rows.append({
                    "Symbole": ticker,
                    "Nom": info.get("shortName", ticker),
                    "Catégorie": "ETF",
                    "Note": d["Score"],
                    "Prix €": d["Prix"],
                    "Actifs sous gestion M€": d["AUM"],
                    "Frais %": d["TER"],
                    "Régime": d["PEA"]
                })
            else:
                d = extract_stock_data(info, fx, data_ticker)

                if asset_type == "SMALL CAPS":
                    market_cap = d.get("MarketCap")
                    if market_cap is not None and market_cap > 10_000:
                        continue

                rows.append({
                    "Symbole": ticker,
                    "Nom": info.get("shortName", ticker),
                    "Catégorie": "Action",
                    "Note": d["Score"],
                    "Prix €": d["Prix"],
                    "Capitalisation M€": d["MarketCap"],
                    "PER": d["PER_Actuel"],
                    "ROE %": d["ROE"],
                    "Marge nette %": d["Marge_Nette"],
                    "Rendement FCF %": d["FCF_Yield"]
                })
        except Exception:
            continue

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    return df.sort_values("Note", ascending=False).head(limit)


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
        "Résultat brut": ["Gross Profit"],
        "EBITDA": ["EBITDA", "Normalized EBITDA"],
        "Résultat opérationnel": ["Operating Income"],
        "Résultat net": ["Net Income", "Net Income Common Stockholders"]
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

    if "Chiffre d'affaires" in df.columns and "Résultat net" in df.columns:
        df["Marge nette %"] = (df["Résultat net"] / df["Chiffre d'affaires"]) * 100

    if "Dette totale" in df.columns and "Cash" in df.columns:
        df["Dette nette"] = df["Dette totale"] - df["Cash"]

    df = df.sort_index()
    df.index = pd.to_datetime(df.index)

    return df.dropna(how="all")


def get_sector_peers(sector, ticker):
    sector = safe_str(sector).upper()

    if ticker.upper() in ["RACE", "RACE.MI", "2FE.MU", "2FE.F", "2FE.BE"]:
        return ["RACE.MI", "MC.PA", "RMS.PA", "KER.PA", "BMW.DE", "MBG.DE", "TSLA"]

    if ticker.upper().endswith(".PA") and sector in ["CONSUMER CYCLICAL", "CONSUMER DEFENSIVE"]:
        return ["MC.PA", "RMS.PA", "KER.PA", "OR.PA", "RI.PA", "CA.PA"]

    for key, peers in SECTOR_PEERS.items():
        if key in sector:
            return [p for p in peers if p.upper() != ticker.upper()]

    return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]


@st.cache_data(ttl=1800)
def get_sector_comparison(ticker_symbol, sector):
    peers = get_sector_peers(sector, ticker_symbol)
    universe = [ticker_symbol] + [p for p in peers if p.upper() != ticker_symbol.upper()][:6]
    rows = []

    for t in universe:
        try:
            info, data_ticker, _ = resolve_analysis_ticker(t)
            if not info:
                continue

            fx = get_fx_rate(info.get("currency", "USD"))
            d = extract_stock_data(info, fx, data_ticker)

            rows.append({
                "Symbole": t,
                "Nom": info.get("shortName", t),
                "Secteur": d["Sector"],
                "Note": d["Score"],
                "PER": d["PER_Actuel"],
                "P/S": d["PS"],
                "P/B": d["PB"],
                "EV/EBITDA": d["EV_EBITDA"],
                "ROE %": d["ROE"],
                "Marge nette %": d["Marge_Nette"],
                "Dette/EBITDA": d["Levier"] if isinstance(d["Levier"], (int, float)) else None,
                "Rendement FCF %": d["FCF_Yield"]
            })
        except Exception:
            continue

    return pd.DataFrame(rows)


def calculate_dcf(data, growth_rate, discount_rate, terminal_growth, years, margin_safety):
    fcf = data.get("FCF")
    shares = data.get("Shares")
    net_debt = data.get("Dette_Nette")
    price = data.get("Prix")

    if not is_num(fcf) or fcf <= 0:
        return None, "Free cash flow indisponible ou négatif. DCF non fiable."
    if not is_num(shares) or shares <= 0:
        return None, "Nombre d'actions indisponible. DCF impossible."
    if discount_rate <= terminal_growth:
        return None, "Le taux d'actualisation doit être supérieur à la croissance terminale."

    projections = []
    current_fcf = fcf

    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth_rate)
        pv = current_fcf / ((1 + discount_rate) ** year)
        projections.append({"Année": year, "FCF projeté M€": current_fcf, "Valeur actuelle M€": pv})

    terminal_value = current_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount_rate) ** years)
    enterprise_value = sum(p["Valeur actuelle M€"] for p in projections) + pv_terminal

    if net_debt is None:
        net_debt = 0

    equity_value = enterprise_value - net_debt
    fair_value = equity_value * 1_000_000 / shares
    safety_price = fair_value * (1 - margin_safety)

    upside = None
    if is_num(price) and price > 0:
        upside = ((fair_value / price) - 1) * 100

    result = {
        "Projections": pd.DataFrame(projections),
        "Valeur terminale M€": terminal_value,
        "Valeur terminale actualisée M€": pv_terminal,
        "Valeur entreprise M€": enterprise_value,
        "Dette nette M€": net_debt,
        "Valeur capitaux propres M€": equity_value,
        "Juste valeur par action €": fair_value,
        "Prix avec marge de sécurité €": safety_price,
        "Potentiel %": upside
    }

    return result, None


def get_risk_alerts(data, metrics_df, share_dilution):
    alerts = []
    missing = []

    required_fields = {
        "PER": data.get("PER_Actuel"),
        "marge nette": data.get("Marge_Nette"),
        "dette nette / EBITDA": data.get("Levier"),
        "free cash flow": data.get("FCF"),
        "payout": data.get("Payout"),
        "current ratio": data.get("Current_Ratio")
    }

    for label, value in required_fields.items():
        if value is None:
            missing.append(label)

    if missing:
        alerts.append(("warning", "Données fondamentales incomplètes chez Yahoo Finance : " + ", ".join(missing) + "."))

    levier = data.get("Levier")
    if isinstance(levier, (int, float)) and levier > 4:
        alerts.append(("danger", f"Dette élevée : dette nette / EBITDA à {levier:.2f}x, zone de danger au-dessus de 4x."))
    elif isinstance(levier, (int, float)) and levier > 2.5:
        alerts.append(("warning", f"Dette à surveiller : dette nette / EBITDA à {levier:.2f}x, au-dessus du repère de 2,5x."))

    if data.get("Debt_Equity") is not None and data["Debt_Equity"] > 150:
        alerts.append(("warning", f"Dette / capitaux propres élevée : {data['Debt_Equity']:.2f}%."))

    if data.get("Current_Ratio") is not None:
        if data["Current_Ratio"] < 1:
            alerts.append(("danger", f"Liquidité court terme faible : Current Ratio à {data['Current_Ratio']:.2f}, sous 1."))
        elif data["Current_Ratio"] < 1.5:
            alerts.append(("warning", f"Liquidité à surveiller : Current Ratio à {data['Current_Ratio']:.2f}, sous le repère de 1,5."))

    if data.get("Quick_Ratio") is not None and data["Quick_Ratio"] < 1:
        alerts.append(("warning", f"Liquidité immédiate à surveiller : Quick Ratio à {data['Quick_Ratio']:.2f}, sous 1."))

    if data.get("Payout") is not None:
        if data["Payout"] > 80:
            alerts.append(("danger", f"Payout dangereux : {data['Payout']:.2f}%, risque de coupure du dividende."))
        elif data["Payout"] > 60:
            alerts.append(("warning", f"Payout à surveiller : {data['Payout']:.2f}%, au-dessus de la zone idéale 30%-60%."))

    if data.get("Dividend_Yield") is not None and data["Dividend_Yield"] > 8:
        alerts.append(("warning", f"Rendement du dividende très élevé : {data['Dividend_Yield']:.2f}%, possible piège de rendement."))

    if data.get("FCF") is not None and data["FCF"] < 0:
        alerts.append(("danger", "Free cash flow négatif : l'entreprise ne génère pas de cash disponible sur la période actuelle."))

    if data.get("FCF_Yield") is not None and data["FCF_Yield"] < 2:
        alerts.append(("warning", f"Rendement FCF faible : {data['FCF_Yield']:.2f}%, sous le seuil confortable de 5%."))

    if data.get("Marge_Nette") is not None and data["Marge_Nette"] < 0:
        alerts.append(("danger", f"Marge nette négative : {data['Marge_Nette']:.2f}%."))
    elif data.get("Marge_Nette") is not None and data["Marge_Nette"] < 5:
        alerts.append(("warning", f"Marge nette faible : {data['Marge_Nette']:.2f}%, rentabilité fragile."))

    if data.get("PER_Actuel") is not None and data["PER_Actuel"] > 35:
        alerts.append(("warning", f"Valorisation exigeante : PER à {data['PER_Actuel']:.2f}, supérieur à 35."))

    if data.get("PS") is not None and data["PS"] > 5:
        alerts.append(("warning", f"Prix / ventes élevé : P/S à {data['PS']:.2f}, zone de survalorisation possible."))

    if data.get("PB") is not None and data["PB"] > 5:
        alerts.append(("warning", f"Prix / valeur comptable élevé : P/B à {data['PB']:.2f}."))

    if data.get("Rev_Growth") is not None and data["Rev_Growth"] < 0:
        alerts.append(("warning", f"Croissance du chiffre d'affaires négative : {data['Rev_Growth']:.2f}%."))
    if data.get("Earnings_Growth") is not None and data["Earnings_Growth"] < 0:
        alerts.append(("warning", f"Croissance des profits négative : {data['Earnings_Growth']:.2f}%."))

    if data.get("Target") is not None and data.get("Prix") is not None and data["Target"] < data["Prix"]:
        alerts.append(("warning", "Objectif moyen des analystes inférieur au prix actuel."))

    if data.get("Prix_Source") is not None and data.get("Two_Hundred_Day_Avg") is not None and data["Prix_Source"] < data["Two_Hundred_Day_Avg"]:
        alerts.append(("warning", "Momentum fragile : prix sous la moyenne mobile 200 jours."))

    if metrics_df is not None and not metrics_df.empty and "Marge nette %" in metrics_df.columns:
        marge = metrics_df["Marge nette %"].dropna().sort_index()
        if len(marge) >= 3:
            last_three = marge.tail(3).values
            if last_three[2] < last_three[1] < last_three[0]:
                alerts.append(("warning", "Marge nette en baisse sur trois périodes consécutives."))

    if share_dilution is not None:
        if share_dilution > 5:
            alerts.append(("warning", f"Dilution importante : nombre d'actions en hausse d'environ {share_dilution:.2f}% sur la période disponible."))
        elif share_dilution > 2:
            alerts.append(("info", f"Dilution légère : nombre d'actions en hausse d'environ {share_dilution:.2f}%."))

    if not alerts:
        alerts.append(("info", "Aucune alerte critique détectée avec les données disponibles. À confirmer avec les rapports financiers officiels."))

    return alerts


def render_risk_alerts(alerts):
    for severity, message in alerts:
        if severity == "danger":
            st.error(message)
        elif severity == "warning":
            st.warning(message)
        else:
            st.info(message)


def build_dividend_analysis(data, dividend_df):
    dividend_yield = data.get("Dividend_Yield")
    payout = data.get("Payout")
    dividend_rate = data.get("Dividend_Rate")

    cagr = None
    if dividend_df is not None and not dividend_df.empty and len(dividend_df) >= 2:
        first = dividend_df["Dividende annuel"].iloc[0]
        last = dividend_df["Dividende annuel"].iloc[-1]
        years = dividend_df["Année"].iloc[-1] - dividend_df["Année"].iloc[0]
        cagr = compute_cagr(first, last, years)

    if payout is None:
        safety = "Indéterminée"
        tone = None
    elif payout <= 60:
        safety = "Saine"
        tone = "positive"
    elif payout <= 80:
        safety = "À surveiller"
        tone = "negative"
    else:
        safety = "Risque de coupure"
        tone = "negative"

    return {
        "Rendement du dividende": dividend_yield,
        "Payout": payout,
        "Dividende annuel": dividend_rate,
        "Croissance dividende": cagr,
        "Sécurité": safety,
        "Tonalité": tone
    }


def pdf_clean(text):
    return str(text).replace("€", "EUR").replace("—", "-").replace("’", "'")


def pdf_escape(text):
    cleaned = pdf_clean(text)
    cleaned = cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return cleaned.encode("latin-1", "replace").decode("latin-1")


def build_simple_pdf(title, lines):
    all_lines = [title, ""]
    for line in lines:
        if line == "":
            all_lines.append("")
        else:
            all_lines.extend(textwrap.wrap(pdf_clean(line), width=94) or [""])

    pages = []
    current = []
    for line in all_lines:
        current.append(line)
        if len(current) >= 46:
            pages.append(current)
            current = []
    if current:
        pages.append(current)

    objects = []
    page_ids = []
    content_ids = []

    objects.append("PLACEHOLDER_CATALOG")
    objects.append("PLACEHOLDER_PAGES")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    next_id = 4
    for page_lines in pages:
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        content_ids.append(content_id)

        text_stream = "BT /F1 10 Tf 50 800 Td 14 TL\n"
        for line in page_lines:
            text_stream += f"({pdf_escape(line)}) Tj T*\n"
        text_stream += "ET"

        stream_bytes = text_stream.encode("latin-1", "replace")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>")
        objects.append(b"<< /Length " + str(len(stream_bytes)).encode() + b" >>\nstream\n" + stream_bytes + b"\nendstream")

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[0] = "<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"

    pdf = b"%PDF-1.4\n"
    offsets = [0]

    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode()
        if isinstance(obj, bytes):
            pdf += obj
        else:
            pdf += obj.encode("latin-1", "replace")
        pdf += b"\nendobj\n"

    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode()

    pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode()
    return pdf


def build_report_lines(ticker, name, data, dcf_result, dividend_analysis, alerts):
    lines = [
        f"Actif : {name} ({ticker})",
        f"Prix marche : {format_metric(data.get('Prix'), 'EUR')}",
        f"Note globale : {data.get('Score', 'N/A')}/100",
        ""
    ]

    if data.get("Score_Detail"):
        lines.append("Note detaillee")
        for key, value in data["Score_Detail"].items():
            lines.append(f"- {key} : {value}/20")
        lines.append("")

    lines.extend([
        "Valorisation",
        f"- PER : {data.get('PER_Actuel')}",
        f"- P/S : {data.get('PS')}",
        f"- P/B : {data.get('PB')}",
        f"- EV/EBITDA : {data.get('EV_EBITDA')}",
        f"- Rendement FCF : {data.get('FCF_Yield')}%",
        "",
        "Rentabilite et bilan",
        f"- Marge brute : {data.get('Marge_Brute')}%",
        f"- Marge nette : {data.get('Marge_Nette')}%",
        f"- ROE : {data.get('ROE')}%",
        f"- Dette nette / EBITDA : {data.get('Levier')}",
        f"- Current ratio : {data.get('Current_Ratio')}",
        "",
        "Dividende",
        f"- Rendement du dividende : {dividend_analysis.get('Rendement du dividende')}%",
        f"- Payout : {dividend_analysis.get('Payout')}%",
        f"- Securite : {dividend_analysis.get('Sécurité')}",
        ""
    ])

    if dcf_result:
        lines.extend([
            "DCF simplifie",
            f"- Juste valeur par action : {dcf_result.get('Juste valeur par action €'):.2f} EUR",
            f"- Prix avec marge de securite : {dcf_result.get('Prix avec marge de sécurité €'):.2f} EUR",
            f"- Potentiel : {dcf_result.get('Potentiel %'):.2f}%" if dcf_result.get("Potentiel %") is not None else "- Potentiel : N/A",
            ""
        ])

    lines.append("Alertes risques")
    for _, message in alerts:
        lines.append(f"- {message}")

    return lines


st.markdown("""
<div class="terminal-shell">
    <div class="terminal-topline">
        <div class="status-pill">Données de marché en direct</div>
    </div>
    <div class="hero-title">Poste d'analyse financière.</div>
    <div class="hero-subtitle">
        Analyse fondamentale, notation propriétaire, DCF, comparaison sectorielle, cash-flow, dividendes, risques et export PDF.
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
        placeholder="Rechercher un actif : AAPL, MSFT, LVMH.PA, 2FE.MU...",
        label_visibility="collapsed",
        key="analysis_ticker"
    ).upper().strip()

    if ticker_input:
        with st.spinner("Acquisition des données en cours..."):
            info, data_ticker, resolution_note = resolve_analysis_ticker(ticker_input)

            if not info:
                st.error("Impossible de récupérer les données. Vérifie le symbole ou réessaie dans quelques minutes.")
                st.stop()

            if resolution_note:
                st.info(resolution_note)

            nom = info.get("longName", info.get("shortName", ticker_input)).upper()
            devise = info.get("currency", "USD").upper()
            fx_rate = get_fx_rate(devise)
            is_etf = info.get("quoteType") == "ETF" or "totalAssets" in info

            if is_etf:
                base_data = extract_etf_data(info, data_ticker, fx_rate)
            else:
                base_data = extract_stock_data(info, fx_rate, data_ticker)

            st.markdown(
                f"<h2>{nom} <span style='color:#2f80ff; font-size:1.05rem;'>// {ticker_input}</span></h2>",
                unsafe_allow_html=True
            )

            tabs = st.tabs([
                "FONDAMENTAUX",
                "TECHNIQUE",
                "ÉVOLUTION DES MÉTRIQUES",
                "VALORISATION DCF",
                "SECTEUR",
                "DIVIDENDES",
                "RISQUES",
                "PRESSE",
                "EXPORT PDF"
            ])

            with tabs[0]:
                if is_etf:
                    data = base_data

                    if data["AUM"] and data["AUM"] < 100:
                        st.warning("Liquidité faible : actifs sous gestion inférieurs à 100 M€.")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        render_metric_card("Note ETF", format_metric(data["Score"], "/100"), tone_score(data["Score"]))
                    with c2:
                        render_metric_card("Valeur liquidative", format_metric(data["Prix"], "€"))
                    with c3:
                        render_metric_card("Frais annuels", format_metric(data["TER"], "%"), tone_lower(data["TER"], 0.30))
                    with c4:
                        render_metric_card("Actifs sous gestion", format_metric(data["AUM"], "M€"), tone_higher(data["AUM"], 100))

                    c5, c6, c7 = st.columns(3)
                    with c5:
                        render_metric_card("Régime fiscal", data["PEA"], "positive" if data["PEA"] == "ÉLIGIBLE PEA" else None)
                    with c6:
                        render_metric_card("Politique dividende", data["Distribution"])
                    with c7:
                        render_metric_card("Réplication", data["Replication"], "positive" if data["Replication"] == "PHYSIQUE" else None)

                else:
                    data = base_data
                    score_tone = tone_score(data["Score"])

                    c1, c2, c3 = st.columns([1.15, 2, 2])

                    with c1:
                        st.markdown(
                            f"""
                            <div class="score-container metric-{score_tone}">
                                <div class="score-title">Note globale</div>
                                <div class="score-val metric-{score_tone}">{data["Score"]}</div>
                                <div class="score-caption">Notation fondamentale sur 100</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with c2:
                        render_metric_card("Prix marché", format_metric(data["Prix"], "€"))
                        render_metric_card(
                            "Objectif moyen analystes",
                            f"{format_metric(data['Target'], '€')} // {data['Reco']}",
                            tone_target(data["Target"], data["Prix"])
                        )

                    with c3:
                        render_metric_card("Capitalisation", format_metric(data["MarketCap"], "M€"))
                        render_metric_card("Croissance CA", format_metric(data["Rev_Growth"], "%"), tone_higher(data["Rev_Growth"], 0))

                    st.markdown("<hr>", unsafe_allow_html=True)
                    render_score_breakdown(data["Score_Detail"])
                    st.markdown("<hr>", unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.markdown("#### Valorisation")
                        render_metric_card("PER trailing", format_metric(data["PER_Actuel"], "x"), tone_between(data["PER_Actuel"], 0, 25))
                        render_metric_card("PER forward", format_metric(data["PER_Futur"], "x"), tone_between(data["PER_Futur"], 0, 25))
                        render_metric_card("PEG", format_metric(data["PEG"], "x"), tone_lower(data["PEG"], 1))
                        render_metric_card("Price / Sales", format_metric(data["PS"], "x"), tone_between(data["PS"], 0, 5))
                        render_metric_card("Price / Book", format_metric(data["PB"], "x"), tone_between(data["PB"], 0, 3))
                        render_metric_card("EV / EBITDA", format_metric(data["EV_EBITDA"], "x"), tone_between(data["EV_EBITDA"], 0, 10))
                        render_metric_card("Rendement FCF", format_metric(data["FCF_Yield"], "%"), tone_higher(data["FCF_Yield"], 5))
                        render_metric_card("Valeur Graham", format_metric(data["Graham"], "€"), tone_graham(data["Graham"], data["Prix"]))

                    with col_b:
                        st.markdown("#### Rentabilité")
                        render_metric_card("Marge brute", format_metric(data["Marge_Brute"], "%"), tone_higher(data["Marge_Brute"], 0))
                        render_metric_card("Marge opérationnelle", format_metric(data["Marge_Op"], "%"), tone_higher(data["Marge_Op"], 15))
                        render_metric_card("Marge nette", format_metric(data["Marge_Nette"], "%"), tone_higher(data["Marge_Nette"], 10))
                        render_metric_card("ROE", format_metric(data["ROE"], "%"), tone_higher(data["ROE"], 15))
                        render_metric_card("ROA", format_metric(data["ROA"], "%"), tone_higher(data["ROA"], 5))
                        render_metric_card("Free cash flow", format_metric(data["FCF"], "M€"), tone_higher(data["FCF"], 0))
                        render_metric_card("Payout ratio", format_metric(data["Payout"], "%"), tone_between(data["Payout"], 30, 60))

                    with col_c:
                        st.markdown("#### Bilan")
                        render_metric_card("Dette nette globale", format_metric(data["Dette_Nette"], "M€"), tone_lower(data["Dette_Nette"], 0))
                        render_metric_card("EBITDA", format_metric(data["EBITDA"], "M€"), tone_higher(data["EBITDA"], 0))
                        render_metric_card("Levier dette / EBITDA", format_metric(data["Levier"], "x"), tone_leverage(data["Levier"]))
                        render_metric_card("Current Ratio", format_metric(data["Current_Ratio"]), tone_higher(data["Current_Ratio"], 1.5))
                        render_metric_card("Quick Ratio", format_metric(data["Quick_Ratio"]), tone_higher(data["Quick_Ratio"], 1.0))
                        render_metric_card("Debt / Equity", format_metric(data["Debt_Equity"], "%"), tone_lower(data["Debt_Equity"], 100))
                        render_metric_card("Rendement du dividende", format_metric(data["Dividend_Yield"], "%"), tone_between(data["Dividend_Yield"], 2, 5))

            with tabs[1]:
                hist, hist_ticker = get_price_history_with_fallback(ticker_input, data_ticker, "5y")

                if len(hist) > 200:
                    if hist_ticker != ticker_input:
                        st.info(f"Historique technique affiché via {hist_ticker}, car l'historique de {ticker_input} est incomplet.")

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
                    st.error("Série temporelle insuffisante.")

            with tabs[2]:
                if is_etf:
                    st.info("L'évolution des métriques fondamentales est disponible pour les actions. Pour les ETF, utilise l'onglet Technique.")
                else:
                    data = base_data
                    metrics_df = get_financial_metric_history(data_ticker, fx_rate)
                    cashflow_df = get_cashflow_metrics(data_ticker, fx_rate)

                    if not cashflow_df.empty:
                        metrics_df = metrics_df.join(cashflow_df, how="outer")

                        if data.get("MarketCap") is not None and data["MarketCap"] > 0 and "Free cash flow" in metrics_df.columns:
                            metrics_df["Rendement FCF %"] = (metrics_df["Free cash flow"] / data["MarketCap"]) * 100

                    if metrics_df.empty:
                        st.warning("Données financières historiques indisponibles pour cet actif chez Yahoo Finance.")
                    else:
                        available_metrics = list(metrics_df.columns)
                        default_metrics = [
                            m for m in ["Chiffre d'affaires", "Résultat net", "EBITDA", "Free cash flow", "Rendement FCF %", "Dette nette"]
                            if m in available_metrics
                        ]

                        selected_metrics = st.multiselect(
                            "Métriques à afficher",
                            available_metrics,
                            default=default_metrics
                        )

                        render_metric_help_chips(selected_metrics)

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
                                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", title="M€ / % selon métrique"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )

                            st.plotly_chart(fig_metrics, use_container_width=True)

                        st.dataframe(format_dataframe(metrics_df.sort_index(ascending=False)), use_container_width=True)

            with tabs[3]:
                if is_etf:
                    st.info("Le DCF est surtout pertinent pour les actions individuelles, pas pour les ETF.")
                else:
                    data = base_data
                    st.markdown("#### Valorisation DCF simplifiée")

                    c1, c2, c3, c4, c5 = st.columns(5)
                    with c1:
                        dcf_growth = st.slider("Croissance FCF annuelle", -10.0, 25.0, 5.0, 0.5) / 100
                    with c2:
                        dcf_discount = st.slider("Taux d'actualisation", 5.0, 18.0, 9.0, 0.5) / 100
                    with c3:
                        dcf_terminal = st.slider("Croissance terminale", 0.0, 5.0, 2.0, 0.25) / 100
                    with c4:
                        dcf_years = st.slider("Horizon", 5, 12, 8)
                    with c5:
                        dcf_safety = st.slider("Marge de sécurité", 0.0, 50.0, 20.0, 5.0) / 100

                    dcf_result, dcf_error = calculate_dcf(data, dcf_growth, dcf_discount, dcf_terminal, dcf_years, dcf_safety)

                    if dcf_error:
                        st.warning(dcf_error)
                    else:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            render_metric_card("Juste valeur DCF", format_metric(dcf_result["Juste valeur par action €"], "€"), tone_target(dcf_result["Juste valeur par action €"], data["Prix"]))
                        with c2:
                            render_metric_card("Prix avec marge de sécurité", format_metric(dcf_result["Prix avec marge de sécurité €"], "€"), tone_target(dcf_result["Prix avec marge de sécurité €"], data["Prix"]))
                        with c3:
                            render_metric_card("Potentiel DCF", format_metric(dcf_result["Potentiel %"], "%"), tone_higher(dcf_result["Potentiel %"], 0))

                        dcf_proj = dcf_result["Projections"]
                        st.dataframe(format_dataframe(dcf_proj), use_container_width=True)

                        fig_fcf = go.Figure()
                        fig_fcf.add_trace(go.Scatter(
                            x=dcf_proj["Année"],
                            y=dcf_proj["FCF projeté M€"],
                            mode="lines+markers",
                            name="FCF projeté",
                            fill="tozeroy",
                            line=dict(color="#2f80ff", width=3),
                            fillcolor="rgba(47,128,255,0.18)"
                        ))
                        fig_fcf.add_trace(go.Scatter(
                            x=dcf_proj["Année"],
                            y=dcf_proj["Valeur actuelle M€"],
                            mode="lines+markers",
                            name="Valeur actualisée",
                            line=dict(color="#53ff9a", width=3)
                        ))
                        fig_fcf.update_layout(
                            height=430,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(13,17,19,0.72)",
                            margin=dict(l=0, r=0, t=30, b=0),
                            xaxis=dict(title="Année", showgrid=False),
                            yaxis=dict(title="M€", gridcolor="rgba(255,255,255,0.07)"),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_fcf, use_container_width=True)

                        fig_value = go.Figure()
                        fig_value.add_trace(go.Bar(
                            x=["Prix actuel", "Juste valeur DCF", "Prix avec sécurité"],
                            y=[data["Prix"], dcf_result["Juste valeur par action €"], dcf_result["Prix avec marge de sécurité €"]],
                            marker_color=["#f5f7f2", "#2f80ff", "#53ff9a"],
                            text=[
                                f"{data['Prix']:.2f} €" if data["Prix"] else "-",
                                f"{dcf_result['Juste valeur par action €']:.2f} €",
                                f"{dcf_result['Prix avec marge de sécurité €']:.2f} €"
                            ],
                            textposition="outside"
                        ))
                        fig_value.update_layout(
                            height=390,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(13,17,19,0.72)",
                            margin=dict(l=0, r=0, t=30, b=0),
                            yaxis=dict(title="€ / action", gridcolor="rgba(255,255,255,0.07)"),
                            xaxis=dict(showgrid=False)
                        )
                        st.plotly_chart(fig_value, use_container_width=True)

            with tabs[4]:
                if is_etf:
                    st.info("Comparaison sectorielle disponible pour les actions individuelles.")
                else:
                    data = base_data
                    st.markdown("#### Comparaison sectorielle automatique")

                    comp_df = get_sector_comparison(data_ticker, data["Sector"])

                    if comp_df.empty:
                        st.error("Comparaison sectorielle indisponible.")
                    else:
                        comp_df = numeric_df_for_display(comp_df)
                        st.dataframe(format_dataframe(comp_df), use_container_width=True, height=430)

                        target_row = comp_df[comp_df["Symbole"].str.upper() == data_ticker.upper()]

                        if not target_row.empty:
                            medians = comp_df[["PER", "ROE %", "Rendement FCF %"]].median(numeric_only=True)
                            target = target_row.iloc[0]

                            c1, c2, c3 = st.columns(3)
                            with c1:
                                render_metric_card("PER vs secteur", f"{format_metric(target.get('PER'), 'x')} / médiane {format_metric(medians.get('PER'), 'x')}", tone_lower(target.get("PER"), medians.get("PER")))
                            with c2:
                                render_metric_card("ROE vs secteur", f"{format_metric(target.get('ROE %'), '%')} / médiane {format_metric(medians.get('ROE %'), '%')}", tone_higher(target.get("ROE %"), medians.get("ROE %")))
                            with c3:
                                render_metric_card("Rendement FCF vs secteur", f"{format_metric(target.get('Rendement FCF %'), '%')} / médiane {format_metric(medians.get('Rendement FCF %'), '%')}", tone_higher(target.get("Rendement FCF %"), medians.get("Rendement FCF %")))

                        scatter_df = comp_df.dropna(subset=["PER", "ROE %"])
                        if not scatter_df.empty:
                            fig_sector = go.Figure()
                            fig_sector.add_trace(go.Scatter(
                                x=scatter_df["PER"],
                                y=scatter_df["ROE %"],
                                mode="markers+text",
                                text=scatter_df["Symbole"],
                                textposition="top center",
                                marker=dict(
                                    size=18,
                                    color=scatter_df["Note"],
                                    colorscale=[[0, "#ff5757"], [0.5, "#ffd166"], [1, "#53ff9a"]],
                                    cmin=0,
                                    cmax=100,
                                    line=dict(color="#f5f7f2", width=1)
                                ),
                                name="Pairs sectoriels"
                            ))
                            fig_sector.update_layout(
                                height=460,
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(13,17,19,0.72)",
                                margin=dict(l=0, r=0, t=30, b=0),
                                xaxis=dict(title="PER", gridcolor="rgba(255,255,255,0.07)"),
                                yaxis=dict(title="ROE %", gridcolor="rgba(255,255,255,0.07)")
                            )
                            st.plotly_chart(fig_sector, use_container_width=True)

            with tabs[5]:
                if is_etf:
                    st.info("Analyse dividende détaillée disponible pour les actions individuelles.")
                else:
                    data = base_data
                    dividend_df = get_dividend_history(data_ticker)
                    dividend_analysis = build_dividend_analysis(data, dividend_df)

                    st.markdown("#### Analyse dividende")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        render_metric_card("Rendement du dividende", format_metric(dividend_analysis["Rendement du dividende"], "%"), tone_between(dividend_analysis["Rendement du dividende"], 2, 5))
                    with c2:
                        render_metric_card("Payout ratio", format_metric(dividend_analysis["Payout"], "%"), tone_between(dividend_analysis["Payout"], 30, 60))
                    with c3:
                        render_metric_card("Croissance dividende", format_metric(dividend_analysis["Croissance dividende"], "%"), tone_higher(dividend_analysis["Croissance dividende"], 0))
                    with c4:
                        render_metric_card("Sécurité dividende", dividend_analysis["Sécurité"], dividend_analysis["Tonalité"])

                    if dividend_df.empty:
                        st.info("Historique de dividendes indisponible.")
                    else:
                        st.dataframe(format_dataframe(dividend_df), use_container_width=True)

                        div_plot = dividend_df.copy()
                        first_div = div_plot["Dividende annuel"].iloc[0]
                        if first_div and first_div > 0:
                            div_plot["Progression cumulée %"] = ((div_plot["Dividende annuel"] / first_div) - 1) * 100
                        else:
                            div_plot["Progression cumulée %"] = None

                        fig_div = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_div.add_trace(
                            go.Bar(
                                x=div_plot["Année"],
                                y=div_plot["Dividende annuel"],
                                marker_color="#2f80ff",
                                name="Dividende annuel"
                            ),
                            secondary_y=False
                        )
                        fig_div.add_trace(
                            go.Scatter(
                                x=div_plot["Année"],
                                y=div_plot["Progression cumulée %"],
                                mode="lines+markers",
                                line=dict(color="#53ff9a", width=3),
                                name="Progression cumulée"
                            ),
                            secondary_y=True
                        )
                        fig_div.update_layout(
                            height=430,
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(13,17,19,0.72)",
                            margin=dict(l=0, r=0, t=30, b=0),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        fig_div.update_yaxes(title_text="Dividende annuel", gridcolor="rgba(255,255,255,0.07)", secondary_y=False)
                        fig_div.update_yaxes(title_text="Progression cumulée %", gridcolor="rgba(255,255,255,0.03)", secondary_y=True)
                        st.plotly_chart(fig_div, use_container_width=True)

            with tabs[6]:
                if is_etf:
                    st.info("Alertes risques surtout disponibles pour les actions individuelles.")
                else:
                    data = base_data
                    metrics_df = get_financial_metric_history(data_ticker, fx_rate)
                    share_dilution = get_share_count_trend(data_ticker)
                    alerts = get_risk_alerts(data, metrics_df, share_dilution)

                    st.markdown("#### Alertes risques")
                    render_risk_alerts(alerts)

            with tabs[7]:
                current_data = base_data
                st.markdown(generate_consensus_and_verdict(current_data, is_etf), unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("#### Presse financière")

                news = get_press_news(data_ticker, nom)

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

            with tabs[8]:
                st.markdown("#### Export PDF")

                if is_etf:
                    st.info("Export PDF détaillé actuellement optimisé pour les actions individuelles.")
                else:
                    data = base_data
                    metrics_df = get_financial_metric_history(data_ticker, fx_rate)
                    dividend_df = get_dividend_history(data_ticker)
                    dividend_analysis = build_dividend_analysis(data, dividend_df)
                    share_dilution = get_share_count_trend(data_ticker)
                    alerts = get_risk_alerts(data, metrics_df, share_dilution)

                    dcf_result, _ = calculate_dcf(
                        data,
                        growth_rate=0.05,
                        discount_rate=0.09,
                        terminal_growth=0.02,
                        years=8,
                        margin_safety=0.20
                    )

                    lines = build_report_lines(ticker_input, nom, data, dcf_result, dividend_analysis, alerts)
                    pdf_bytes = build_simple_pdf(f"Rapport d'analyse - {ticker_input}", lines)

                    st.download_button(
                        "Exporter le rapport PDF",
                        data=pdf_bytes,
                        file_name=f"rapport_{ticker_input}.pdf",
                        mime="application/pdf"
                    )


elif mode == "TOP SÉLECTION":
    st.markdown("#### Sélection algorithmique")

    c1, c2 = st.columns([1, 1])

    with c1:
        asset_type = st.selectbox("Univers", ["ACTIONS", "SMALL CAPS", "ETF"])

    with c2:
        top_limit = st.slider("Nombre de résultats", 5, 20, 10)

    st.caption(f"Actualisation à chaque rechargement de page : {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}")

    with st.spinner("Analyse du marché en cours..."):
        ranking = rank_universe(asset_type, top_limit)

    if ranking.empty:
        st.error("Aucune donnée exploitable pour cet univers.")
    else:
        ranking = numeric_df_for_display(ranking)
        best = ranking.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:
            render_metric_card("Meilleur actif", f"{best['Symbole']}")

        with c2:
            render_metric_card("Note", format_metric(best["Note"], "/100"), tone_score(best["Note"]))

        with c3:
            render_metric_card("Prix", format_metric(best.get("Prix €"), "€"))

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(format_dataframe(ranking), use_container_width=True, height=430)

        render_open_asset_buttons(ranking, "top_selection_open")

        fig_rank = go.Figure()

        fig_rank.add_trace(
            go.Bar(
                x=ranking["Symbole"],
                y=ranking["Note"],
                marker=dict(
                    color=ranking["Note"],
                    colorscale=[
                        [0, "#ff5757"],
                        [0.5, "#ffd166"],
                        [1, "#53ff9a"]
                    ],
                    cmin=0,
                    cmax=100
                ),
                text=ranking["Note"].round(0),
                textposition="outside"
            )
        )

        fig_rank.update_layout(
            height=420,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,19,0.72)",
            margin=dict(l=0, r=0, t=24, b=0),
            yaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.07)", title="Note /100"),
            xaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig_rank, use_container_width=True)


elif mode == "COMPARER":
    st.markdown("#### COMPARER")

    tickers_input = st.text_area(
        "",
        placeholder="Entre tes symboles séparés par une virgule : AAPL, MSFT, LVMH.PA, 2FE.MU",
        label_visibility="collapsed",
        height=90
    ).upper()

    c1, c2, c3 = st.columns(3)

    with c1:
        sort_metric = st.selectbox("Tri principal", ["NOTE", "PRIX (€)", "PER", "ROE (%)", "MARGE NETTE (%)", "RENDEMENT FCF (%)"])

    with c2:
        min_score = st.slider("Note minimum", 0, 100, 0)

    with c3:
        show_chart = st.selectbox("Vue graphique", ["Note", "Note vs PER", "Note vs marge nette", "Note vs rendement FCF"])

    if tickers_input and st.button("Comparer les actifs"):
        with st.spinner("Acquisition et comparaison des données..."):
            t_list = [t.strip().upper() for t in tickers_input.replace("\n", ",").split(",") if t.strip()]
            res = []

            progress_bar = st.progress(0)

            for i, t in enumerate(t_list):
                try:
                    info, data_ticker, _ = resolve_analysis_ticker(t)

                    if not info:
                        progress_bar.progress((i + 1) / len(t_list))
                        continue

                    fx = get_fx_rate(info.get("currency", "USD"))
                    is_etf = info.get("quoteType") == "ETF" or "totalAssets" in info

                    if is_etf:
                        d = extract_etf_data(info, data_ticker, fx)

                        res.append({
                            "SYMBOLE": t,
                            "NOM": info.get("shortName", t),
                            "CATÉGORIE": "ETF",
                            "NOTE": d["Score"],
                            "PRIX (€)": d["Prix"],
                            "CAPITALISATION / ACTIFS (M€)": d["AUM"],
                            "PER": None,
                            "ROE (%)": None,
                            "MARGE NETTE (%)": None,
                            "DETTE/EBITDA": None,
                            "RENDEMENT FCF (%)": None,
                            "FRAIS (%)": d["TER"]
                        })
                    else:
                        d = extract_stock_data(info, fx, data_ticker)

                        res.append({
                            "SYMBOLE": t,
                            "NOM": info.get("shortName", t),
                            "CATÉGORIE": "ACTION",
                            "NOTE": d["Score"],
                            "PRIX (€)": d["Prix"],
                            "CAPITALISATION / ACTIFS (M€)": d["MarketCap"],
                            "PER": d["PER_Actuel"],
                            "ROE (%)": d["ROE"],
                            "MARGE NETTE (%)": d["Marge_Nette"],
                            "DETTE/EBITDA": d["Levier"] if isinstance(d["Levier"], (int, float)) else None,
                            "RENDEMENT FCF (%)": d["FCF_Yield"],
                            "FRAIS (%)": None
                        })
                except Exception:
                    pass

                progress_bar.progress((i + 1) / len(t_list))

            progress_bar.empty()
            st.session_state.compare_raw_df = pd.DataFrame(res) if res else None

    if st.session_state.compare_raw_df is not None and not st.session_state.compare_raw_df.empty:
        df = numeric_df_for_display(st.session_state.compare_raw_df)
        df = df[df["NOTE"] >= min_score]

        if df.empty:
            st.warning("Aucun actif ne passe le filtre de note minimum.")
        else:
            if sort_metric in df.columns:
                df = df.sort_values(by=sort_metric, ascending=False, na_position="last")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_metric_card("Actifs comparés", str(len(df)))
            with c2:
                render_metric_card("Meilleure note", format_metric(df["NOTE"].max(), "/100"), tone_score(df["NOTE"].max()))
            with c3:
                render_metric_card("Note moyenne", format_metric(df["NOTE"].mean(), "/100"), tone_score(df["NOTE"].mean()))
            with c4:
                render_metric_card("Leader", str(df.iloc[0]["SYMBOLE"]))

            st.dataframe(format_dataframe(df), use_container_width=True, height=460)

            button_df = df.rename(columns={"SYMBOLE": "Symbole", "NOM": "Nom"})
            render_open_asset_buttons(button_df, "comparer_open")

            if show_chart == "Note":
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=df["SYMBOLE"],
                        y=df["NOTE"],
                        marker=dict(
                            color=df["NOTE"],
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
                fig.update_yaxes(range=[0, 100], title="Note /100")

            elif show_chart == "Note vs PER":
                chart_df = df.dropna(subset=["PER"])
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=chart_df["PER"],
                        y=chart_df["NOTE"],
                        mode="markers+text",
                        text=chart_df["SYMBOLE"],
                        textposition="top center",
                        marker=dict(size=16, color="#2f80ff", line=dict(color="#f5f7f2", width=1))
                    )
                )
                fig.update_xaxes(title="PER")
                fig.update_yaxes(range=[0, 100], title="Note /100")

            elif show_chart == "Note vs rendement FCF":
                chart_df = df.dropna(subset=["RENDEMENT FCF (%)"])
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=chart_df["RENDEMENT FCF (%)"],
                        y=chart_df["NOTE"],
                        mode="markers+text",
                        text=chart_df["SYMBOLE"],
                        textposition="top center",
                        marker=dict(size=16, color="#2f80ff", line=dict(color="#f5f7f2", width=1))
                    )
                )
                fig.update_xaxes(title="Rendement FCF (%)")
                fig.update_yaxes(range=[0, 100], title="Note /100")

            else:
                chart_df = df.dropna(subset=["MARGE NETTE (%)"])
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=chart_df["MARGE NETTE (%)"],
                        y=chart_df["NOTE"],
                        mode="markers+text",
                        text=chart_df["SYMBOLE"],
                        textposition="top center",
                        marker=dict(size=16, color="#2f80ff", line=dict(color="#f5f7f2", width=1))
                    )
                )
                fig.update_xaxes(title="Marge nette (%)")
                fig.update_yaxes(range=[0, 100], title="Note /100")

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
                file_name="matrice_alpha.csv",
                mime="text/csv"
            )
    elif tickers_input:
        st.info("Clique sur comparer les actifs pour lancer l'analyse.")
