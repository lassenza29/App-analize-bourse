import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import feedparser
import urllib.parse

# ==============================================================================
# CONFIGURATION DE LA PAGE & DESIGN UI/UX "BENTO BOX"
# ==============================================================================
st.set_page_config(
    page_title="Alpha Terminal Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injection du CSS Avancé (Style Dribbble / Bento Box)
st.markdown("""
<style>
    /* Fond global ultra-sombre et police */
    .stApp { background-color: #09090b; color: #ededed; font-family: 'Inter', sans-serif; }
    
    /* Masquer les éléments natifs Streamlit pour un look d'application pure */
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Titres globaux */
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; letter-spacing: -0.5px; }
    
    /* Bento Card Principale */
    .bento-card {
        background: linear-gradient(145deg, #121214 0%, #0d0d0f 100%);
        border: 1px solid #27272a;
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .bento-card:hover {
        border-color: #3f3f46;
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
    }
    
    /* Titre des cartes */
    .bento-header {
        font-size: 0.9rem;
        color: #a1a1aa;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 16px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Grille de métriques à l'intérieur des cartes */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 20px;
    }
    
    /* Élément métrique individuel */
    .metric-item { display: flex; flex-direction: column; }
    .metric-label { font-size: 0.85rem; color: #71717a; margin-bottom: 4px; }
    .metric-value { font-size: 1.6rem; color: #ffffff; font-weight: 700; letter-spacing: -0.5px; }
    .metric-value.highlight { color: #3b82f6; /* Bleu électrique */ }
    .metric-value.success { color: #10b981; /* Vert émeraude */ }
    .metric-value.danger { color: #ef4444; /* Rouge corail */ }
    
    /* Score Géant */
    .score-display {
        font-size: 4.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        margin: 10px 0;
    }
    
    /* Verdict de l'expert */
    .expert-verdict-box {
        background-color: #18181b;
        border-left: 4px solid #3b82f6;
        padding: 20px;
        border-radius: 0 16px 16px 0;
        margin-top: 10px;
    }
    .verdict-buy { border-left-color: #10b981; }
    .verdict-hold { border-left-color: #f59e0b; }
    .verdict-sell { border-left-color: #ef4444; }
    
    /* Stylisation des Tabs Streamlit pour correspondre au design */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #18181b; 
        border: 1px solid #27272a; 
        border-radius: 100px; 
        padding: 8px 24px;
        color: #a1a1aa;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #fafafa !important; 
        color: #09090b !important; 
        border-color: #fafafa !important;
    }
    
    /* Barre de recherche personnalisée */
    .stTextInput input {
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 1.1rem !important;
    }
    .stTextInput input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 1px #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# MOTEUR DE TRAITEMENT ET CONVERSION
# ==============================================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    if not currency_code or not isinstance(currency_code, str): return 1.0
    curr = currency_code.upper().strip()
    is_pence = False
    if curr in ["GBP", "GBX", "GBP=X", "GBp"]:
        is_pence = (curr in ["GBX", "GBp"])
        curr = "GBP"
    if curr == "EUR": return 0.01 if is_pence else 1.0

    fallbacks = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "CAD": 0.68, "JPY": 0.006, "AUD": 0.60, "CNY": 0.13}
    try:
        data = yf.Ticker(f"{curr}EUR=X").history(period="1d")
        if not data.empty:
            rate = float(data['Close'].iloc[-1])
            return (rate * 0.01) if is_pence else rate
    except Exception: pass
    rate = fallbacks.get(curr, 1.0)
    return (rate * 0.01) if is_pence else rate

def safe_float(val, multiplier=1.0, precision=2):
    if val is None or pd.isna(val) or val == "": return None
    try: return round(float(val) * multiplier, precision)
    except Exception: return None

def safe_str(val):
    if val is None or pd.isna(val) or val == "": return "N/A"
    return str(val)

def format_metric(val, suffix="", special_class=""):
    if val is None: return "<span style='color:#71717a'>N/A</span>"
    if isinstance(val, str) and val.lower() == "cash positif": return "<span class='metric-value success'>Cash Positif</span>"
    if isinstance(val, str): return f"<span class='metric-value {special_class}'>{val}</span>"
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"<span class='metric-value {special_class}'>{formatted} <span style='font-size:1rem;color:#71717a'>{suffix}</span></span>"

def render_bento_box(title, icon, metrics_dict):
    """Génère une carte Bento avec une grille de métriques"""
    html = f"""
    <div class="bento-card">
        <div class="bento-header"><span>{icon}</span> {title}</div>
        <div class="metric-grid">
    """
    for label, val_html in metrics_dict.items():
        html += f"""
            <div class="metric-item">
                <div class="metric-label">{label}</div>
                <div>{val_html}</div>
            </div>
        """
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)


# ==============================================================================
# ABSTRACTION DES DONNÉES
# ==============================================================================
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
    d['Reco'] = reco_raw.replace('_', ' ').title() if isinstance(reco_raw, str) else 'N/A'
    
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
    d['Sector'] = safe_str(info.get('sector'))
    
    return d

def extract_etf_data(info, ticker_symbol, fx_rate):
    d = {}
    d['Prix'] = safe_float(info.get('navPrice') or info.get('previousClose') or info.get('regularMarketPrice'), fx_rate)
    d['TER'] = safe_float(info.get('annualReportExpenseRatio') or info.get('ytdReturn'), 100)
    d['AUM'] = safe_float(info.get('totalAssets'), fx_rate / 1_000_000)
    name = str(info.get('longName', '')).upper()
    d['Distribution'] = "Capitalisation" if " ACC" in name or "ACCUM" in name else "Distribution"
    d['Replication'] = "Synthétique" if "SWAP" in name else "Physique"
    is_pea = any(x in name for x in ["AMUNDI", "LYXOR", "BNP"]) and ".PA" in ticker_symbol.upper()
    d['PEA'] = "Éligible PEA" if is_pea else "CTO Uniquement"
    return d


# ==============================================================================
# FLUX D'ACTUALITÉS RSS
# ==============================================================================
@st.cache_data(ttl=1800)
def get_morningstar_news(ticker_symbol):
    news = []
    try:
        clean_ticker = ticker_symbol.split('.')[0]
        query = f'"{clean_ticker}" (site:morningstar.fr OR site:morningstar.com)'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            title = entry.title.rsplit(' - ', 1)[0] if ' - ' in entry.title else entry.title
            news.append({
                'title': title, 'link': entry.link, 'publisher': 'Morningstar',
                'published': entry.published[5:16] if hasattr(entry, 'published') else 'Récemment'
            })
    except Exception: pass

    if not news:
        try:
            tk_news = yf.Ticker(ticker_symbol).news
            for n in tk_news[:5]:
                news.append({
                    'title': n.get('title', 'Actualité'), 'link': n.get('link', '#'),
                    'publisher': n.get('publisher', 'Yahoo Finance'), 'published': 'Récemment'
                })
        except Exception: pass
    return news


def calculer_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    return 100 - (100 / (1 + (gain / loss)))


# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================
col_search, _ = st.columns([1, 2])
with col_search:
    ticker_input = st.text_input("Recherche", placeholder="Saisir un Ticker (ex: AAPL, CW8.PA)", label_visibility="collapsed").upper().strip()

if ticker_input:
    if "," in ticker_input:
        st.warning("Le mode comparateur n'est pas optimisé pour l'affichage Bento. Veuillez saisir un seul ticker.")
        st.stop()
        
    with st.spinner("Analyse quantitative en cours..."):
        try:
            tk = yf.Ticker(ticker_input)
            info = tk.info
            if not info or ('symbol' not in info and 'regularMarketPrice' not in info and 'currentPrice' not in info):
                st.error("Ticker introuvable ou non valide.")
                st.stop()
                
            nom = info.get('longName', info.get('shortName', ticker_input))
            devise = info.get('currency', 'USD')
            fx_rate = get_fx_rate(devise)
            is_etf = info.get('quoteType') == 'ETF'
            
            # HEADER DU DECK
            st.markdown(f"<h1 style='margin-bottom:0;'>{nom} <span style='color:#71717a; font-weight:400;'>{ticker_input}</span></h1>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            tabs = st.tabs(["Overview & Fondamentaux", "Analyse Technique", "Simulateur DCA", "Intelligence & Presse"])
            
            with tabs[0]:
                if is_etf:
                    data = extract_etf_data(info, ticker_input, fx_rate)
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        html_nav = f"""
                        <div class="bento-card" style="text-align:center; padding: 40px 20px;">
                            <div class="bento-header" style="justify-content:center;">NAV Actuelle</div>
                            <div class="score-display">{format_metric(data['Prix'], '€', 'highlight')}</div>
                        </div>
                        """
                        st.markdown(html_nav, unsafe_allow_html=True)
                        
                    with col2:
                        render_bento_box("Structure du Fonds", "🏛️", {
                            "Encours (AUM)": format_metric(data['AUM'], "M€", "success" if data['AUM'] and data['AUM']>100 else "danger"),
                            "Frais (TER)": format_metric(data['TER'], "%"),
                            "Politique": format_metric(data['Distribution']),
                            "Réplication": format_metric(data['Replication']),
                            "Enveloppe": format_metric(data['PEA'], "", "highlight" if "PEA" in data['PEA'] else "")
                        })

                else:
                    data = extract_stock_data(info, fx_rate)
                    
                    # SECTION 1 : HIGHLIGHTS (Bento haut)
                    col_score, col_prix, col_croissance = st.columns([1, 1.5, 1.5])
                    with col_score:
                        html_score = f"""
                        <div class="bento-card" style="text-align:center; height:100%;">
                            <div class="bento-header" style="justify-content:center;">Score Alpha</div>
                            <div class="score-display">{data['Score']}</div>
                            <div class="metric-label" style="margin-top:10px;">Sur 100 points</div>
                        </div>
                        """
                        st.markdown(html_score, unsafe_allow_html=True)
                        
                    with col_prix:
                        render_bento_box("Marché & Consensus", "📈", {
                            "Prix Actuel": format_metric(data['Prix'], "€", "highlight"),
                            "Objectif Moyen": format_metric(data['Target'], "€"),
                            "Recommandation": format_metric(data['Reco'], "", "success" if "Buy" in str(data['Reco']) else ""),
                            "Secteur": format_metric(data.get('Sector'))
                        })
                        
                    with col_croissance:
                        render_bento_box("Moteurs de Croissance", "🚀", {
                            "Croissance CA": format_metric(data['Rev_Growth'], "%", "success" if data['Rev_Growth'] and data['Rev_Growth']>0 else "danger"),
                            "Marge Nette": format_metric(data['Marge_Nette'], "%", "highlight"),
                            "ROE": format_metric(data['ROE'], "%"),
                            "BPA": format_metric(data['BPA'], "€")
                        })
                    
                    # SECTION 2 : DATA GRID (Bento bas)
                    col_val, col_sante = st.columns(2)
                    with col_val:
                        render_bento_box("Métriques de Valorisation", "⚖️", {
                            "PER Actuel": format_metric(data['PER_Actuel'], "x"),
                            "PER Futur": format_metric(data['PER_Futur'], "x"),
                            "Price / Sales": format_metric(data['PS'], "x"),
                            "Prix de Graham": format_metric(data['Graham'], "€")
                        })
                    with col_sante:
                        render_bento_box("Santé Financière", "🛡️", {
                            "Levier (Dette/EBITDA)": format_metric(data['Levier'], "x"),
                            "Dette Nette": format_metric(data['Dette_Nette'], "M€"),
                            "Current Ratio": format_metric(data['Current_Ratio'], "x"),
                            "Payout Ratio": format_metric(data['Payout'], "%")
                        })

            with tabs[1]:
                hist = tk.history(period="3y")
                if len(hist) > 100:
                    hist['Close_EUR'] = hist['Close'] * fx_rate
                    hist['SMA50'] = hist['Close_EUR'].rolling(50).mean()
                    hist['SMA200'] = hist['Close_EUR'].rolling(200).mean()
                    
                    st.markdown("""<div class="bento-card" style="padding:10px;"><div class="bento-header" style="margin:10px 0 0 10px;">Price Action & Moyennes Mobiles</div>""", unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close_EUR'], name="Prix", line=dict(color="#ffffff", width=2)))
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color="#3b82f6", width=1.5)))
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color="#f59e0b", width=1.5, dash='dot')))
                    
                    fig.update_layout(
                        height=500, 
                        template="plotly_dark", 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    fig.update_xaxes(showgrid=False)
                    fig.update_yaxes(showgrid=True, gridcolor='#27272a')
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("Historique insuffisant.")

            with tabs[2]:
                st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
                st.markdown("<div class='bento-header'>Paramètres d'Investissement Programmé</div>", unsafe_allow_html=True)
                
                c_in1, c_in2 = st.columns(2)
                mensualite = c_in1.number_input("Montant mensuel investi (€)", min_value=10, value=200, step=10)
                duree = c_in2.selectbox("Horizon d'investissement", ["1y", "3y", "5y", "10y"], index=2)
                
                dca_hist = tk.history(period=duree)
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
                        
                    val_finale = val_list[-1]
                    pv = val_finale - cap_investi
                    renta = (pv / cap_investi) * 100
                    
                    # Affichage des résultats DCA façon Bento
                    st.markdown("<br>", unsafe_allow_html=True)
                    res_col1, res_col2, res_col3 = st.columns(3)
                    with res_col1: st.markdown(f"<div class='metric-item'><div class='metric-label'>Capital Investi</div><div class='metric-value'>{cap_investi:,.0f} €</div></div>", unsafe_allow_html=True)
                    with res_col2: st.markdown(f"<div class='metric-item'><div class='metric-label'>Valeur Finale</div><div class='metric-value highlight'>{val_finale:,.0f} €</div></div>", unsafe_allow_html=True)
                    with res_col3: st.markdown(f"<div class='metric-item'><div class='metric-label'>Performance</div><div class='metric-value {'success' if pv>0 else 'danger'}'>{renta:+.2f} %</div></div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    fig_dca = go.Figure()
                    fig_dca.add_trace(go.Scatter(x=monthly.index, y=cap_list, name="Investissement", line=dict(color="#71717a", dash='dash')))
                    fig_dca.add_trace(go.Scatter(x=monthly.index, y=val_list, name="Portefeuille", fill='tozeroy', line=dict(color="#10b981")))
                    fig_dca.update_layout(height=350, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0))
                    st.plotly_chart(fig_dca, use_container_width=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

            with tabs[3]:
                c_news, c_verdict = st.columns([2, 1])
                
                with c_news:
                    st.markdown("<div class='bento-card'><div class='bento-header'>📰 Flux d'Actualités Récent</div>", unsafe_allow_html=True)
                    news = get_morningstar_news(ticker_input)
                    if news:
                        for n in news:
                            st.markdown(f"""
                            <div style="padding: 15px 0; border-bottom: 1px solid #27272a;">
                                <a href="{n['link']}" target="_blank" style="color:#e6edf3; font-weight:500; font-size:1.05rem; text-decoration:none; display:block; margin-bottom:5px;">{n['title']}</a>
                                <span style="color:#71717a; font-size:0.85rem;">{n['publisher']} • {n['published']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Aucune actualité disponible.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with c_verdict:
                    st.markdown("<div class='bento-card'><div class='bento-header'>🧠 Analyse IA</div>", unsafe_allow_html=True)
                    if is_etf:
                        verdict = "Achat" if (data['AUM'] and data['AUM'] > 100) and (data['TER'] and data['TER'] < 0.3) else "Conservation"
                        v_class = "verdict-buy" if verdict == "Achat" else "verdict-hold"
                        st.markdown(f"""
                        <div class="expert-verdict-box {v_class}">
                            <h3 style="margin-top:0; font-size:1.4rem;">{verdict}</h3>
                            <p style="color:#a1a1aa; font-size:0.95rem; line-height:1.5;">Fonds indiciel {data.get('Replication', '')}. Liquidité {'optimale' if (data['AUM'] or 0)>100 else 'à surveiller'} ({format_metric(data['AUM'], 'M€')}). Frais structurels à {format_metric(data['TER'], '%')}.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        score = data.get('Score', 0)
                        if score >= 65: verdict, v_class = "Achat Fort", "verdict-buy"
                        elif score >= 50: verdict, v_class = "Accumulation", "verdict-buy"
                        elif score >= 35: verdict, v_class = "Conservation", "verdict-hold"
                        else: verdict, v_class = "Allègement", "verdict-sell"
                        st.markdown(f"""
                        <div class="expert-verdict-box {v_class}">
                            <h3 style="margin-top:0; font-size:1.4rem;">{verdict}</h3>
                            <p style="color:#a1a1aa; font-size:0.95rem; line-height:1.5;">Valorisation {'attractive' if data['Graham'] and data['Prix'] and data['Graham']>data['Prix'] else 'exigeante'}. Rentabilité des capitaux (ROE: {format_metric(data['ROE'], '%')}) et gestion de la dette ({format_metric(data['Levier'], 'x')}) alignées avec la recommandation actuelle.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erreur lors de la génération du tableau de bord. Vérifiez le Ticker.")
