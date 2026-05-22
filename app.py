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

# ==============================================================================
# CONFIGURATION DE LA PAGE & DESIGN UI/UX INSTITUTIONNEL (VIBE: BATMAN / AMERICAN PSYCHO)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Terminal Pro | Institutionnel",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Vibe sombre, épurée, bords tranchants, noir profond et contrastes nets */
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Helvetica Neue', sans-serif; }
    h1, h2, h3, h4, h5 { color: #ffffff !important; font-weight: 300 !important; letter-spacing: 1px; text-transform: uppercase; }
    
    /* Cartes de métriques - Style Verre Fumé / Minimaliste */
    .fin-card {
        background-color: #0a0a0a;
        border: 1px solid #1a1a1a;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        border-left: 3px solid #333333;
        transition: all 0.3s ease;
    }
    .fin-card:hover { border-left-color: #f1f1f1; background-color: #0f0f0f; }
    .fin-title { font-size: 0.75rem; color: #888888; text-transform: uppercase; font-weight: 400; letter-spacing: 2px; margin-bottom: 12px; }
    .fin-val { font-size: 1.8rem; color: #ffffff; font-weight: 200; font-family: 'Courier New', monospace; }
    .fin-na { color: #555555; font-size: 1.2rem; font-weight: 200; }
    .fin-cash { color: #a3b18a; font-size: 1.2rem; font-weight: 400; letter-spacing: 1px; }
    
    /* Conteneur Score */
    .score-container { text-align: center; padding: 40px 20px; background-color: #0a0a0a; border: 1px solid #1a1a1a; }
    .score-title { font-size: 0.85rem; color: #888888; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 15px; }
    .score-val { font-size: 4.5rem; font-weight: 100; color: #ffffff; line-height: 1; font-family: 'Helvetica Neue', sans-serif;}
    
    /* Tabs Streamlit modifiés pour un look tranchant */
    .stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 1px solid #1a1a1a; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 15px 30px; font-weight: 300; letter-spacing: 1px; color: #888888; }
    .stTabs [aria-selected="true"] { background-color: #0a0a0a; border-bottom: 2px solid #ffffff; color: #ffffff; }
    
    /* Verdict de l'Expert - Minimaliste et catégorique */
    .expert-verdict { border-left: 2px solid #555555; padding-left: 20px; background-color: transparent; padding: 20px; margin-bottom: 30px; }
    .buy-verdict { border-left-color: #a3b18a; } /* Vert sourd */
    .hold-verdict { border-left-color: #888888; } /* Gris neutre */
    .sell-verdict { border-left-color: #5c1616; } /* Rouge sombre */
    .expert-verdict h4 { font-size: 1.1rem; margin-bottom: 10px; font-weight: 400 !important; }
    .expert-verdict p { color: #aaaaaa; font-weight: 300; line-height: 1.6; font-size: 0.95rem; }
    
    /* Inputs et boutons */
    .stTextInput input { background-color: #0a0a0a !important; color: #ffffff !important; border: 1px solid #333333 !important; border-radius: 0 !important; }
    .stTextInput input:focus { border-color: #ffffff !important; box-shadow: none !important; }
    .stButton button { background-color: #ffffff; color: #000000; border: none; border-radius: 0; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; padding: 10px 25px; transition: all 0.2s ease;}
    .stButton button:hover { background-color: #cccccc; color: #000000; }
    
    /* Dataframes */
    .stDataFrame { border: 1px solid #1a1a1a; }
    
    /* Custom divider */
    hr { border-color: #1a1a1a; margin: 40px 0; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# MOTEUR DE TRAITEMENT ET CONVERSION (ROBUSTE ET SÉCURISÉ)
# ==============================================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    if not currency_code or not isinstance(currency_code, str):
        return 1.0
    curr = currency_code.upper().strip()
    is_pence = False
    if curr in ["GBP", "GBX", "GBP=X", "GBp"]:
        is_pence = (curr in ["GBX", "GBp"])
        curr = "GBP"
    if curr == "EUR":
        return 0.01 if is_pence else 1.0

    fallbacks = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "CAD": 0.68, "JPY": 0.006, "AUD": 0.60, "CNY": 0.13}
    try:
        data = yf.Ticker(f"{curr}EUR=X").history(period="1d")
        if not data.empty:
            rate = float(data['Close'].iloc[-1])
            return (rate * 0.01) if is_pence else rate
    except Exception:
        pass
    rate = fallbacks.get(curr, 1.0)
    return (rate * 0.01) if is_pence else rate

def safe_float(val, multiplier=1.0, precision=2):
    if val is None or pd.isna(val) or val == "": return None
    try: return round(float(val) * multiplier, precision)
    except Exception: return None

def safe_str(val):
    if val is None or pd.isna(val) or val == "": return "N/A"
    return str(val)

def format_metric(val, suffix="", is_currency=False):
    if val is None: return "<span class='fin-na'>—</span>"
    if isinstance(val, str) and val.lower() == "cash positif": return "<span class='fin-cash'>CASH POSITIF</span>"
    if isinstance(val, str): return val
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"{formatted} {suffix}".strip()

def render_metric_card(title, html_value):
    st.markdown(f'<div class="fin-card"><div class="fin-title">{title}</div><div class="fin-val">{html_value}</div></div>', unsafe_allow_html=True)

def calculer_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ==============================================================================
# ABSTRACTION DES DONNÉES & CALCULS FONCTIONNELS
# ==============================================================================
@st.cache_data(ttl=600)
def fetch_info_with_retry(ticker_symbol, retries=3, backoff=1):
    """Tente de récupérer les infos avec un système de retry pour contrer les Timeout/Rate Limit de Yahoo"""
    for attempt in range(retries):
        try:
            tk = yf.Ticker(ticker_symbol)
            info = tk.info
            # Vérification basique pour s'assurer que c'est un dictionnaire valide
            if info and ('symbol' in info or 'regularMarketPrice' in info or 'currentPrice' in info or 'previousClose' in info):
                return info
            # Si le dico est vide (parfois Yahoo fait ça en cas de rate limit muet)
            time.sleep(backoff)
            backoff *= 2
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(backoff)
            backoff *= 2
    return None

def extract_stock_data(info, fx_rate):
    d = {}
    d['Prix'] = safe_float(info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose'), fx_rate)
    d['PER_Actuel'] = safe_float(info.get('trailingPE'))
    d['PER_Futur'] = safe_float(info.get('forwardPE'))
    d['PS'] = safe_float(info.get('priceToSalesTrailing12Months'))
    d['PB'] = safe_float(info.get('priceToBook'))
    d['EV_EBITDA'] = safe_float(info.get('enterpriseToEbitda'))
    d['BPA'] = safe_float(info.get('trailingEps'), fx_rate)
    d['BVPS'] = safe_float(info.get('bookValue'), fx_rate)
    
    if d['BPA'] and d['BVPS'] and (d['BPA'] * d['BVPS']) > 0:
        d['Graham'] = round(math.sqrt(22.5 * d['BPA'] * d['BVPS']), 2)
    else: d['Graham'] = None

    d['Marge_Brute'] = safe_float(info.get('grossMargins'), 100)
    d['Marge_Op'] = safe_float(info.get('operatingMargins'), 100)
    d['Marge_Nette'] = safe_float(info.get('profitMargins'), 100)
    d['ROE'] = safe_float(info.get('returnOnEquity'), 100)
    d['ROA'] = safe_float(info.get('returnOnAssets'), 100)

    treso = safe_float(info.get('totalCash'), fx_rate / 1_000_000)
    dette_totale = safe_float(info.get('totalDebt'), fx_rate / 1_000_000)
    d['EBITDA'] = safe_float(info.get('ebitda'), fx_rate / 1_000_000)
    
    d['Dette_Nette'] = (dette_totale - treso) if treso is not None and dette_totale is not None else None

    if d['Dette_Nette'] is not None and d['EBITDA'] and d['EBITDA'] > 0:
        d['Levier'] = "Cash Positif" if d['Dette_Nette'] < 0 else round(d['Dette_Nette'] / d['EBITDA'], 2)
    else: d['Levier'] = None

    d['Current_Ratio'] = safe_float(info.get('currentRatio'))
    d['Quick_Ratio'] = safe_float(info.get('quickRatio'))
    d['Debt_Equity'] = safe_float(info.get('debtToEquity'))
    d['Rev_Growth'] = safe_float(info.get('revenueGrowth'), 100)
    d['Payout'] = safe_float(info.get('payoutRatio'), 100)
    d['Target'] = safe_float(info.get('targetMeanPrice'), fx_rate)
    d['Analystes'] = info.get('numberOfAnalystOpinions', 'N/A')
    
    reco_raw = info.get('recommendationKey', 'N/A')
    d['Reco'] = reco_raw.replace('_', ' ').upper() if isinstance(reco_raw, str) else 'N/A'
    
    score = 0
    if isinstance(d['Levier'], float) and d['Levier'] < 2: score += 15
    elif isinstance(d['Levier'], str) and d['Levier'] == "Cash Positif": score += 15
    if d['ROE'] is not None and d['ROE'] > 15: score += 15
    if d['Marge_Nette'] is not None and d['Marge_Nette'] > 12: score += 15
    if d['Graham'] is not None and d['Prix'] is not None and d['Graham'] > d['Prix']: score += 15
    if d['PER_Actuel'] is not None and 0 < d['PER_Actuel'] < 20: score += 10
    if d['Current_Ratio'] is not None and d['Current_Ratio'] > 1.2: score += 10
    if d['Rev_Growth'] is not None and d['Rev_Growth'] > 5: score += 10
    if d['Payout'] is not None and 0 < d['Payout'] < 60: score += 10
    d['Score'] = score
    d['Sector'] = safe_str(info.get('sector')).upper()
    d['Industry'] = safe_str(info.get('industry')).upper()

    return d

def extract_etf_data(info, ticker_symbol, fx_rate):
    d = {}
    d['Prix'] = safe_float(info.get('navPrice') or info.get('previousClose') or info.get('regularMarketPrice'), fx_rate)
    d['TER'] = safe_float(info.get('annualReportExpenseRatio') or info.get('ytdReturn'), 100)
    d['AUM'] = safe_float(info.get('totalAssets'), fx_rate / 1_000_000)
    name = str(info.get('longName', '')).upper()
    d['Distribution'] = "ACCUMULATION" if " ACC" in name or "ACCUM" in name else "DISTRIBUTION"
    d['Replication'] = "SYNTHÉTIQUE (SWAP)" if "SWAP" in name else "PHYSIQUE"
    is_pea = any(x in name for x in ["AMUNDI", "LYXOR", "BNP"]) and ".PA" in ticker_symbol.upper()
    d['PEA'] = "ÉLIGIBLE PEA" if is_pea else "COMPTE-TITRES"
    return d


# ==============================================================================
# MOTEUR D'ACTUALITÉS (CONTOURNEMENT ANTI-BOTS VIA GOOGLE NEWS RSS)
# ==============================================================================
@st.cache_data(ttl=1800)
def get_morningstar_news(ticker_symbol, company_name):
    news = []
    try:
        clean_ticker = ticker_symbol.split('.')[0]
        query = f'"{clean_ticker}" (site:morningstar.fr OR site:morningstar.com OR site:lesechos.fr)'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
        
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:5]:
            title = entry.title.rsplit(' - ', 1)[0] if ' - ' in entry.title else entry.title
            news.append({
                'title': title,
                'link': entry.link,
                'publisher': entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else 'Presse',
                'published': entry.published[5:16] if hasattr(entry, 'published') else 'Récemment'
            })
    except Exception:
        pass

    if not news:
        try:
            tk_news = yf.Ticker(ticker_symbol).news
            if tk_news:
                for n in tk_news[:5]:
                    news.append({
                        'title': n.get('title', 'Intelligence de marché'),
                        'link': n.get('link', '#'),
                        'publisher': n.get('publisher', 'Data Feed'),
                        'published': 'Récemment'
                    })
        except Exception:
            pass
            
    return news

def generate_consensus_and_verdict(data, is_etf, nom):
    if is_etf:
        verdict = "ACHAT" if (data['AUM'] and data['AUM'] > 100) and (data['TER'] and data['TER'] < 0.3) else "CONSERVATION"
        color = "buy-verdict" if verdict == "ACHAT" else "hold-verdict"
        return f"""
        <div class="expert-verdict {color}">
            <h4>VERDICT STRATÉGIQUE : {verdict}</h4>
            <p>VÉHICULE INDICIEL {data.get('Replication', '')}. LIQUIDITÉ {'OPTIMALE' if (data['AUM'] or 0) > 100 else 'SOUS SURVEILLANCE'} ({format_metric(data['AUM'], 'M€')}). FRAIS STRUCTURELS : {format_metric(data['TER'], '%')}. EXPOSITION MACRO-ÉCONOMIQUE ALIGNÉE.</p>
        </div>
        """
    else:
        score = data.get('Score', 0)
        reco = data.get('Reco', 'N/A').upper()
        if score >= 65 and 'BUY' in reco: verdict, color = "ACHAT FORT", "buy-verdict"
        elif score >= 50: verdict, color = "ACCUMULATION", "buy-verdict"
        elif score >= 35: verdict, color = "CONSERVATION", "hold-verdict"
        else: verdict, color = "LIQUIDATION", "sell-verdict"
        
        return f"""
        <div class="expert-verdict {color}">
            <h4>VERDICT STRATÉGIQUE : {verdict}</h4>
            <p>SCORE D'INTÉGRITÉ : {score}/100. VALORISATION {'ATTRACTIVE' if data['Graham'] and data['Prix'] and data['Graham'] > data['Prix'] else 'TENDUE'}. RENTABILITÉ DU CAPITAL : {format_metric(data['ROE'], '%')}. LEVIER D'EXPLOITATION : {format_metric(data['Levier'], 'x')}. SECTEUR : {data.get('Sector', 'N/A')}. DISTRIBUTION : {format_metric(data['Payout'], '%')}.</p>
        </div>
        """


# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================
st.markdown("<h3>ALPHA TERMINAL</h3>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top:0px; margin-bottom: 30px;'>", unsafe_allow_html=True)

mode = st.radio("SÉLECTEUR DE MODULE", ["ANALYSE INDIVIDUELLE", "MATRICE COMPARATIVE"], label_visibility="collapsed", horizontal=True)
st.markdown("<br>", unsafe_allow_html=True)

if mode == "ANALYSE INDIVIDUELLE":
    # Search bar style American Psycho : cold, simple, wide
    ticker_input = st.text_input("", placeholder="IDENTIFIANT ACTIF (EX: AAPL, LVMH.PA)", label_visibility="collapsed").upper().strip()
    
    if ticker_input:
        with st.spinner("ACQUISITION DES DONNÉES EN COURS..."):
            info = fetch_info_with_retry(ticker_input)
            
            if not info:
                st.error("ÉCHEC DE LA RÉSOLUTION. IDENTIFIANT INVALIDE OU SERVEUR DISTANT MUET.")
                st.stop()
                
            nom = info.get('longName', info.get('shortName', ticker_input)).upper()
            devise = info.get('currency', 'USD').upper()
            fx_rate = get_fx_rate(devise)
            is_etf = info.get('quoteType') == 'ETF' or 'totalAssets' in info
            
            st.markdown(f"<h2 style='margin-top: 20px;'>{nom} <span style='color:#555555; font-size:1.5rem;'>// {ticker_input}</span></h2>", unsafe_allow_html=True)
            
            tabs = st.tabs(["FONDAMENTAUX", "TECHNIQUE", "SIMULATION DCA", "INTELLIGENCE"])
            
            with tabs[0]:
                if is_etf:
                    data = extract_etf_data(info, ticker_input, fx_rate)
                    if data['AUM'] and data['AUM'] < 100: st.warning("ALERTE : LIQUIDITÉ CRITIQUE (AUM < 100M€).")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: render_metric_card("NET ASSET VALUE", format_metric(data['Prix'], "€"))
                    with c2: render_metric_card("TOTAL EXPENSE", format_metric(data['TER'], "%"))
                    with c3: render_metric_card("ASSETS UNDER MGT", format_metric(data['AUM'], "M€"))
                    with c4: render_metric_card("RÉGIME FISCAL", data['PEA'])
                    c5, c6 = st.columns(2)
                    with c5: render_metric_card("POLITIQUE DIVIDENDE", data['Distribution'])
                    with c6: render_metric_card("MÉTHODE RÉPLICATION", data['Replication'])
                else:
                    data = extract_stock_data(info, fx_rate)
                    c1, c2, c3 = st.columns([1.5, 2, 2])
                    with c1:
                        st.markdown(f'<div class="score-container"><div class="score-title">INDICE D\'INTÉGRITÉ</div><div class="score-val">{data["Score"]}</div></div>', unsafe_allow_html=True)
                    with c2:
                        render_metric_card("PRIX MARCHÉ", format_metric(data['Prix'], "€"))
                        render_metric_card("CONSENSUS TARGET", f"{format_metric(data['Target'], '€')} // {data['Reco']}")
                    with c3:
                        render_metric_card("LEVIER (DETTE/EBITDA)", format_metric(data['Levier'], "x"))
                        render_metric_card("CROISSANCE CA", format_metric(data['Rev_Growth'], "%"))

                    st.markdown("<hr>", unsafe_allow_html=True)
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown("#### MULTIPLES DE VALORISATION")
                        render_metric_card("PER TRAILING", format_metric(data['PER_Actuel'], "x"))
                        render_metric_card("PER FORWARD", format_metric(data['PER_Futur'], "x"))
                        render_metric_card("PRICE / SALES", format_metric(data['PS'], "x"))
                        render_metric_card("PRICE / BOOK", format_metric(data['PB'], "x"))
                        render_metric_card("EV / EBITDA", format_metric(data['EV_EBITDA'], "x"))
                        render_metric_card("VALEUR GRAHAM", format_metric(data['Graham'], "€"))
                    with col_b:
                        st.markdown("#### RENTABILITÉ OPÉRATIONNELLE")
                        render_metric_card("MARGE BRUTE", format_metric(data['Marge_Brute'], "%"))
                        render_metric_card("MARGE OPÉRATIONNELLE", format_metric(data['Marge_Op'], "%"))
                        render_metric_card("MARGE NETTE", format_metric(data['Marge_Nette'], "%"))
                        render_metric_card("RETURN ON EQUITY (ROE)", format_metric(data['ROE'], "%"))
                        render_metric_card("RETURN ON ASSETS (ROA)", format_metric(data['ROA'], "%"))
                        render_metric_card("PAYOUT RATIO", format_metric(data['Payout'], "%"))
                    with col_c:
                        st.markdown("#### STRUCTURE BILANCIELLE")
                        render_metric_card("DETTE NETTE GLOBALE", format_metric(data['Dette_Nette'], "M€"))
                        render_metric_card("GÉNÉRATION EBITDA", format_metric(data['EBITDA'], "M€"))
                        render_metric_card("CURRENT RATIO", format_metric(data['Current_Ratio']))
                        render_metric_card("QUICK RATIO", format_metric(data['Quick_Ratio']))
                        render_metric_card("DEBT / EQUITY", format_metric(data['Debt_Equity'], "%"))
                        render_metric_card("EPS (BPA)", format_metric(data['BPA'], "€"))

            with tabs[1]:
                tk_obj = yf.Ticker(ticker_input)
                hist = tk_obj.history(period="5y")
                if len(hist) > 200:
                    hist['Close_EUR'] = hist['Close'] * fx_rate
                    hist['SMA50'] = hist['Close_EUR'].rolling(50).mean()
                    hist['SMA200'] = hist['Close_EUR'].rolling(200).mean()
                    hist['RSI'] = calculer_rsi(hist['Close'])

                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                    
                    # Colors: Cold, sharp
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close_EUR'], name="SPOT", line=dict(color="#ffffff", width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="MA50", line=dict(color="#555555", width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="MA200", line=dict(color="#880000", width=1)), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color="#aaaaaa", width=1)), row=2, col=1)
                    fig.add_hline(y=70, line_dash="solid", line_color="#880000", line_width=1, row=2, col=1)
                    fig.add_hline(y=30, line_dash="solid", line_color="#a3b18a", line_width=1, row=2, col=1)

                    fig.update_layout(
                        height=650, 
                        template="plotly_dark", 
                        margin=dict(l=0, r=0, t=30, b=0),
                        paper_bgcolor='#050505',
                        plot_bgcolor='#0a0a0a',
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='#1a1a1a'),
                        xaxis2=dict(showgrid=False),
                        yaxis2=dict(showgrid=True, gridcolor='#1a1a1a'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else: st.error("SÉRIE TEMPORELLE INSUFFISANTE.")

            with tabs[2]:
                st.markdown("#### PARAMÈTRES D'INJECTION DE CAPITAL")
                st.markdown("<br>", unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                mensualite = dc1.number_input("INJECTION MENSUELLE (€)", min_value=10, value=1000, step=100, label_visibility="collapsed")
                duree = dc2.selectbox("HORIZON DE MODÉLISATION", ["1y", "3y", "5y", "10y"], index=2, label_visibility="collapsed")
                
                tk_obj = yf.Ticker(ticker_input)
                dca_hist = tk_obj.history(period=duree)
                
                if not dca_hist.empty and len(dca_hist) > 20:
                    dca_hist['Close_EUR'] = dca_hist['Close'] * fx_rate
                    monthly = dca_hist['Close_EUR'].resample('BMS').first().dropna()
                    
                    cap_investi, actions = 0, 0
                    cap_list, val_list = [], []
                    
                    for date, price in monthly.items():
                        actions += mensualite / price
                        cap_investi += mensualite
                        cap_list.append(cap_investi)
                        val_list.append(actions * price)
                        
                    df_dca = pd.DataFrame({'Date': monthly.index, 'Investi': cap_list, 'Valeur': val_list}).set_index('Date')
                    val_finale = df_dca['Valeur'].iloc[-1]
                    pv = val_finale - cap_investi
                    
                    # Style résumé DCA
                    st.markdown(f"""
                    <div style="border: 1px solid #1a1a1a; background-color: #0a0a0a; padding: 20px; text-align: center; margin-top: 20px; margin-bottom: 30px;">
                        <span style="color: #888888; font-size: 0.8rem; letter-spacing: 2px;">RÉSULTAT DE LA MODÉLISATION</span><br><br>
                        <span style="font-size: 1.2rem; color: #ffffff;">EXPOSITION TOTALE : <strong>{cap_investi:,.0f} €</strong></span> &nbsp;&nbsp;|&nbsp;&nbsp; 
                        <span style="font-size: 1.2rem; color: #ffffff;">VALEUR LIQUIDATIVE : <strong>{val_finale:,.0f} €</strong></span><br><br>
                        <span style="font-size: 1rem; color: {'#a3b18a' if pv >=0 else '#880000'};">PNL NET : {pv:,.0f} € ({(pv/cap_investi)*100:.2f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    fig_dca = go.Figure()
                    fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Investi'], name="CAPITAL ALLOUÉ", line=dict(color="#555555", dash='dash', width=2)))
                    fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Valeur'], name="VALEUR DU PORTEFEUILLE", fill='tozeroy', line=dict(color="#ffffff", width=2), fillcolor="rgba(255,255,255,0.05)"))
                    fig_dca.update_layout(
                        height=500, 
                        template="plotly_dark", 
                        paper_bgcolor='#050505',
                        plot_bgcolor='#0a0a0a',
                        margin=dict(l=0, r=0, t=20, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='#1a1a1a'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_dca, use_container_width=True)
                else:
                    st.error("PROFONDEUR DE DONNÉES INSUFFISANTE POUR LA MODÉLISATION.")

            with tabs[3]:
                st.markdown(generate_consensus_and_verdict(data, is_etf, nom), unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("#### INTELLIGENCE DE MARCHÉ (FLUX DIRECT)")
                
                news = get_morningstar_news(ticker_input, nom)
                if news:
                    for n in news:
                        st.markdown(f"""
                        <div style="background:#0a0a0a; padding:15px; border: 1px solid #1a1a1a; border-left:2px solid #555555; margin-bottom:15px; transition: all 0.3s ease;">
                            <a href="{n['link']}" target="_blank" style="color:#ffffff; font-weight:300; text-decoration:none; font-size: 1.1rem; letter-spacing: 0.5px;">{n['title']}</a><br>
                            <span style="color:#555555; font-size:0.75rem; text-transform: uppercase; letter-spacing: 1px; display: inline-block; margin-top: 8px;">SOURCE : {n['publisher']} // TIMESTAMP : {n['published']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("FLUX D'INFORMATION MUET.")


elif mode == "MATRICE COMPARATIVE":
    st.markdown("#### INJECTION MULTI-ACTIFS")
    tickers_input = st.text_input("", placeholder="IDENTIFIANTS (EX: AAPL, MSFT, LVMH.PA)", label_visibility="collapsed").upper()
    st.markdown("<br>", unsafe_allow_html=True)
    
    if tickers_input:
        if st.button("EXÉCUTER L'ALGORITHME DE COMPARAISON"):
            with st.spinner("ACQUISITION ET TRAITEMENT VECTORIEL..."):
                t_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
                res = []
                
                # Progress bar custom
                progress_bar = st.progress(0)
                
                for i, t in enumerate(t_list):
                    try:
                        info = fetch_info_with_retry(t)
                        if not info: continue
                        fx = get_fx_rate(info.get('currency', 'USD'))
                        
                        if info.get('quoteType') == 'ETF':
                            d = extract_etf_data(info, t, fx)
                            res.append({'TICKER': t, 'TYPE': 'ETF', 'PRIX (€)': d['Prix'], 'SCORE': 0, 'DETTE/EBITDA': None, 'PER': None, 'MARGE NETTE': None})
                        else:
                            d = extract_stock_data(info, fx)
                            res.append({'TICKER': t, 'TYPE': 'EQUITY', 'PRIX (€)': d['Prix'], 'SCORE': d['Score'], 'DETTE/EBITDA': d['Levier'] if isinstance(d['Levier'], (int, float)) else None, 'PER': d['PER_Actuel'], 'MARGE NETTE': d['Marge_Nette']})
                    except Exception: pass
                    
                    progress_bar.progress((i + 1) / len(t_list))
                
                time.sleep(0.5)
                progress_bar.empty()
                
                if res:
                    df = pd.DataFrame(res).sort_values(by="SCORE", ascending=False)
                    
                    # Formatting DataFrame pour affichage propre dans Streamlit
                    styled_df = df.style.format({
                        'PRIX (€)': "{:.2f}",
                        'SCORE': "{:.0f}",
                        'DETTE/EBITDA': "{:.2f}",
                        'PER': "{:.2f}",
                        'MARGE NETTE': "{:.2f}%"
                    }, na_rep="—")
                    
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button("EXPORTER LA MATRICE (CSV)", data=csv, file_name="alpha_matrix.csv", mime="text/csv")
                else: 
                    st.error("ÉCHEC TOTAL DE L'EXTRACTION.")
