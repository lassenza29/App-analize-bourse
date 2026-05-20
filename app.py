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
# CONFIGURATION DE LA PAGE & DESIGN UI/UX INSTITUTIONNEL
# ==============================================================================
st.set_page_config(
    page_title="Alpha Terminal Pro | Institutionnel",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3 { color: #f0f6fc !important; font-weight: 500 !important; }
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
    .fin-title { font-size: 0.80rem; color: #8b949e; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
    .fin-val { font-size: 1.5rem; color: #58a6ff; font-weight: 700; }
    .fin-na { color: #f85149; font-size: 1.2rem; font-weight: 500; }
    .fin-cash { color: #3fb950; font-size: 1.2rem; font-weight: 600; }
    .score-container { text-align: center; padding: 25px; background-color: #161b22; border-radius: 8px; border: 1px solid #30363d; }
    .score-title { font-size: 1rem; color: #8b949e; text-transform: uppercase; margin-bottom: 10px; }
    .score-val { font-size: 3.5rem; font-weight: 800; color: #58a6ff; line-height: 1; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px 6px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #21262d; border-bottom-color: transparent; }
    .expert-verdict { border-left: 4px solid #58a6ff; padding-left: 15px; background-color: #161b22; padding: 15px; border-radius: 0 8px 8px 0; }
    .buy-verdict { border-left-color: #3fb950; }
    .hold-verdict { border-left-color: #d29922; }
    .sell-verdict { border-left-color: #f85149; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# MOTEUR DE TRAITEMENT ET CONVERSION
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
    except:
        pass
    rate = fallbacks.get(curr, 1.0)
    return (rate * 0.01) if is_pence else rate

def safe_float(val, multiplier=1.0, precision=2):
    if val is None or pd.isna(val) or val == "": return None
    try: return round(float(val) * multiplier, precision)
    except: return None

def safe_str(val):
    if val is None or pd.isna(val) or val == "": return "N/A"
    return str(val)

def format_metric(val, suffix="", is_currency=False):
    if val is None: return "<span class='fin-na'>N/A</span>"
    if isinstance(val, str) and val.lower() == "cash positif": return "<span class='fin-cash'>Cash Positif</span>"
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
    d['Industry'] = safe_str(info.get('industry'))

    return d

def extract_etf_data(info, ticker_symbol, fx_rate):
    d = {}
    d['Prix'] = safe_float(info.get('navPrice') or info.get('previousClose') or info.get('regularMarketPrice'), fx_rate)
    d['TER'] = safe_float(info.get('annualReportExpenseRatio') or info.get('ytdReturn'), 100)
    d['AUM'] = safe_float(info.get('totalAssets'), fx_rate / 1_000_000)
    name = str(info.get('longName', '')).upper()
    d['Distribution'] = "Capitalisation (Acc)" if " ACC" in name or "ACCUM" in name else "Distribution (Dist)"
    d['Replication'] = "Synthétique (Swap)" if "SWAP" in name else "Physique (Standard)"
    is_pea = any(x in name for x in ["AMUNDI", "LYXOR", "BNP"]) and ".PA" in ticker_symbol.upper()
    d['PEA'] = "Éligible PEA (Probable)" if is_pea else "Compte-Titres Ordinaire (CTO)"
    return d


# ==============================================================================
# MOTEUR D'ACTUALITÉS (MORNINGSTAR EXCLUSIF)
# ==============================================================================
@st.cache_data(ttl=1800)
def get_morningstar_news(ticker_symbol, company_name):
    try:
        url = f"https://www.morningstar.fr/fr/news/search.aspx?q={ticker_symbol.split('.')[0]}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=lambda x: x and '/news/' in x.lower())
        news = []
        for l in links[:6]:
            title = l.get_text(strip=True)
            if len(title) > 15:
                href = l.get('href')
                if not href.startswith('http'): href = f"https://www.morningstar.fr{href}"
                news.append({'title': title, 'link': href, 'publisher': 'Morningstar', 'published': 'Date récente'})
        return news
    except:
        return []

def generate_consensus_and_verdict(data, is_etf, nom):
    if is_etf:
        verdict = "Achat" if (data['AUM'] and data['AUM'] > 100) and (data['TER'] and data['TER'] < 0.3) else "Conservation"
        color = "buy-verdict" if verdict == "Achat" else "hold-verdict"
        return f"""
        <div class="expert-verdict {color}">
            <h4 style="margin-top:0;">Verdict de l'Expert : {verdict}</h4>
            <p><strong>Validation des critères :</strong> Fonds indiciel {data.get('Replication', '')}. Liquidité {'optimale' if (data['AUM'] or 0) > 100 else 'à surveiller'} ({format_metric(data['AUM'], 'M€')}). Frais de gestion à {format_metric(data['TER'], '%')}. Structuration adaptée pour une exposition macro-économique diversifiée.</p>
        </div>
        """
    else:
        score = data.get('Score', 0)
        reco = data.get('Reco', 'N/A').lower()
        if score >= 65 and 'buy' in reco: verdict, color = "Achat Fort", "buy-verdict"
        elif score >= 50: verdict, color = "Achat / Accumulation", "buy-verdict"
        elif score >= 35: verdict, color = "Conservation (Hold)", "hold-verdict"
        else: verdict, color = "Vente / Allègement", "sell-verdict"
        
        return f"""
        <div class="expert-verdict {color}">
            <h4 style="margin-top:0;">Verdict de l'Expert : {verdict}</h4>
            <p><strong>Synthèse Fondamentale :</strong> Avec un score de {score}/100, la valorisation est {'attractive' if data['Graham'] and data['Prix'] and data['Graham'] > data['Prix'] else 'exigeante'}. La rentabilité (ROE: {format_metric(data['ROE'], '%')}) et le profil d'endettement ({format_metric(data['Levier'], 'x')}) justifient cette pondération. L'environnement micro-économique du secteur {data.get('Sector', 'N/A')} impose un positionnement stratégique aligné sur la politique de distribution ({format_metric(data['Payout'], '%')}).</p>
        </div>
        """


# ==============================================================================
# INTERFACE PRINCIPALE
# ==============================================================================
mode = st.sidebar.radio("Navigation", ["🔍 Terminal Quantitatif", "⚖️ Comparateur Matrice"], label_visibility="collapsed")

if mode == "🔍 Terminal Quantitatif":
    ticker_input = st.text_input("Recherche", placeholder="Saisir un Ticker (ex: AAPL, LVMH.PA, CW8.PA)", label_visibility="collapsed").upper().strip()
    
    if ticker_input:
        with st.spinner("Acquisition et validation des données (Yahoo / Morningstar / Zonebourse)..."):
            try:
                tk = yf.Ticker(ticker_input)
                info = tk.info
                if not info or ('symbol' not in info and 'regularMarketPrice' not in info):
                    st.error("Donnée non validée. Ticker introuvable.")
                    st.stop()
                    
                nom = info.get('longName', info.get('shortName', ticker_input))
                devise = info.get('currency', 'USD')
                fx_rate = get_fx_rate(devise)
                is_etf = info.get('quoteType') == 'ETF'
                
                st.markdown(f"## {nom} <span style='color:#8b949e; font-size:1.2rem;'>({ticker_input})</span>", unsafe_allow_html=True)
                
                tabs = st.tabs(["📊 Données Fondamentales", "📈 Technique & Graphiques", "⚙️ Modélisation DCA", "📰 Consensus & Presse (Morningstar)"])
                
                with tabs[0]:
                    if is_etf:
                        data = extract_etf_data(info, ticker_input, fx_rate)
                        if data['AUM'] and data['AUM'] < 100: st.error("Alerte Liquidité : Encours < 100M€.")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1: render_metric_card("NAV Actuelle", format_metric(data['Prix'], "€"))
                        with c2: render_metric_card("TER", format_metric(data['TER'], "%"))
                        with c3: render_metric_card("AUM", format_metric(data['AUM'], "M€"))
                        with c4: render_metric_card("Fiscalité", data['PEA'])
                        c5, c6 = st.columns(2)
                        with c5: render_metric_card("Distribution", data['Distribution'])
                        with c6: render_metric_card("Réplication", data['Replication'])
                    else:
                        data = extract_stock_data(info, fx_rate)
                        c1, c2, c3 = st.columns([1.5, 2, 2])
                        with c1:
                            st.markdown(f'<div class="score-container"><div class="score-title">Score Fondamental</div><div class="score-val">{data["Score"]}</div></div>', unsafe_allow_html=True)
                        with c2:
                            render_metric_card("Prix", format_metric(data['Prix'], "€"))
                            render_metric_card("Objectif Consensus", f"{format_metric(data['Target'], '€')} ({data['Reco']})")
                        with c3:
                            render_metric_card("Levier Financier", format_metric(data['Levier'], "x"))
                            render_metric_card("Croissance CA", format_metric(data['Rev_Growth'], "%"))

                        st.markdown("<br>", unsafe_allow_html=True)
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown("### Valorisation")
                            render_metric_card("PER Actuel", format_metric(data['PER_Actuel'], "x"))
                            render_metric_card("PER Futur", format_metric(data['PER_Futur'], "x"))
                            render_metric_card("P/S Ratio", format_metric(data['PS'], "x"))
                            render_metric_card("P/B Ratio", format_metric(data['PB'], "x"))
                            render_metric_card("EV / EBITDA", format_metric(data['EV_EBITDA'], "x"))
                            render_metric_card("BPA", format_metric(data['BPA'], "€"))
                            render_metric_card("Valeur Comptable", format_metric(data['BVPS'], "€"))
                            render_metric_card("Prix de Graham", format_metric(data['Graham'], "€"))
                        with col_b:
                            st.markdown("### Rentabilité")
                            render_metric_card("Marge Brute", format_metric(data['Marge_Brute'], "%"))
                            render_metric_card("Marge Opérationnelle", format_metric(data['Marge_Op'], "%"))
                            render_metric_card("Marge Nette", format_metric(data['Marge_Nette'], "%"))
                            render_metric_card("ROE", format_metric(data['ROE'], "%"))
                            render_metric_card("ROA", format_metric(data['ROA'], "%"))
                        with col_c:
                            st.markdown("### Santé & Dividendes")
                            render_metric_card("Dette Nette", format_metric(data['Dette_Nette'], "M€"))
                            render_metric_card("EBITDA", format_metric(data['EBITDA'], "M€"))
                            render_metric_card("Current Ratio", format_metric(data['Current_Ratio']))
                            render_metric_card("Quick Ratio", format_metric(data['Quick_Ratio']))
                            render_metric_card("Debt / Equity", format_metric(data['Debt_Equity'], "%"))
                            render_metric_card("Payout Ratio", format_metric(data['Payout'], "%"))

                with tabs[1]:
                    hist = tk.history(period="5y")
                    if len(hist) > 200:
                        hist['Close_EUR'] = hist['Close'] * fx_rate
                        hist['SMA50'] = hist['Close_EUR'].rolling(50).mean()
                        hist['SMA200'] = hist['Close_EUR'].rolling(200).mean()
                        hist['RSI'] = calculer_rsi(hist['Close'])

                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close_EUR'], name="Prix", line=dict(color="#58a6ff")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], name="SMA 50", line=dict(color="#f1e05a", dash='dot')), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name="SMA 200", line=dict(color="#ff7b72", dash='dot')), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name="RSI", line=dict(color="#79c0ff")), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="#ff7b72", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#3fb950", row=2, col=1)

                        fig.update_layout(height=600, template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.warning("Historique insuffisant.")

                with tabs[2]:
                    dc1, dc2 = st.columns(2)
                    mensualite = dc1.number_input("Montant mensuel (€)", min_value=10, value=150, label_visibility="collapsed")
                    duree = dc2.selectbox("Période", ["1y", "3y", "5y", "10y"], index=2, label_visibility="collapsed")
                    
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
                            
                        df_dca = pd.DataFrame({'Date': monthly.index, 'Investi': cap_list, 'Valeur': val_list}).set_index('Date')
                        val_finale = df_dca['Valeur'].iloc[-1]
                        pv = val_finale - cap_investi
                        
                        st.success(f"Capital Investi: {cap_investi:,.2f} € | Valeur Finale: {val_finale:,.2f} € | Plus-value: {pv:,.2f} € ({(pv/cap_investi)*100:.2f}%)")
                        
                        fig_dca = go.Figure()
                        fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Investi'], name="Capital", line=dict(color="#8b949e", dash='dash')))
                        fig_dca.add_trace(go.Scatter(x=df_dca.index, y=df_dca['Valeur'], name="Portefeuille", fill='tozeroy', line=dict(color="#3fb950")))
                        fig_dca.update_layout(height=400, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig_dca, use_container_width=True)

                with tabs[3]:
                    st.markdown("### Résumé Exécutif du Consensus")
                    st.markdown(generate_consensus_and_verdict(data, is_etf, nom), unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("### Revue de Presse Macro/Micro")
                    
                    news = get_morningstar_news(ticker_input, nom)
                    if news:
                        for n in news:
                            st.markdown(f"""
                            <div style="background:#161b22; padding:10px; border-left:3px solid #d29922; margin-bottom:10px;">
                                <a href="{n['link']}" target="_blank" style="color:#58a6ff; font-weight:bold; text-decoration:none;">{n['title']}</a><br>
                                <span style="color:#8b949e; font-size:0.8rem;">{n['publisher']} | {n['published']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Donnée non validée ou flux Morningstar temporairement indisponible.")

            except Exception as e:
                st.error("Donnée non validée. Erreur d'exécution du flux de données.")

elif mode == "⚖️ Comparateur Matrice":
    tickers_input = st.text_input("Matrice", placeholder="Ex: AAPL, MSFT, LVMH.PA, CW8.PA", label_visibility="collapsed")
    
    if tickers_input:
        with st.spinner("Analyse quantitative multi-actifs en cours..."):
            t_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            res = []
            
            for t in t_list:
                try:
                    info = yf.Ticker(t).info
                    if not info or 'symbol' not in info: continue
                    fx = get_fx_rate(info.get('currency', 'USD'))
                    
                    if info.get('quoteType') == 'ETF':
                        d = extract_etf_data(info, t, fx)
                        res.append({'Ticker': t, 'Type': 'ETF', 'Prix (€)': d['Prix'], 'Score': 0, 'Dette/EBITDA': 'N/A', 'PER': 'N/A', 'Marge Nette': 'N/A'})
                    else:
                        d = extract_stock_data(info, fx)
                        res.append({'Ticker': t, 'Type': 'Action', 'Prix (€)': d['Prix'], 'Score': d['Score'], 'Dette/EBITDA': d['Levier'], 'PER': d['PER_Actuel'], 'Marge Nette': d['Marge_Nette']})
                except: pass
            
            if res:
                df = pd.DataFrame(res).sort_values(by="Score", ascending=False)
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Télécharger CSV", data=csv, file_name="matrice_alpha_pro.csv", mime="text/csv")
            else: st.error("Aucune donnée n'a pu être extraite.")
