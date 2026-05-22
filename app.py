import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import math
import feedparser
import urllib.parse
import time

# ==============================================================================
# 1. CONFIGURATION ET DESIGN UI/UX (STYLE PHOTO LIGHT/PRO)
# ==============================================================================
st.set_page_config(page_title="Terminal Financier Pro", page_icon="🏛️", layout="wide")

# Design personnalisé via CSS pour style "Light / Pro / Cold"
st.markdown("""
<style>
    /* Global Styles */
    .stApp { background-color: #fdfdfd; color: #212121; }
    h1, h2, h3, h4, h5 { color: #1a1a1a !important; font-weight: 300 !important; letter-spacing: -0.5px; }
    
    /* Metrics Cards - Style "Light / Bloomberg" */
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Score Container */
    .score-container {
        text-align: center;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 4px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .score-title { font-size: 1rem; color: #616161; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .score-val { font-size: 3.5rem; font-weight: 800; color: #1a73e8; line-height: 1; }
    
    /* Tabs style minimaliste */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #e0e0e0; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; padding: 10px 15px; color: #616161; }
    .stTabs [aria-selected="true"] { background-color: #f1f3f4; color: #1a73e8; border-bottom: 2px solid #1a73e8; }
    
    /* News style minimaliste */
    .news-box {
        background-color: #ffffff;
        padding: 15px;
        border-left: 3px solid #1a73e8;
        border-radius: 0 4px 4px 0;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. MOTEUR DE CALCULS ET CONVERSION
# ==============================================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    """Récupère le taux de change vers l'Euro pour afficher tout en €"""
    if not currency_code or not isinstance(currency_code, str): return 1.0
    curr = currency_code.upper().strip()
    is_pence = False
    if curr in ["GBP", "GBX", "GBp"]:
        is_pence = (curr in ["GBX", "GBp"]); curr = "GBP"
    if curr == "EUR": return 0.01 if is_pence else 1.0
    
    fallbacks = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "CAD": 0.68, "JPY": 0.006}
    try:
        data = yf.Ticker(f"{curr}EUR=X").history(period="1d")
        if not data.empty:
            rate = float(data['Close'].iloc[-1])
            return (rate * 0.01) if is_pence else rate
    except Exception: pass
    return (fallbacks.get(curr, 1.0) * 0.01) if is_pence else fallbacks.get(curr, 1.0)

def safe_float(val, multiplier=1.0, precision=2):
    if val is None or pd.isna(val) or val == "": return None
    try: return round(float(val) * multiplier, precision)
    except Exception: return None

def calculer_rsi(data, window=14):
    """Calcule le Relative Strength Index (RSI)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ==============================================================================
# 3. MOTEUR DE TRAITEMENT DONNÉES (ACTION/ETF/SMALL CAPS/SCORING)
# ==============================================================================
@st.cache_data(ttl=600)
def extract_master_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    try: info = ticker.info
    except Exception: return None
    
    devise = info.get('currency', 'EUR')
    fx_rate = get_fx_rate(devise)
    is_etf = info.get('quoteType') == 'ETF' or 'totalAssets' in info

    d = {}
    d['info'] = info
    d['ticker'] = ticker
    d['is_etf'] = is_etf
    d['nom'] = info.get('longName', info.get('shortName', ticker_symbol))
    d['cap'] = safe_float(info.get('marketCap', info.get('totalAssets', 0)), fx_rate / 1_000_000)
    
    if is_etf:
        d['ter'] = safe_float(info.get('annualReportExpenseRatio'), 100)
    else:
        # Bilan
        treso = safe_float(info.get('totalCash'), fx_rate / 1_000_000)
        dette_b = safe_float(info.get('totalDebt'), fx_rate / 1_000_000)
        ebitda = safe_float(info.get('ebitda'), fx_rate / 1_000_000)
        dette_n = dette_b - treso if treso is not None and dette_b is not None else None
        
        if ebitda and ebitda > 0:
            d['levier'] = "Cash Positif" if dette_n < 0 else round(dette_n / ebitda, 2)
        else: d['levier'] = None
        
        d['roe'] = safe_float(info.get('returnOnEquity'), 100)
        d['marge_nette'] = safe_float(info.get('profitMargins'), 100)
        
        # Graham
        bna = safe_float(info.get('trailingEps'), fx_rate)
        actif_net_a = safe_float(info.get('bookValue'), fx_rate)
        if bna and actif_net_a and bna > 0 and actif_net_a > 0:
            d['graham'] = round(math.sqrt(22.5 * bna * actif_net_a), 2)
        else: d['graham'] = None
        
        d['per'] = safe_float(info.get('trailingPE'))
        d['current_ratio'] = safe_float(info.get('currentRatio'))
        d['rev_growth'] = safe_float(info.get('revenueGrowth'), 100)
        d['payout'] = safe_float(info.get('payoutRatio'), 100)
        d['target'] = safe_float(info.get('targetMeanPrice'), fx_rate)
        d['prix'] = safe_float(info.get('currentPrice'), fx_rate)

        # SCORING ALGORITHMIQUE (Sur 100)
        score = 0
        if d['levier'] is not None and (d['levier'] == "Cash Positif" or d['levier'] < 2.5): score += 15
        if d['roe'] is not None and d['roe'] > 15: score += 15
        if d['marge_nette'] is not None and d['marge_nette'] > 12: score += 15
        if d['graham'] is not None and d['prix'] is not None and d['graham'] > d['prix']: score += 15
        if d['per'] is not None and 0 < d['per'] < 22: score += 10
        if d['current_ratio'] is not None and d['current_ratio'] > 1.2: score += 10
        if d['rev_growth'] is not None and d['rev_growth'] > 5: score += 10
        if d['payout'] is not None and 0 < d['payout'] < 60: score += 10
        d['score'] = score
    
    return d

# ==============================================================================
# 4. MOTEUR D'ACTUALITÉS (RSS Morningstar)
# ==============================================================================
@st.cache_data(ttl=1800)
def get_morningstar_news(ticker_symbol, company_name):
    news = []
    try:
        clean_ticker = ticker_symbol.split('.')[0]
        query = f'"{clean_ticker}" OR "{company_name}" site:morningstar.fr'
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=fr&gl=FR&ceid=FR:fr"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            title = entry.title.rsplit(' - ', 1)[0] if ' - ' in entry.title else entry.title
            news.append({
                'title': title,
                'link': entry.link,
                'published': entry.published[5:16] if hasattr(entry, 'published') else 'Récemment'
            })
    except Exception: pass
    return news

# ==============================================================================
# 5. PREDEFINITIONS TICKERS (MODELS TOP PICK)
# ==============================================================================
@st.cache_data(ttl=3600)
def get_top_picks_df():
    # Listes définies de manière institutionnelle sur la base de la capitalisation et/ou qualité
    top_small_caps = ["FDJ.PA", "RCO.PA", "KRI.PA", "MDM.PA", "ALD.PA"]
    top_etf = ["CW8.PA", "ESE.PA", "WLD.PA", "EURE.PA"]
    top_stocks = ["LVMH.PA", "OR.PA", "HER.PA", "SU.PA", "AIR.PA", "TTE.PA"]
    
    all_picks = []
    
    for category, tickers in [("SMALL CAPS (€)", top_small_caps), ("ETFs GLOBAL (€)", top_etf), ("ACTIONS CAC 40", top_stocks)]:
        for t in tickers:
            data = extract_master_data(t)
            if data:
                entry = {
                    "Ticker": t, "Nom": data['nom'], "Type": category, 
                    "Capitalisation (M€)": data['cap'], "Score (/100)": data.get('score', 0)
                }
                if data['is_etf']:
                    entry["PER"] = None; entry["Marge Nette"] = None
                else:
                    entry["PER"] = data['per']; entry["Marge Nette"] = data['marge_nette']
                all_picks.append(entry)
                
    df = pd.DataFrame(all_picks)
    return df

# ==============================================================================
# 6. INTERFACE STREAMLIT PRINCIPALE
# ==============================================================================
tabs_top = st.tabs(["📊 ANALYSE INDIVIDUELLE", "⚖️ COMPARATEUR MATRICE"])

# --- ONGLET 1 : ANALYSE INDIVIDUELLE ---
with tabs_top[0]:
    # Sidebar
    st.sidebar.markdown("### 🔍 SÉLECTEURS DE RÉFÉRENCE")
    with st.spinner("Actualisation des Top Picks..."):
        all_picks_df = get_top_picks_df()
        
        selected_stock = st.sidebar.selectbox("BEST STOCKS (Scoring)", all_picks_df[all_picks_df['Type'] == "ACTIONS CAC 40"].sort_values(by="Score (/100)", ascending=False)['Ticker'])
        selected_etf = st.sidebar.selectbox("BEST ETFs (Liquidité/TER)", all_picks_df[all_picks_df['Type'] == "ETFs GLOBAL (€)"].sort_values(by="Score (/100)", ascending=False)['Ticker'])
        selected_small = st.sidebar.selectbox("BEST SMALL CAPS", all_picks_df[all_picks_df['Type'] == "SMALL CAPS (€)"].sort_values(by="Score (/100)", ascending=False)['Ticker'])

    st.sidebar.markdown("---")
    ticker_input = st.text_input("RECHERCHE", placeholder="Saisir symbole (ex: AAPL, RMS.PA, CW8.PA)...", value=selected_stock or selected_etf or selected_small or "AAPL").upper().strip()
    
    if ticker_input:
        with st.spinner("Génération du rapport d'analyse institutionnel..."):
            d = extract_master_data(ticker_input)
            
            if d:
                # EN-TÊTE ET SCORE
                col_head1, col_head2 = st.columns([3, 1])
                with col_head1:
                    st.title(f"{d['nom']} <span style='font-size:1.5rem; color:#757575'>| {ticker_input}</span>")
                    st.markdown(f"Capitalisation : **{d['cap']:,.0f} M€**")
                
                with col_head2:
                    if not d['is_etf']:
                        st.markdown(f'<div class="score-container"><div class="score-title">SCORE FINANCIER</div><div class="score-val">{d["score"]}</div></div>', unsafe_allow_html=True)

                # ONGLET DE NAVIGATION INTERNE
                tab_metrics, tab_graph, tab_history, tab_news = st.tabs(["🏢 MÉTRIQUES CLÉS", "📈 ANALYSE TECHNIQUE", "🕰️ HISTORIQUE MÉTRIQUES", "📰 ACTUALITÉS"])

                # --- MÉTRIQUES CLÉS ---
                with tab_metrics:
                    if d['is_etf']:
                        st.header("📊 Fiche d'Identité ETF")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("NAV Actuelle (€)", f"{d['info'].get('navPrice', 0):,.2f}")
                        c2.metric("Frais TER", f"{d['ter']:.2f}%" if d['ter'] else "N/A")
                        c3.metric("Encours (M€)", f"{d['cap']:,.0f}")
                        c4.metric("Rendement Yield", f"{safe_float(d['info'].get('trailingAnnualDividendYield'), 100):.2f}%" or "N/A / Acc")
                    else:
                        st.header("🏢 Valorisation & Santé (Action)")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Prix Actuel (€)", f"{d['prix']:,.2f}")
                        c2.metric("PER (x)", f"{d['per']:.2f}" if d['per'] else "N/A")
                        c3.metric("Marge Nette", f"{d['marge_nette']:.2f}%" if d['marge_nette'] else "N/A")
                        c4.metric("Dette / EBITDA (x)", f"{d['levier']:.2f}" if isinstance(d['levier'], float) else d['levier'] or "N/A")

                        c5, c6, c7, c8 = st.columns(4)
                        c5.metric("Graham (€)", f"{d['graham']:,.2f}" if d['graham'] else "N/A")
                        c6.metric("Consensus Target (€)", f"{d['target']:,.2f}" if d['target'] else "N/A")
                        c7.metric("ROE", f"{d['roe']:.2f}%" if d['roe'] else "N/A")
                        c8.metric("Revenue Growth", f"{d['rev_growth']:.2f}%" if d['rev_growth'] else "N/A")

                # --- ANALYSE TECHNIQUE ---
                with tab_graph:
                    st.header("📈 Graphique Technique Interactif (MM50/MM200 & RSI)")
                    hist = d['ticker'].history(period="3y")
                    if len(hist) > 200:
                        hist['SMA50'] = hist.Close.rolling(50).mean()
                        hist['SMA200'] = hist.Close.rolling(200).mean()
                        hist['RSI'] = calculer_rsi(hist.Close)
                        
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.Close, name="Prix (€)", line=dict(color="#1a73e8", width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.SMA50, name="MM50 Jours", line=dict(color="#f4b400", width=1, dash='dot')), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.SMA200, name="MM200 Jours", line=dict(color="#db4437", width=1, dash='dot')), row=1, col=1)
                        
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.RSI, name="RSI (14)", line=dict(color="#a142f4", width=1)), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="#db4437", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#0f9d58", row=2, col=1)
                        
                        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=600, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.warning("Données historiques insuffisantes pour l'analyse technique.")

                # --- HISTORIQUE MÉTRIQUES (REMPlACE DCA) ---
                with tab_history:
                    if d['is_etf']:
                        st.header("🕰️ Historique de l'Encours et NAV (ETF)")
                        hist_5y = d['ticker'].history(period="5y")
                        if len(hist_5y) > 100:
                            fig_aum = go.Figure()
                            fig_aum.add_trace(go.Scatter(x=hist_5y.index, y=hist_5y.Close, name="NAV Actuelle (€)", line=dict(color="#1a73e8")))
                            fig_aum.update_layout(template="plotly_white", title="Évolution de la NAV (Cours de Clôture, 5 Ans)", yaxis_title="Euros (€)")
                            st.plotly_chart(fig_aum, use_container_width=True)
                        else: st.info("Historique de l'encours non disponible pour ce fonds.")

                    else:
                        st.header("🕰️ Évolution de la Valorisation et Rentabilité (5 Ans)")
                        metrics_hist = d['ticker'].history(period="5y")[['Close', 'Volume']]
                        
                        # Récupération états financiers historiques si possible
                        financials = d['ticker'].financials # Compte de résultat
                        balance = d['ticker'].balance_sheet # Bilan

                        if financials is not None and balance is not None and not financials.empty:
                            hist_roe, hist_marge = [], []
                            dates_f = financials.columns
                            
                            for date in dates_f:
                                try:
                                    net_income = financials.loc['Net Income'].get(date, None)
                                    revenue = financials.loc['Total Revenue'].get(date, None)
                                    equity = balance.loc['Total Stockholder Equity'].get(date, None)
                                    
                                    if net_income and revenue and equity:
                                        hist_marge.append(net_income / revenue * 100)
                                        hist_roe.append(net_income / equity * 100)
                                except Exception: pass

                            # Graphique évolution marges/ROE
                            fig_hist = go.Figure()
                            fig_hist.add_trace(go.Scatter(x=dates_f, y=hist_roe, name="ROE (%)", line=dict(color="#1a73e8", width=2)))
                            fig_hist.add_trace(go.Scatter(x=dates_f, y=hist_marge, name="Marge Nette (%)", line=dict(color="#109d58", width=2, dash='dash')))
                            fig_hist.update_layout(template="plotly_white", title="Tendance Rentabilité Historique", yaxis_title="Pourcentage (%)")
                            st.plotly_chart(fig_hist, use_container_width=True)

                # --- ACTUALITÉS ---
                with tab_news:
                    st.header(f"📰 Actualités Morningstar France")
                    news = get_morningstar_news(ticker_input, d['nom'])
                    if news:
                        for n in news:
                            st.markdown(f"""
                            <div class="news-box">
                                <a href="{n['link']}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:none;">{n['title']}</a><br>
                                <span style="color:#757575; font-size:0.85rem;">Publié le {n['published']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Aucune actualité récente disponible pour cet actif.")

            else:
                st.error("Échec de l'acquisition des données fondamentales.")

# --- ONGLET 2 : COMPARATEUR MATRICE ---
with tabs_top[1]:
    st.header("⚖️ Comparateur Quantitatif Multi-Actifs (Matrice Pro)")
    st.markdown("Comparez instantanément la valorisation et la rentabilité d'une liste d'actions ou d'ETF.")
    
    # Amélioration UI comparateur : liste plus claire, boutons d'exportation
    tickers_input = st.text_input("Entrez les symboles séparés par des virgules (ex: AAPL, LVMH.PA, RMS.PA, OR.PA)", value="AAPL, MSFT, LVMH.PA, RMS.PA")
    lista_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    
    col_comp1, col_comp2 = st.columns([3, 1])
    with col_comp1:
        if st.button("Lancer la Comparaison Vectorielle"):
            resultats_comp = []
            with st.spinner("Analyse quantitative des actifs en Euros..."):
                for t in lista_tickers:
                    d = extract_master_data(t)
                    if d:
                        res = {
                            "Ticker": t, "Nom": d['nom'], "Score (/100)": d.get('score', 0),
                            "Capitalisation (M€)": round(d['cap'], 0), "is_etf": d['is_etf']
                        }
                        if not d['is_etf']:
                            res["Prix Graham (€)"] = d.get('graham', None)
                            res["PER (x)"] = d.get('per', None)
                            res["Marge Nette (%)"] = d.get('marge_nette', None)
                            res["ROE (%)"] = d.get('roe', None)
                            res["Dette/EBITDA (x)"] = d.get('levier', None) if isinstance(d.get('levier'), float) else None
                        else:
                            res["Frais TER"] = d.get('ter', None)
                        
                        resultats_comp.append(res)
            
            if resultats_comp:
                df_matrix = pd.DataFrame(resultats_comp)
                
                # Formatage et coloration conditionnelle (style gradient Vert pour le score)
                st.dataframe(
                    df_matrix.set_index("Ticker").style.background_gradient(subset=['Score (/100)'], cmap='Greens', vmin=0, vmax=100),
                    use_container_width=True
                )
                
                # Export CSV amélioré
                st.markdown("---")
                csv = df_matrix.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Télécharger le rapport de matrice au format CSV", data=csv, file_name="matrice_alpha_engine.csv", mime="text/csv", use_container_width=True)
            else:
                st.error("Aucune donnée n'a pu être récupérée pour la comparaison.")
