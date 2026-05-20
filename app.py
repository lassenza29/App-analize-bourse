import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import math
import feedparser
import requests
from bs4 import BeautifulSoup

# ==============================================================================
# 0. CONFIGURATION DE LA PAGE & DESIGN UI/UX (CSS PERSONNALISÉ)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Terminal Pro | Institutionnel",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection CSS (Dark Mode Institutionnel Haut de Gamme)
st.markdown("""
<style>
    /* Arrière-plan global */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* Typographie des titres */
    h1, h2, h3 { color: #f0f6fc !important; font-weight: 500 !important; }
    
    /* Cartes de métriques personnalisées */
    .fin-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    .fin-card:hover { transform: translateY(-2px); border-color: #58a6ff; }
    .fin-title { font-size: 0.80rem; color: #8b949e; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; letter-spacing: 0.5px; }
    .fin-val { font-size: 1.5rem; color: #58a6ff; font-weight: 700; }
    .fin-na { color: #f85149; font-size: 1.2rem; font-weight: 500; }
    .fin-cash { color: #3fb950; font-size: 1.2rem; font-weight: 600; }
    
    /* Conteneur du Score Fondamental */
    .score-container { text-align: center; padding: 25px; background-color: #161b22; border-radius: 8px; border: 1px solid #30363d; }
    .score-title { font-size: 1rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .score-val { font-size: 3.5rem; font-weight: 800; color: #58a6ff; line-height: 1; }
    
    /* Tabulations Streamlit */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px 6px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #21262d; border-bottom-color: transparent; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 1. ARCHITECTURE TECHNIQUE : PARSING DÉFENSIF & DEVISES
# ==============================================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    """Conversion robuste vers l'Euro avec fallbacks locaux."""
    if not currency_code or not isinstance(currency_code, str):
        return 1.0
    
    curr = currency_code.upper().strip()
    is_pence = False
    
    # Traitement spécial pour la bourse de Londres (Pence vs Pound)
    if curr in ["GBP", "GBX", "GBP=X", "GBp"]:
        is_pence = (curr in ["GBX", "GBp"])
        curr = "GBP"
        
    if curr == "EUR":
        return 0.01 if is_pence else 1.0

    # Fallbacks institutionnels (Valeurs de secours si l'API Yahoo crash)
    fallbacks = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "CAD": 0.68, "JPY": 0.006, "AUD": 0.60, "CNY": 0.13}
    
    try:
        ticker = f"{curr}EUR=X"
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            rate = float(data['Close'].iloc[-1])
            return (rate * 0.01) if is_pence else rate
    except Exception:
        pass # Silencieux, on passe au fallback
    
    rate = fallbacks.get(curr, 1.0)
    return (rate * 0.01) if is_pence else rate

def safe_float(val, multiplier=1.0, precision=2):
    """Parseur défensif pour éviter les crashs sur des champs manquants."""
    if val is None or pd.isna(val) or val == "":
        return None
    try:
        return round(float(val) * multiplier, precision)
    except (ValueError, TypeError):
        return None

def format_metric(val, suffix="", is_currency=False):
    """Formateur d'affichage élégant."""
    if val is None:
        return "<span class='fin-na'>N/A</span>"
    if isinstance(val, str) and val.lower() == "cash positif":
        return "<span class='fin-cash'>Cash Positif</span>"
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"{formatted} {suffix}".strip()

def render_metric_card(title, html_value):
    """Génère la carte HTML/CSS pour une métrique."""
    st.markdown(f"""
        <div class="fin-card">
            <div class="fin-title">{title}</div>
            <div class="fin-val">{html_value}</div>
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 2. LOGIQUE MÉTIER & CALCUL DES RATIOS
# ==============================================================================
def calculer_rsi(data, window=14):
    """Calcul du Relative Strength Index (Analyse Technique)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=1800)
def get_news_from_zonebourse_rss():
    """Récupère les actualités Zone Bourse via flux RSS"""
    try:
        rss_url = "https://www.zonebourse.com/rss/news.xml"
        feed = feedparser.parse(rss_url)
        
        news_list = []
        for entry in feed.entries[:15]:  # Récupère jusqu'à 15 articles
            try:
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                published = entry.get('published', 'Date non disponible')
                
                # Parse la date pour un format plus lisible
                if published and published != 'Date non disponible':
                    try:
                        dt_obj = datetime.strptime(published[:19], '%Y-%m-%dT%H:%M:%S')
                        published = dt_obj.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                
                if title and link:
                    news_list.append({
                        'title': title,
                        'link': link,
                        'published': published,
                        'publisher': 'Zone Bourse'
                    })
            except:
                continue
        
        return news_list if news_list else None
    except Exception as e:
        print(f"Erreur RSS Zone Bourse: {e}")
        return None

def get_zonebourse_direct_link(ticker):
    """Retourne un lien direct vers Zone Bourse pour un titre"""
    ticker_clean = ticker.replace('.PA', '').replace('.AS', '').upper()
    return f"https://www.zonebourse.com/recherche/?q={ticker_clean}"

def extract_stock_data(info, fx_rate):
    """Extraction et calcul des 21 ratios pour les actions."""
    d = {}
    
    # A. Valorisation & Prix
    d['Prix'] = safe_float(info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose'), fx_rate)
    d['PER_Actuel'] = safe_float(info.get('trailingPE'))
    d['PER_Futur'] = safe_float(info.get('forwardPE'))
    d['PS'] = safe_float(info.get('priceToSalesTrailing12Months'))
    d['PB'] = safe_float(info.get('priceToBook'))
    d['EV_EBITDA'] = safe_float(info.get('enterpriseToEbitda'))
    d['BPA'] = safe_float(info.get('trailingEps'), fx_rate)
    d['BVPS'] = safe_float(info.get('bookValue'), fx_rate)
    
    # Prix de Graham (√22.5 * BPA * BVPS)
    if d['BPA'] and d['BVPS'] and (d['BPA'] * d['BVPS']) > 0:
        d['Graham'] = round(math.sqrt(22.5 * d['BPA'] * d['BVPS']), 2)
    else:
        d['Graham'] = None

    # B. Rentabilité
    d['Marge_Brute'] = safe_float(info.get('grossMargins'), 100)
    d['Marge_Op'] = safe_float(info.get('operatingMargins'), 100)
    d['Marge_Nette'] = safe_float(info.get('profitMargins'), 100)
    d['ROE'] = safe_float(info.get('returnOnEquity'), 100)
    d['ROA'] = safe_float(info.get('returnOnAssets'), 100)

    # C. Santé Financière
    treso = safe_float(info.get('totalCash'), fx_rate / 1_000_000)
    dette_totale = safe_float(info.get('totalDebt'), fx_rate / 1_000_000)
    d['EBITDA'] = safe_float(info.get('ebitda'), fx_rate / 1_000_000)
    
    if treso is not None and dette_totale is not None:
        d['Dette_Nette'] = dette_totale - treso
    else:
        d['Dette_Nette'] = None

    if d['Dette_Nette'] is not None and d['EBITDA'] and d['EBITDA'] > 0:
        d['Levier'] = "Cash Positif" if d['Dette_Nette'] < 0 else round(d['Dette_Nette'] / d['EBITDA'], 2)
    else:
        d['Levier'] = None

    d['Current_Ratio'] = safe_float(info.get('currentRatio'))
    d['Quick_Ratio'] = safe_float(info.get('quickRatio'))
    d['Debt_Equity'] = safe_float(info.get('debtToEquity'))

    # D. Croissance & Dividendes
    d['Rev_Growth'] = safe_float(info.get('revenueGrowth'), 100)
    d['Payout'] = safe_float(info.get('payoutRatio'), 100)
    
    # E. Consensus
    d['Target'] = safe_float(info.get('targetMeanPrice'), fx_rate)
    d['Analystes'] = info.get('numberOfAnalystOpinions', 'N/A')
    reco_raw = info.get('recommendationKey', 'N/A')
    d['Reco'] = reco_raw.replace('_', ' ').title() if isinstance(reco_raw, str) else 'N/A'
    
    # Calcul Score Fondamental (sur 100)
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

    return d

def extract_etf_data(info, ticker_symbol, fx_rate):
    """Extraction spécifique pour les ETF selon les 5 critères clés."""
    d = {}
    d['Prix'] = safe_float(info.get('navPrice') or info.get('previousClose') or info.get('regularMarketPrice'), fx_rate)
    d['TER'] = safe_float(info.get('annualReportExpenseRatio') or info.get('ytdReturn'), 100)
    d['AUM'] = safe_float(info.get('totalAssets'), fx_rate / 1_000_000)
    
    name = str(info.get('longName', '')).upper()
    d['Distribution'] = "Capitalisation (Acc)" if " ACC" in name or "ACCUM" in name else "Distribution (Dist)"
    d['Replication'] = "Synthétique (Swap)" if "SWAP" in name else "Physique (Standard)"
    
    # Éligibilité (Heuristique institutionnelle)
    is_pea_emitter = any(x in name for x in ["AMUNDI", "LYXOR", "BNP"])
    is_paris = ".PA" in ticker_symbol.upper()
    d['PEA'] = "Éligible PEA (Probable)" if (is_pea_emitter and is_paris) else "Compte-Titres Ordinaire (CTO)"
        
    return d


# ==============================================================================
# 3. INTERFACE UTILISATEUR PRINCIPALE
# ==============================================================================
st.sidebar.markdown("## 🏛️ Alpha Terminal Pro")
mode = st.sidebar.radio("Navigation Principale", ["🔍 Analyse Individuelle", "⚖️ Comparateur Multi-Actifs"])
st.sidebar.markdown("---")

if mode == "🔍 Analyse Individuelle":
    ticker_input = st.sidebar.text_input("Saisir un Ticker (ex: AAPL, LVMH.PA, CW8.PA)", "AAPL").upper().strip()
    
    if ticker_input:
        with st.spinner("Extraction et calcul des données quantitatives..."):
            try:
                ticker = yf.Ticker(ticker_input)
                info = ticker.info
                
                if not info or ('symbol' not in info and 'regularMarketPrice' not in info):
                    st.error(f"❌ Impossible de localiser le ticker '{ticker_input}'. Vérifiez la syntaxe (ex: .PA pour Paris).")
                    st.stop()
                    
                nom = info.get('longName') or info.get('shortName', ticker_input)
                devise = info.get('currency', 'USD')
                fx_rate = get_fx_rate(devise)
                is_etf = info.get('quoteType') == 'ETF'
                
                st.title(f"{nom} ({ticker_input})")
                st.caption(f"📍 Devise d'origine : **{devise}** | Taux de conversion appliqué : **1 {devise} = {fx_rate:.4f} €**")
                
                tabs = st.tabs(["📊 Fondamentaux", "📈 Technique (5A)", "⚙️ Simulateur DCA", "📰 Actualités (Live)"])
                
                # ---------------------------------------------------------
                # ONGLET 1 : FONDAMENTAUX (ACTIONS VS ETF)
                # ---------------------------------------------------------
                with tabs[0]:
                    if is_etf:
                        etf_data = extract_etf_data(info, ticker_input, fx_rate)
                        st.subheader("Analyse du Fonds Indiciel (ETF)")
                        
                        if etf_data['AUM'] and etf_data['AUM'] < 100:
                            st.warning("⚠️ **Alerte Liquidité :** L'encours du fonds est inférieur à 100 M€. Risque accru de fermeture ou de spread de spread large.")
                        elif etf_data['AUM']:
                            st.success("✅ **Liquidité saine :** Encours supérieur à 100 M€.")

                        c1, c2, c3, c4 = st.columns(4)
                        with c1: render_metric_card("Prix Actuel", format_metric(etf_data['Prix'], "€"))
                        with c2: render_metric_card("Frais de Gestion (TER)", format_metric(etf_data['TER'], "%"))
                        with c3: render_metric_card("Encours (AUM)", format_metric(etf_data['AUM'], "M€"))
                        with c4: render_metric_card("Enveloppe Fiscale", etf_data['PEA'])
                        
                        c5, c6 = st.columns(2)
                        with c5: render_metric_card("Politique de Dividendes", etf_data['Distribution'])
                        with c6: render_metric_card("Qualité de Réplication", etf_data['Replication'])
                        
                    else:
                        data = extract_stock_data(info, fx_rate)
                        
                        # Section Score & Synthèse
                        c1, c2, c3 = st.columns([1.5, 2, 2])
                        with c1:
                            st.markdown(f"""
                                <div class="score-container">
                                    <div class="score-title">Score Fondamental</div>
                                    <div class="score-val">{data['Score']}<span style="font-size:1.5rem; color:#8b949e;">/100</span></div>
                                </div>
                            """, unsafe_allow_html=True)
                            st.progress(data['Score'] / 100)
                        with c2:
                            render_metric_card("Prix Actuel", format_metric(data['Prix'], "€"))
                            target_disp = format_metric(data['Target'], "€")
                            render_metric_card("Consensus Analystes", f"{target_disp} <span style='font-size:0.8rem; color:#8b949e;'>({data['Reco']})</span>")
                        with c3:
                            render_metric_card("Levier (Dette Nette / EBITDA)", format_metric(data['Levier'], "x"))
                            render_metric_card("Croissance du Chiffre d'Affaires", format_metric(data['Rev_Growth'], "%"))

                        st.markdown("---")
                        
                        # Grille des 21 Ratios (3 Colonnes)
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown("### 💰 Valorisation & Prix")
                            render_metric_card("PER Actuel (Trailing P/E)", format_metric(data['PER_Actuel'], "x"))
                            render_metric_card("PER Futur (Forward P/E)", format_metric(data['PER_Futur'], "x"))
                            render_metric_card("Valeur d'Entreprise / EBITDA", format_metric(data['EV_EBITDA'], "x"))
                            render_metric_card("Prix de Graham (Théorique)", format_metric(data['Graham'], "€"))
                            render_metric_card("Price to Book (P/B)", format_metric(data['PB'], "x"))
                            render_metric_card("Price to Sales (P/S)", format_metric(data['PS'], "x"))

                        with col_b:
                            st.markdown("### 📈 Rentabilité & Performance")
                            render_metric_card("Marge Nette (Profit Margin)", format_metric(data['Marge_Nette'], "%"))
                            render_metric_card("Marge Opérationnelle", format_metric(data['Marge_Op'], "%"))
                            render_metric_card("Marge Brute (Gross Margin)", format_metric(data['Marge_Brute'], "%"))
                            render_metric_card("ROE (Rentabilité Capitaux)", format_metric(data['ROE'], "%"))
                            render_metric_card("ROA (Rentabilité Actifs)", format_metric(data['ROA'], "%"))
                            render_metric_card("Payout Ratio (Distribution)", format_metric(data['Payout'], "%"))

                        with col_c:
                            st.markdown("### 🛡️ Santé Financière & Bilan")
                            render_metric_card("Dette Nette Globale", format_metric(data['Dette_Nette'], "M€"))
                            render_metric_card("EBITDA (Génération de Cash)", format_metric(data['EBITDA'], "M€"))
                            render_metric_card("Liquidité Générale (Current)", format_metric(data['Current_Ratio']))
                            render_metric_card("Liquidité Immédiate (Quick)", format_metric(data['Quick_Ratio']))
                            render_metric_card("Ratio Dette / Fonds Propres", format_metric(data['Debt_Equity'], "%"))
                            render_metric_card("Bénéfice par Action (BPA)", format_metric(data['BPA'], "€"))

                # ---------------------------------------------------------
                # ONGLET 2 : ANALYSE TECHNIQUE (5 Ans)
                # ---------------------------------------------------------
                with tabs[1]:
                    st.subheader("Analyse Graphique (Historique 5 Ans)")
                    hist = ticker.history(period="5y")
                    
                    if len(hist) > 50: # Au moins 50 jours pour la SMA 50
                        hist['Close_EUR'] = hist['Close'] * fx_rate
                        hist['SMA50'] = hist['Close_EUR'].rolling(50).mean()
                        hist['SMA200'] = hist['Close_EUR'].rolling(200).mean()
                        hist['RSI'] = calculer_rsi(hist['Close']) # Le RSI est indépendant de la devise

                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                        
                        # Graphique des Prix (Ligne)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close_EUR'], name="Prix (€)", line=dict(color="#58a6ff", width=2)), row=1, col=1)
                        # Moyennes Mobiles
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color="#f1e05a", width=1.5, dash='dot')), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color="#ff7b72", width=1.5, dash='dot')), row=1, col=1)
                        
                        # Graphique RSI
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI (14)", line=dict(color="#79c0ff", width=1.5)), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="#ff7b72", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", row=2, col=1)

                        fig.update_layout(
                            height=650, 
                            template="plotly_dark", 
                            paper_bgcolor='rgba(0,0,0,0)', 
                            plot_bgcolor='rgba(0,0,0,0)', 
                            margin=dict(l=10, r=10, t=30, b=10), 
                            hovermode="x unified",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Historique insuffisant pour générer une analyse technique sur 5 ans.")

                # ---------------------------------------------------------
                # ONGLET 3 : SIMULATEUR DCA DE HAUTE PRÉCISION
                # ---------------------------------------------------------
                with tabs[2]:
                    st.subheader("Simulateur d'Investissement Programmé (DCA)")
                    st.write("Ce simulateur utilise les prix réels de clôture au premier jour ouvré de chaque mois pour modéliser une stratégie DCA institutionnelle.")
                    
                    dc1, dc2 = st.columns(2)
                    mensualite = dc1.number_input("Montant mensuel investi (€)", min_value=10, max_value=10000, value=150, step=50)
                    duree = dc2.selectbox("Recul historique (Backtest)", ["1 an", "3 ans", "5 ans", "10 ans"], index=2)
                    
                    period_map = {"1 an": "1y", "3 ans": "3y", "5 ans": "5y", "10 ans": "10y"}
                    
                    if st.button("🚀 Lancer la Simulation DCA", type="primary"):
                        dca_hist = ticker.history(period=period_map[duree])
                        if not dca_hist.empty and len(dca_hist) > 20:
                            dca_hist['Close_EUR'] = dca_hist['Close'] * fx_rate
                            # Échantillonnage précis : 'BMS' = Business Month Start (1er jour ouvré)
                            monthly_data = dca_hist['Close_EUR'].resample('BMS').first().dropna()
                            
                            capital_investi = 0
                            actions_cumulees = 0
                            valeurs_pf = []
                            capitaux_investis = []
                            
                            # Boucle de calcul cumulatif
                            for date, price in monthly_data.items():
                                actions_achetees = mensualite / price
                                actions_cumulees += actions_achetees
                                capital_investi += mensualite
                                
                                capitaux_investis.append(capital_investi)
                                valeurs_pf.append(actions_cumulees * price)
                                
                            df_dca = pd.DataFrame({
                                'Date': monthly_data.index,
                                'Capital Investi': capitaux_investis,
                                'Valeur Réelle': valeurs_pf
                            }).set_index('Date')

                            # Bilan Métriques
                            valeur_finale = df_dca['Valeur Réelle'].iloc[-1]
                            capital_final = df_dca['Capital Investi'].iloc[-1]
                            plus_value = valeur_finale - capital_final
                            rendement = (plus_value / capital_final) * 100

                            st.success(f"""
                            **Bilan du backtest sur {duree} :**
                            * 💼 **Capital total investi :** {capital_final:,.2f} €
                            * 📈 **Valeur finale du portefeuille :** {valeur_finale:,.2f} €
                            * 💰 **Plus-value latente :** {plus_value:,.2f} €
                            * 🚀 **Rendement total :** {rendement:,.2f} %
                            """)

                            # Graphique Plotly de la simulation
                            fig_dca = go.Figure()
                            fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Capital Investi'], mode='lines', name="Capital Sorti (€)", line=dict(color="#8b949e", width=2, dash='dash')))
                            fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Valeur Réelle'], mode='lines', fill='tozeroy', name="Valeur du Portefeuille (€)", line=dict(color="#3fb950", width=2)))
                            fig_dca.update_layout(height=450, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
                            st.plotly_chart(fig_dca, use_container_width=True)
                        else:
                            st.error("Données historiques insuffisantes pour effectuer la simulation sur cette période.")

                # ---------------------------------------------------------
                # ONGLET 4 : ACTUALITÉS ZONE BOURSE
                # ---------------------------------------------------------
                with tabs[3]:
                    st.subheader("📰 Actualités Boursières (Zone Bourse)")
                    
                    # Récupère les actualités
                    news_list = get_news_from_zonebourse_rss()
                    
                    if news_list and len(news_list) > 0:
                        st.info("✅ Actualités en direct depuis Zone Bourse (RSS)")
                        
                        for i, news in enumerate(news_list[:10]):  # Affiche max 10
                            st.markdown(f"""
                            <div style="background-color:#161b22; padding:15px; border-radius:6px; margin-bottom:12px; border-left: 4px solid #58a6ff; border-top: 1px solid #30363d; border-right: 1px solid #30363d;">
                                <a href="{news['link']}" target="_blank" style="color:#58a6ff; font-weight:600; text-decoration:none; font-size:1.1rem;">{news['title']}</a><br>
                                <small style="color:#8b949e; margin-top:5px; display:inline-block;">📰 {news['publisher']} &nbsp;|&nbsp; 🕒 {news['published']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Impossible de charger le flux RSS Zone Bourse.")
                        st.info(f"""
                        **📌 Consultation directe :**
                        
                        [🔗 Voir les actualités pour **{ticker_input}** sur Zone Bourse]({get_zonebourse_direct_link(ticker_input)})
                        
                        Zone Bourse propose les actualités les plus récentes et les analyses spécifiques par titre.
                        """)

            except Exception as e:
                st.error(f"Erreur d'exécution isolée lors du traitement de {ticker_input} : {str(e)}")


# ==============================================================================
# MODULE COMPARATEUR MULTI-ACTIFS
# ==============================================================================
elif mode == "⚖️ Comparateur Multi-Actifs":
    st.title("Comparateur Quantitatif (Matrice Multi-Actifs)")
    st.write("Saisissez une liste de tickers (actions ou ETF) séparés par des virgules. Le tableau généré sera trié automatiquement par le Score Fondamental pour faire ressortir les meilleures opportunités.")
    
    tickers_input = st.text_input("Tickers (ex: AAPL, MSFT, LVMH.PA, ASML.AS, CW8.PA)", "AAPL, MSFT, NVDA, LVMH.PA, JNJ")
    
    if st.button("📊 Générer la Matrice Comparative", type="primary"):
        with st.spinner("Analyse quantitative des actifs en cours..."):
            tickers_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            results = []
            
            for t in tickers_list:
                try:
                    tk = yf.Ticker(t)
                    info = tk.info
                    
                    if not info or 'symbol' not in info:
                        continue # Ignore les tickers invalides silencieusement pour ne pas crasher la boucle
                        
                    devise = info.get('currency', 'USD')
                    fx = get_fx_rate(devise)
                    is_etf = info.get('quoteType') == 'ETF'
                    nom_court = info.get('shortName', t)
                    
                    if is_etf:
                        d = extract_etf_data(info, t, fx)
                        results.append({
                            "Ticker": t, "Nom": nom_court, "Type": "ETF", "Score (/100)": 0,
                            "Prix (€)": d['Prix'], "PER (x)": None, "Marge Nette (%)": None, 
                            "Levier (Dette/EBITDA)": None, "Croissance CA (%)": None, "Frais ETF (%)": d['TER']
                        })
                    else:
                        d = extract_stock_data(info, fx)
                        results.append({
                            "Ticker": t, "Nom": nom_court, "Type": "Action", "Score (/100)": d['Score'],
                            "Prix (€)": d['Prix'], "PER (x)": d['PER_Actuel'], "Marge Nette (%)": d['Marge_Nette'], 
                            "Levier (Dette/EBITDA)": d['Levier'], "Croissance CA (%)": d['Rev_Growth'], "Frais ETF (%)": None
                        })
                except Exception:
                    continue # Bypass défensif sur erreur API isolée
            
            if results:
                df = pd.DataFrame(results)
                
                # Tri décroissant par Score Fondamental
                df = df.sort_values(by="Score (/100)", ascending=False).reset_index(drop=True)
                
                # Affichage formaté (DataFrame Streamlit)
                st.dataframe(df.style.format({
                    "Score (/100)": "{:.0f}", 
                    "Prix (€)": "{:.2f} €", 
                    "PER (x)": "{:.2f}", 
                    "Marge Nette (%)": "{:.2f} %", 
                    "Croissance CA (%)": "{:.2f} %", 
                    "Frais ETF (%)": "{:.2f} %"
                }, na_rep="N/A"), use_container_width=True, height=400)
                
                # Exportation CSV robuste
                csv = df.to_csv(index=False, sep=";").encode('utf-8')
                st.download_button(
                    label="📥 Télécharger la Matrice (CSV)",
                    data=csv,
                    file_name=f"matrice_alpha_pro_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.error("Impossible de récupérer les données. Vérifiez la syntaxe des tickers.")
