import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import feedparser
import urllib.parse
import time

st.set_page_config(
    page_title="Alpha Terminal Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top left, #18231f 0%, #08110f 32%, #030505 100%);
        color: #f3efe4;
        font-family: "Avenir Next", "Helvetica Neue", sans-serif;
    }

    h1, h2, h3, h4, h5 {
        color: #f7f1df !important;
        font-weight: 500 !important;
        letter-spacing: 0;
        text-transform: none;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    .terminal-header {
        border-bottom: 1px solid rgba(247, 241, 223, 0.16);
        padding-bottom: 18px;
        margin-bottom: 26px;
    }

    .terminal-kicker {
        color: #9fb7a4;
        font-size: 0.78rem;
        letter-spacing: 1.6px;
        text-transform: uppercase;
    }

    .terminal-title {
        font-size: 2.1rem;
        color: #f7f1df;
        font-weight: 500;
        margin-top: 6px;
    }

    .terminal-subtitle {
        color: #9d9a8f;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    .fin-card {
        background: rgba(12, 18, 16, 0.86);
        border: 1px solid rgba(247, 241, 223, 0.12);
        padding: 18px;
        margin-bottom: 16px;
        border-radius: 6px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.22);
    }

    .fin-card:hover {
        border-color: rgba(180, 206, 151, 0.45);
        background: rgba(16, 24, 21, 0.94);
    }

    .fin-title {
        font-size: 0.72rem;
        color: #8b9188;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 1.2px;
        margin-bottom: 10px;
    }

    .fin-val {
        font-size: 1.55rem;
        color: #f7f1df;
        font-weight: 500;
        font-family: "SF Mono", "Courier New", monospace;
    }

    .fin-na {
        color: #666b64;
        font-size: 1.15rem;
        font-weight: 400;
    }

    .fin-cash {
        color: #b4ce97;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .score-container {
        text-align: center;
        padding: 34px 20px;
        background: linear-gradient(180deg, rgba(24, 36, 31, 0.95), rgba(8, 13, 12, 0.95));
        border: 1px solid rgba(180, 206, 151, 0.28);
        border-radius: 8px;
        min-height: 176px;
    }

    .score-title {
        font-size: 0.78rem;
        color: #9fb7a4;
        text-transform: uppercase;
        letter-spacing: 1.6px;
        margin-bottom: 15px;
    }

    .score-val {
        font-size: 4.4rem;
        font-weight: 500;
        color: #f7f1df;
        line-height: 1;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(247, 241, 223, 0.12);
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(247, 241, 223, 0.04);
        border: 1px solid rgba(247, 241, 223, 0.08);
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 13px 22px;
        font-weight: 600;
        color: #9d9a8f;
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(180, 206, 151, 0.12);
        color: #f7f1df;
        border-color: rgba(180, 206, 151, 0.3);
    }

    .expert-verdict {
        border-left: 4px solid #777;
        padding: 20px;
        background: rgba(247, 241, 223, 0.045);
        border-radius: 0 8px 8px 0;
        margin-bottom: 26px;
    }

    .buy-verdict { border-left-color: #b4ce97; }
    .hold-verdict { border-left-color: #d5bf77; }
    .sell-verdict { border-left-color: #be6a5b; }

    .expert-verdict h4 {
        font-size: 1.05rem;
        margin-bottom: 10px;
    }

    .expert-verdict p {
        color: #c5c0b4;
        line-height: 1.6;
        font-size: 0.95rem;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(8, 13, 12, 0.95) !important;
        color: #f7f1df !important;
        border: 1px solid rgba(247, 241, 223, 0.16) !important;
        border-radius: 6px !important;
    }

    .stButton button,
    .stDownloadButton button {
        background: #b4ce97;
        color: #06100d;
        border: none;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 800;
        padding: 10px 22px;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        background: #d4e7bb;
        color: #06100d;
    }

    .stDataFrame {
        border: 1px solid rgba(247, 241, 223, 0.12);
        border-radius: 8px;
        overflow: hidden;
    }

    hr {
        border-color: rgba(247, 241, 223, 0.12);
        margin: 34px 0;
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
    "EXLS", "LNTH", "TMDX", "ALRM", "ITRI", "WING", "SMCI", "NXT", "FN", "CVLT",
    "IPAR", "AKE.PA", "BEN.PA", "VIRP.PA", "ALCJ.PA", "IDL.PA"
]

TOP_ETFS = [
    "SPY", "QQQ", "VTI", "VOO", "SCHD", "VEA", "VWO", "IWM", "XLK", "XLF",
    "IWDA.AS", "VWCE.DE", "CSPX.L", "ESE.PA", "CW8.PA", "WPEA.PA", "PANX.PA",
    "PAEEM.PA", "PUST.PA", "MSE.PA"
]


@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    if not currency_code or not isinstance(currency_code, str):
        return 1.0

    curr = currency_code.upper().strip()
    is_pence = False

    if curr in ["GBP", "GBX", "GBP=X", "GBP"]:
        is_pence = curr == "GBX"
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


def safe_float(val, multiplier=1.0, precision=2):
    if val is None or pd.isna(val) or val == "":
        return None
    try:
        return round(float(val) * multiplier, precision)
    except Exception:
        return None


def safe_str(val):
    if val is None or pd.isna(val) or val == "":
        return "N/A"
    return str(val)


def format_metric(val, suffix=""):
    if val is None:
        return "<span class='fin-na'>—</span>"
    if isinstance(val, str) and val.lower() == "cash positif":
        return "<span class='fin-cash'>CASH POSITIF</span>"
    if isinstance(val, str):
        return val
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"{formatted} {suffix}".strip()


def render_metric_card(title, html_value):
    st.markdown(
        f"""
        <div class="fin-card">
            <div class="fin-title">{title}</div>
            <div class="fin-val">{html_value}</div>
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


@st.cache_data(ttl=600)
def fetch_info_with_retry(ticker_symbol, retries=3, backoff=1):
    for attempt in range(retries):
        try:
            tk = yf.Ticker(ticker_symbol)
            info = tk.info
            if info and ("symbol" in info or "regularMarketPrice" in info or "currentPrice" in info or "previousClose" in info):
                return info
            time.sleep(backoff)
            backoff *= 2
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(backoff)
            backoff *= 2
    return None


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

    d["Score"] = score
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
def get_morningstar_news(ticker_symbol, company_name):
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
                "published": entry.published[5:16] if hasattr(entry, "published") else "Récemment"
            })
    except Exception:
        pass

    if not news:
        try:
            tk_news = yf.Ticker(ticker_symbol).news
            if tk_news:
                for n in tk_news[:5]:
                    news.append({
                        "title": n.get("title", "Intelligence de marché"),
                        "link": n.get("link", "#"),
                        "publisher": n.get("publisher", "Data Feed"),
                        "published": "Récemment"
                    })
        except Exception:
            pass

    return news


def generate_consensus_and_verdict(data, is_etf, nom):
    if is_etf:
        score = data.get("Score", 0)

        if score >= 70:
            verdict, color = "ACHAT"
        elif score >= 50:
            verdict, color = "CONSERVATION", "hold-verdict"
        else:
            verdict, color = "SOUS SURVEILLANCE", "sell-verdict"

        if score >= 70:
            color = "buy-verdict"

        return f"""
        <div class="expert-verdict {color}">
            <h4>Verdict stratégique : {verdict}</h4>
            <p>Score ETF : {score}/100. Actifs sous gestion : {format_metric(data.get("AUM"), "M€")}. Frais : {format_metric(data.get("TER"), "%")}. Réplication : {data.get("Replication", "N/A")}. Fiscalité : {data.get("PEA", "N/A")}.</p>
        </div>
        """

    score = data.get("Score", 0)
    reco = data.get("Reco", "N/A").upper()

    if score >= 65 and "BUY" in reco:
        verdict, color = "ACHAT FORT", "buy-verdict"
    elif score >= 50:
        verdict, color = "ACCUMULATION", "buy-verdict"
    elif score >= 35:
        verdict, color = "CONSERVATION", "hold-verdict"
    else:
        verdict, color = "LIQUIDATION", "sell-verdict"

    return f"""
    <div class="expert-verdict {color}">
        <h4>Verdict stratégique : {verdict}</h4>
        <p>Score d'intégrité : {score}/100. Valorisation {'attractive' if data.get("Graham") and data.get("Prix") and data["Graham"] > data["Prix"] else 'tendue'}. ROE : {format_metric(data.get("ROE"), "%")}. Levier : {format_metric(data.get("Levier"), "x")}. Secteur : {data.get("Sector", "N/A")}. Distribution : {format_metric(data.get("Payout"), "%")}.</p>
    </div>
    """


@st.cache_data(ttl=3600)
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
            info = fetch_info_with_retry(ticker)
            if not info:
                continue

            fx = get_fx_rate(info.get("currency", "USD"))
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
        for label, possible_rows in {
            "Cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
            "Dette totale": ["Total Debt"]
        }.items():
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


st.markdown("""
<div class="terminal-header">
    <div class="terminal-kicker">Alpha Terminal Pro</div>
    <div class="terminal-title">Analyse financière institutionnelle</div>
    <div class="terminal-subtitle">Valorisation, qualité bilancielle, momentum technique, screener et comparateur multi-actifs.</div>
</div>
""", unsafe_allow_html=True)

mode = st.radio(
    "Module",
    ["ANALYSE INDIVIDUELLE", "TOP SÉLECTION", "MATRICE COMPARATIVE"],
    label_visibility="collapsed",
    horizontal=True
)

st.markdown("<br>", unsafe_allow_html=True)

if mode == "ANALYSE INDIVIDUELLE":
    ticker_input = st.text_input(
        "",
        placeholder="Rechercher un actif : AAPL, MSFT, LVMH.PA, CW8.PA...",
        label_visibility="collapsed"
    ).upper().strip()

    if ticker_input:
        with st.spinner("Acquisition des données en cours..."):
            info = fetch_info_with_retry(ticker_input)

            if not info:
                st.error("Impossible de récupérer les données. Vérifie le ticker ou réessaie dans quelques minutes.")
                st.stop()

            nom = info.get("longName", info.get("shortName", ticker_input)).upper()
            devise = info.get("currency", "USD").upper()
            fx_rate = get_fx_rate(devise)
            is_etf = info.get("quoteType") == "ETF" or "totalAssets" in info

            st.markdown(
                f"<h2>{nom} <span style='color:#8b9188; font-size:1.1rem;'>// {ticker_input}</span></h2>",
                unsafe_allow_html=True
            )

            tabs = st.tabs(["FONDAMENTAUX", "TECHNIQUE", "ÉVOLUTION MÉTRIQUES", "INTELLIGENCE"])

            with tabs[0]:
                if is_etf:
                    data = extract_etf_data(info, ticker_input, fx_rate)

                    if data["AUM"] and data["AUM"] < 100:
                        st.warning("Liquidité faible : AUM inférieur à 100 M€.")

                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        render_metric_card("Score ETF", format_metric(data["Score"], "/100"))
                    with c2:
                        render_metric_card("Net Asset Value", format_metric(data["Prix"], "€"))
                    with c3:
                        render_metric_card("Total Expense Ratio", format_metric(data["TER"], "%"))
                    with c4:
                        render_metric_card("Assets Under Management", format_metric(data["AUM"], "M€"))

                    c5, c6, c7 = st.columns(3)
                    with c5:
                        render_metric_card("Régime fiscal", data["PEA"])
                    with c6:
                        render_metric_card("Politique dividende", data["Distribution"])
                    with c7:
                        render_metric_card("Réplication", data["Replication"])

                else:
                    data = extract_stock_data(info, fx_rate)

                    c1, c2, c3 = st.columns([1.2, 2, 2])
                    with c1:
                        st.markdown(
                            f"""
                            <div class="score-container">
                                <div class="score-title">Score d'intégrité</div>
                                <div class="score-val">{data["Score"]}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with c2:
                        render_metric_card("Prix marché", format_metric(data["Prix"], "€"))
                        render_metric_card("Consensus target", f"{format_metric(data['Target'], '€')} // {data['Reco']}")
                    with c3:
                        render_metric_card("Capitalisation", format_metric(data["MarketCap"], "M€"))
                        render_metric_card("Croissance CA", format_metric(data["Rev_Growth"], "%"))

                    st.markdown("<hr>", unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.markdown("#### Valorisation")
                        render_metric_card("PER trailing", format_metric(data["PER_Actuel"], "x"))
                        render_metric_card("PER forward", format_metric(data["PER_Futur"], "x"))
                        render_metric_card("Price / Sales", format_metric(data["PS"], "x"))
                        render_metric_card("Price / Book", format_metric(data["PB"], "x"))
                        render_metric_card("EV / EBITDA", format_metric(data["EV_EBITDA"], "x"))
                        render_metric_card("Valeur Graham", format_metric(data["Graham"], "€"))

                    with col_b:
                        st.markdown("#### Rentabilité")
                        render_metric_card("Marge brute", format_metric(data["Marge_Brute"], "%"))
                        render_metric_card("Marge opérationnelle", format_metric(data["Marge_Op"], "%"))
                        render_metric_card("Marge nette", format_metric(data["Marge_Nette"], "%"))
                        render_metric_card("ROE", format_metric(data["ROE"], "%"))
                        render_metric_card("ROA", format_metric(data["ROA"], "%"))
                        render_metric_card("Payout ratio", format_metric(data["Payout"], "%"))

                    with col_c:
                        st.markdown("#### Bilan")
                        render_metric_card("Dette nette globale", format_metric(data["Dette_Nette"], "M€"))
                        render_metric_card("EBITDA", format_metric(data["EBITDA"], "M€"))
                        render_metric_card("Levier dette / EBITDA", format_metric(data["Levier"], "x"))
                        render_metric_card("Current ratio", format_metric(data["Current_Ratio"]))
                        render_metric_card("Quick ratio", format_metric(data["Quick_Ratio"]))
                        render_metric_card("Debt / Equity", format_metric(data["Debt_Equity"], "%"))

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

                    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close_EUR"], name="Prix", line=dict(color="#f7f1df", width=1.8)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA50"], name="MM50", line=dict(color="#b4ce97", width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist["SMA200"], name="MM200", line=dict(color="#d5bf77", width=1.2)), row=1, col=1)

                    fig.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], name="RSI", line=dict(color="#c5c0b4", width=1)), row=2, col=1)
                    fig.add_hline(y=70, line_color="#be6a5b", line_width=1, row=2, col=1)
                    fig.add_hline(y=30, line_color="#b4ce97", line_width=1, row=2, col=1)

                    fig.update_layout(
                        height=650,
                        template="plotly_dark",
                        margin=dict(l=0, r=0, t=30, b=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(8,13,12,0.88)",
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor="rgba(247,241,223,0.08)"),
                        xaxis2=dict(showgrid=False),
                        yaxis2=dict(showgrid=True, gridcolor="rgba(247,241,223,0.08)"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Série temporelle insuffisante.")

            with tabs[2]:
                if is_etf:
                    st.info("L'évolution des métriques fondamentales est disponible pour les actions. Pour les ETF, utilise l'onglet Technique.")
                else:
                    metrics_df = get_financial_metric_history(ticker_input, fx_rate)

                    if metrics_df.empty:
                        st.error("Données financières trimestrielles indisponibles pour cet actif.")
                    else:
                        available_metrics = list(metrics_df.columns)

                        selected_metrics = st.multiselect(
                            "Métriques à afficher",
                            available_metrics,
                            default=[m for m in ["Chiffre d'affaires", "Résultat net", "EBITDA", "Dette nette"] if m in available_metrics]
                        )

                        if selected_metrics:
                            fig_metrics = go.Figure()

                            for metric in selected_metrics:
                                fig_metrics.add_trace(
                                    go.Scatter(
                                        x=metrics_df.index,
                                        y=metrics_df[metric],
                                        mode="lines+markers",
                                        name=metric,
                                        line=dict(width=2)
                                    )
                                )

                            fig_metrics.update_layout(
                                height=560,
                                template="plotly_dark",
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(8,13,12,0.88)",
                                margin=dict(l=0, r=0, t=30, b=0),
                                xaxis=dict(showgrid=False),
                                yaxis=dict(showgrid=True, gridcolor="rgba(247,241,223,0.08)", title="M€ / % selon métrique"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )

                            st.plotly_chart(fig_metrics, use_container_width=True)

                        st.dataframe(
                            metrics_df.sort_index(ascending=False).style.format("{:,.2f}", na_rep="—"),
                            use_container_width=True
                        )

            with tabs[3]:
                st.markdown(generate_consensus_and_verdict(data, is_etf, nom), unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("#### Intelligence de marché")

                news = get_morningstar_news(ticker_input, nom)

                if news:
                    for n in news:
                        st.markdown(
                            f"""
                            <div style="background:rgba(12,18,16,0.86); padding:16px; border:1px solid rgba(247,241,223,0.12); border-left:4px solid #b4ce97; border-radius:0 8px 8px 0; margin-bottom:14px;">
                                <a href="{n['link']}" target="_blank" style="color:#f7f1df; font-weight:600; text-decoration:none; font-size:1rem;">{n['title']}</a><br>
                                <span style="color:#8b9188; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; display:inline-block; margin-top:8px;">{n['publisher']} // {n['published']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Flux d'information indisponible.")


elif mode == "TOP SÉLECTION":
    st.markdown("#### Sélection algorithmique")

    c1, c2 = st.columns([1, 1])

    with c1:
        asset_type = st.selectbox("Univers", ["ACTIONS", "SMALL CAPS", "ETF"])

    with c2:
        top_limit = st.slider("Nombre de résultats", 5, 20, 10)

    with st.spinner("Classement des meilleurs actifs selon le score /100..."):
        ranking = rank_universe(asset_type, top_limit)

    if ranking.empty:
        st.error("Aucune donnée exploitable pour cet univers.")
    else:
        best = ranking.iloc[0]

        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Meilleur actif", f"{best['Ticker']}")
        with c2:
            render_metric_card("Score", format_metric(best["Score"], "/100"))
        with c3:
            render_metric_card("Prix", format_metric(best.get("Prix €"), "€"))

        st.markdown("<br>", unsafe_allow_html=True)

        st.dataframe(
            ranking.style
            .format({
                "Score": "{:.0f}",
                "Prix €": "{:.2f}",
                "Market Cap M€": "{:.0f}",
                "AUM M€": "{:.0f}",
                "TER %": "{:.2f}",
                "PER": "{:.2f}",
                "ROE %": "{:.2f}",
                "Marge nette %": "{:.2f}"
            }, na_rep="—")
            .background_gradient(subset=["Score"], cmap="YlGn"),
            use_container_width=True,
            height=430
        )

        fig_rank = go.Figure()
        fig_rank.add_trace(
            go.Bar(
                x=ranking["Ticker"],
                y=ranking["Score"],
                marker_color="#b4ce97",
                text=ranking["Score"],
                textposition="outside"
            )
        )
        fig_rank.update_layout(
            height=420,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,13,12,0.88)",
            margin=dict(l=0, r=0, t=24, b=0),
            yaxis=dict(range=[0, 100], gridcolor="rgba(247,241,223,0.08)", title="Score /100"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_rank, use_container_width=True)


elif mode == "MATRICE COMPARATIVE":
    st.markdown("#### Comparateur multi-actifs")

    tickers_input = st.text_area(
        "",
        placeholder="Entre tes tickers séparés par une virgule : AAPL, MSFT, LVMH.PA, CW8.PA",
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
            with st.spinner("Acquisition et comparaison des données..."):
                t_list = [t.strip().upper() for t in tickers_input.replace("\n", ",").split(",") if t.strip()]
                res = []

                progress_bar = st.progress(0)

                for i, t in enumerate(t_list):
                    try:
                        info = fetch_info_with_retry(t)

                        if not info:
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
                    df = df[df["SCORE"] >= min_score]

                    if df.empty:
                        st.warning("Aucun actif ne passe le filtre de score minimum.")
                        st.stop()

                    if sort_metric in df.columns:
                        df = df.sort_values(by=sort_metric, ascending=False)

                    styled_df = df.style.format({
                        "SCORE": "{:.0f}",
                        "PRIX (€)": "{:.2f}",
                        "MARKET CAP / AUM (M€)": "{:.0f}",
                        "PER": "{:.2f}",
                        "ROE (%)": "{:.2f}",
                        "MARGE NETTE (%)": "{:.2f}",
                        "DETTE/EBITDA": "{:.2f}",
                        "FRAIS (%)": "{:.2f}"
                    }, na_rep="—").background_gradient(subset=["SCORE"], cmap="YlGn")

                    st.dataframe(styled_df, use_container_width=True, height=460)

                    if show_chart == "Score":
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=df["TICKER"], y=df["SCORE"], marker_color="#b4ce97"))
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
                                marker=dict(size=14, color="#b4ce97")
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
                                marker=dict(size=14, color="#b4ce97")
                            )
                        )
                        fig.update_xaxes(title="Marge nette (%)")
                        fig.update_yaxes(range=[0, 100], title="Score /100")

                    fig.update_layout(
                        height=440,
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(8,13,12,0.88)",
                        margin=dict(l=0, r=0, t=24, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(gridcolor="rgba(247,241,223,0.08)")
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
                    st.error("Échec total de l'extraction.")
