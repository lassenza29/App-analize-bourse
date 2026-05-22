import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import feedparser
import urllib.parse
import time
import json

# ==============================================================================
# CONFIGURATION DE LA PAGE & DESIGN CLAIR (UI MODERNE ET STANDARD)
# ==============================================================================
st.set_page_config(
    page_title="Terminal d'Analyse Financière",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Un peu de CSS léger pour espacer proprement les métriques sans en faire trop
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #1f77b4; font-weight: 600; }
    hr { margin: 20px 0; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# MOTEUR DE TRAITEMENT ET CONVERSION (CORRECTION DU CACHE STREAMLIT)
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

def format_metric(val, suffix="", default="N/A"):
    if val is None: return default
    if isinstance(val, str): return val
    formatted = f"{val:,.2f}".replace(",", " ")
    return f"{formatted} {suffix}".strip()

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
    """
    CORRECTION DU BUG DE CACHE : 
    On convertit le dictionnaire de yfinance en texte JSON puis on le recharge.
    Cela détruit tous les objets complexes non-sérialisables qui font planter Streamlit.
    """
    for attempt in range(retries):
        try:
            tk = yf.Ticker(ticker_symbol)
            info = tk.info
            if info and ('symbol' in info or 'regularMarketPrice' in info or 'currentPrice' in info):
                # Nettoyage strict pour le cache de Streamlit
                clean_info = json.loads(json.dumps(info, default=str))
                return clean_info
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
    d['Score'] = score

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
    d['PEA'] = "Éligible PEA" if is_pea else "Compte-Titres (CTO)"
    return d

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
    except Exception: pass
    return news

# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================
st.title("Terminal d'Analyse Financière")

mode = st.radio("Sélectionnez un module :", ["Analyse Individuelle", "Comparateur d'Actifs"], horizontal=True)
st.markdown("<hr>", unsafe_allow_html=True)

if mode == "Analyse Individuelle":
    ticker_input = st.text_input("Saisissez un Ticker (ex: AAPL, LVMH.PA, MSFT) :").upper().strip()
    
    if ticker_input:
        with st.spinner("Récupération des données en cours..."):
            info = fetch_info_with_retry(ticker_input)
            
            if not info:
                st.error("Impossible de récupérer les données. Vérifiez le symbole ou réessayez plus tard.")
                st.stop()
                
            nom = info.get('longName', info.get('shortName', ticker_input))
            devise = info.get('currency', 'USD').upper()
            fx_rate = get_fx_rate(devise)
            is_etf = info.get('quoteType') == 'ETF' or 'totalAssets' in info
            
            st.header(f"{nom} ({ticker_input})")
            
            tabs = st.tabs(["📊 Fondamentaux", "📈 Analyse Technique", "📅 Simulation DCA", "📰 Actualités"])
            
            with tabs[0]:
                if is_etf:
                    data = extract_etf_data(info, ticker_input, fx_rate)
                    st.subheader("Informations de l'ETF")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Prix Actuel", format_metric(data['Prix'], "€"))
                    c2.metric("Frais (TER)", format_metric(data['TER'], "%"))
                    c3.metric("Actifs gérés (AUM)", format_metric(data['AUM'], "M€"))
                    c4.metric("Régime Fiscal", data['PEA'])
                    
                    c5, c6 = st.columns(2)
                    c5.metric("Politique de Dividende", data['Distribution'])
                    c6.metric("Méthode de Réplication", data['Replication'])
                else:
                    data = extract_stock_data(info, fx_rate)
                    
                    # Section Haute - Métriques Clés
                    st.subheader("Indicateurs Principaux")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Prix Actuel", format_metric(data['Prix'], "€"))
                    c2.metric("Score d'Investissement", f"{data['Score']}/100")
                    c3.metric("Croissance CA", format_metric(data['Rev_Growth'], "%"))
                    c4.metric("Objectif Analystes", format_metric(data['Target'], "€"))

                    st.markdown("<hr>", unsafe_allow_html=True)
                    
                    # Section Détaillée
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.markdown("#### Valorisation")
                        st.metric("PER (Actuel)", format_metric(data['PER_Actuel'], "x"))
                        st.metric("Price / Sales", format_metric(data['PS'], "x"))
                        st.metric("Price / Book", format_metric(data['PB'], "x"))
                        st.metric("Valeur de Graham", format_metric(data['Graham'], "€"))
                    with col_b:
                        st.markdown("#### Rentabilité")
                        st.metric("Marge Nette", format_metric(data['Marge_Nette'], "%"))
                        st.metric("Marge Opérationnelle", format_metric(data['Marge_Op'], "%"))
                        st.metric("ROE (Capitaux Propres)", format_metric(data['ROE'], "%"))
                        st.metric("Payout Ratio", format_metric(data['Payout'], "%"))
                    with col_c:
                        st.markdown("#### Santé Financière")
                        st.metric("Dette / EBITDA", format_metric(data['Levier'], "x"))
                        st.metric("Dette Nette", format_metric(data['Dette_Nette'], "M€"))
                        st.metric("Current Ratio", format_metric(data['Current_Ratio']))
                        st.metric("BPA (EPS)", format_metric(data['BPA'], "€"))

            with tabs[1]:
                tk_obj = yf.Ticker(ticker_input)
                hist = tk_obj.history(period="5y")
                if len(hist) > 200:
                    hist['Close_EUR'] = hist['Close'] * fx_rate
                    hist['SMA50'] = hist['Close_EUR'].rolling(50).mean()
                    hist['SMA200'] = hist['Close_EUR'].rolling(200).mean()
                    hist['RSI'] = calculer_rsi(hist['Close'])

                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close_EUR'], name="Prix", line=dict(color="#1f77b4")), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="Moy. 50 jours", line=dict(color="#ff7f0e")), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="Moy. 200 jours", line=dict(color="#2ca02c")), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color="#7f7f7f")), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

                    fig.update_layout(height=600, margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                else: st.warning("Historique insuffisant pour afficher les graphiques.")

            with tabs[2]:
                st.markdown("#### Simuler un investissement périodique (DCA)")
                dc1, dc2 = st.columns(2)
                mensualite = dc1.number_input("Investissement mensuel (€)", min_value=10, value=500, step=50)
                duree = dc2.selectbox("Horizon d'investissement", ["1y", "3y", "5y", "10y"], index=2)
                
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
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Capital Total Investi", f"{cap_investi:,.0f} €".replace(',', ' '))
                    c2.metric("Valeur du Portefeuille", f"{val_finale:,.0f} €".replace(',', ' '))
                    c3.metric("Plus-Value Nette", f"{pv:,.0f} €".replace(',', ' '), delta=f"{(pv/cap_investi)*100:.2f}%")
                    
                    fig_dca = go.Figure()
                    fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Investi'], name="Capital Investi", line=dict(dash='dash', color='gray')))
                    fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Valeur'], name="Valeur Réelle", fill='tozeroy', line=dict(color='#1f77b4')))
                    fig_dca.update_layout(height=400, hovermode="x unified")
                    st.plotly_chart(fig_dca, use_container_width=True)
                else: st.warning("Données historiques insuffisantes pour la modélisation DCA.")

            with tabs[3]:
                news = get_morningstar_news(ticker_input, nom)
                if news:
                    for n in news:
                        st.markdown(f"**[{n['title']}]({n['link']})**")
                        st.caption(f"Source : {n['publisher']} | Date : {n['published']}")
                        st.markdown("---")
                else:
                    st.info("Aucune actualité récente trouvée.")

elif mode == "Comparateur d'Actifs":
    st.markdown("#### Entrez plusieurs tickers pour les comparer")
    tickers_input = st.text_input("Exemples : AAPL, MSFT, LVMH.PA, TTE.PA").upper()
    
    if tickers_input:
        if st.button("Comparer"):
            with st.spinner("Analyse des actifs en cours..."):
                t_list = [t.strip() for t in tickers_input.split(",") if t.strip()]
                res = []
                
                progress_bar = st.progress(0)
                
                for i, t in enumerate(t_list):
                    info = fetch_info_with_retry(t)
                    if info:
                        fx = get_fx_rate(info.get('currency', 'USD'))
                        if info.get('quoteType') == 'ETF':
                            d = extract_etf_data(info, t, fx)
                            res.append({'Ticker': t, 'Type': 'ETF', 'Prix (€)': d['Prix'], 'Score': None, 'Dette/EBITDA': None, 'PER': None, 'Marge Nette': None})
                        else:
                            d = extract_stock_data(info, fx)
                            res.append({'Ticker': t, 'Type': 'Action', 'Prix (€)': d['Prix'], 'Score': d['Score'], 'Dette/EBITDA': d['Levier'] if isinstance(d['Levier'], (int, float)) else None, 'PER': d['PER_Actuel'], 'Marge Nette': d['Marge_Nette']})
                    progress_bar.progress((i + 1) / len(t_list))
                
                progress_bar.empty()
                
                if res:
                    df = pd.DataFrame(res).sort_values(by="Score", ascending=False)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else: 
                    st.error("Aucune donnée n'a pu être récupérée pour ces tickers.")
