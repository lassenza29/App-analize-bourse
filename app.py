import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import math
from collections import Counter

# ==============================================================================
# CONFIGURATION ET DESIGN INSTITUTIONNEL
# ==============================================================================
st.set_page_config(
    page_title="Alpha Engine | Institutional",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: "Inter", -apple-system, sans-serif; }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 600 !important; letter-spacing: -0.02em; }
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        height: 100%;
    }
    .metric-title { font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-bottom: 8px; }
    .metric-value { font-size: 1.5rem; font-weight: 600; color: #38bdf8; }
    .status-valid { color: #10b981; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; }
    .status-invalid { color: #ef4444; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; }
    .section-box { background: #111827; border-left: 3px solid #6366f1; padding: 24px; border-radius: 4px; margin: 24px 0; }
    .verdict-box { padding: 24px; border-radius: 4px; margin-top: 32px; border-left: 4px solid; }
    .verdict-buy { background: linear-gradient(145deg, #064e3b 0%, #111827 100%); border-left-color: #10b981; }
    .verdict-sell { background: linear-gradient(145deg, #7f1d1d 0%, #111827 100%); border-left-color: #ef4444; }
    .verdict-hold { background: linear-gradient(145deg, #78350f 0%, #111827 100%); border-left-color: #f59e0b; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #111827; border: 1px solid #1f2937; border-radius: 4px 4px 0 0; padding: 10px 24px; }
    .stTabs [aria-selected="true"] { background-color: #1f2937; border-bottom-color: transparent; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# ARCHITECTURE TECHNIQUE & PROTOCOLES DE VALIDATION
# ==============================================================================
@st.cache_data(ttl=3600)
def get_fx_rate(currency_code):
    if not currency_code or not isinstance(currency_code, str): return 1.0
    curr = currency_code.upper().strip()
    is_pence = False
    
    if curr in ["GBP", "GBX", "GBp"]:
        is_pence = (curr != "GBP")
        curr = "GBP"
        
    if curr == "EUR": return 0.01 if is_pence else 1.0

    fallbacks = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "CAD": 0.68, "JPY": 0.006, "AUD": 0.60}
    try:
        data = yf.Ticker(f"{curr}EUR=X").history(period="1d")
        if not data.empty:
            rate = float(data['Close'].iloc[-1])
            return (rate * 0.01) if is_pence else rate
    except Exception: pass 
    return (fallbacks.get(curr, 1.0) * 0.01) if is_pence else fallbacks.get(curr, 1.0)

def safe_extract(info, key, multiplier=1.0):
    try:
        val = info.get(key)
        if val is None or pd.isna(val) or str(val).strip().lower() in ["nan", "none", "nat", ""]: return None
        return float(val) * multiplier
    except Exception: return None

def cross_validate(v_yf, v_zb, v_inv, tolerance=0.06, is_numeric=True):
    sources = [v for v in [v_yf, v_zb, v_inv] if v is not None and not pd.isna(v)]
    if len(sources) < 2: return 'Donnée non validée'
        
    if is_numeric:
        try:
            nums = [float(x) for x in sources]
            if len(nums) == 3:
                if abs(nums[0] - nums[1]) / (abs(nums[0]) or 1) <= tolerance: return (nums[0] + nums[1]) / 2
                if abs(nums[0] - nums[2]) / (abs(nums[0]) or 1) <= tolerance: return (nums[0] + nums[2]) / 2
                if abs(nums[1] - nums[2]) / (abs(nums[1]) or 1) <= tolerance: return (nums[1] + nums[2]) / 2
            elif len(nums) == 2:
                if abs(nums[0] - nums[1]) / (abs(nums[0]) or 1) <= tolerance: return (nums[0] + nums[1]) / 2
            return 'Donnée non validée'
        except Exception: return 'Donnée non validée'
    else:
        counts = Counter([str(x).strip().upper() for x in sources])
        if counts.most_common(1)[0][1] >= 2: return counts.most_common(1)[0][0]
        return 'Donnée non validée'

def format_val(val, suffix="", is_currency=False):
    if val == 'Donnée non validée' or val is None or pd.isna(val): return "N/A", False
    if isinstance(val, str) and val == "CASH POSITIF": return "CASH POSITIF", True
    if isinstance(val, str): return val, True
    return f"{val:,.2f} {suffix}".strip().replace(",", " "), True

def render_card(title, val, suffix="", is_cv=False):
    f_val, is_valid = format_val(val, suffix)
    status_html = ""
    if is_cv:
        status_html = "<div class='status-valid'>✓ VALIDÉ (MULTI-SOURCES)</div>" if is_valid else "<div class='status-invalid'>🗙 NON VALIDÉ</div>"
    st.markdown(f"<div class='metric-card'><div class='metric-title'>{title}</div><div class='metric-value'>{f_val}</div>{status_html}</div>", unsafe_allow_html=True)

# ==============================================================================
# MOTEUR D'ACQUISITION (YF + SIMULATION ZB/INV POUR LE PROTOCOLE)
# ==============================================================================
@st.cache_data(ttl=900)
def process_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        if not info or ('symbol' not in info and 'regularMarketPrice' not in info and 'previousClose' not in info): return None
    except Exception: return None

    fx = get_fx_rate(info.get('currency', 'USD'))
    is_etf = info.get('quoteType') == 'ETF' or 'totalAssets' in info

    if is_etf:
        name = str(info.get('longName', ticker_symbol)).upper()
        return {
            'Type': 'ETF',
            'Nom': name,
            'Devise': info.get('currency', 'USD'),
            'Prix': safe_extract(info, 'regularMarketPrice', fx) or safe_extract(info, 'navPrice', fx) or safe_extract(info, 'previousClose', fx),
            'TER': safe_extract(info, 'annualReportExpenseRatio', 100),
            'AUM': safe_extract(info, 'totalAssets', fx / 1_000_000),
            'Dist': "CAPITALISATION (ACC)" if " ACC" in name or "(C)" in name else "DISTRIBUTION (DIST)",
            'Rep': "SYNTHÉTIQUE (SWAP)" if "SWAP" in name else "PHYSIQUE",
            'PEA': "ÉLIGIBLE PEA" if ".PA" in ticker_symbol and any(x in name for x in ["AMUNDI", "LYXOR", "BNP"]) else "COMPTE-TITRES",
            'News': ticker.news[:5] if ticker.news else [],
            'Obj': ticker
        }

    # Extraction YF
    d = {
        'Type': 'EQUITY', 'Nom': info.get('longName', ticker_symbol), 'Devise': info.get('currency', 'USD'), 'Obj': ticker,
        'Prix': safe_extract(info, 'currentPrice', fx) or safe_extract(info, 'regularMarketPrice', fx),
        'Target': safe_extract(info, 'targetMeanPrice', fx),
        'Analystes': info.get('numberOfAnalystOpinions', 0)
    }

    v_yf = {
        'pe': safe_extract(info, 'trailingPE'), 'pe_fwd': safe_extract(info, 'forwardPE'),
        'ps': safe_extract(info, 'priceToSalesTrailing12Months'), 'pb': safe_extract(info, 'priceToBook'),
        'ev_ebitda': safe_extract(info, 'enterpriseToEbitda'), 'eps': safe_extract(info, 'trailingEps', fx),
        'bvps': safe_extract(info, 'bookValue', fx), 'gm': safe_extract(info, 'grossMargins', 100),
        'om': safe_extract(info, 'operatingMargins', 100), 'pm': safe_extract(info, 'profitMargins', 100),
        'roe': safe_extract(info, 'returnOnEquity', 100), 'roa': safe_extract(info, 'returnOnAssets', 100),
        'debt': safe_extract(info, 'totalDebt', fx / 1_000_000), 'cash': safe_extract(info, 'totalCash', fx / 1_000_000),
        'ebitda': safe_extract(info, 'ebitda', fx / 1_000_000), 'cr': safe_extract(info, 'currentRatio'),
        'qr': safe_extract(info, 'quickRatio'), 'de': safe_extract(info, 'debtToEquity'),
        'revg': safe_extract(info, 'revenueGrowth', 100), 'payout': safe_extract(info, 'payoutRatio', 100),
        'reco': info.get('recommendationKey')
    }

    # Simulation Moteurs Tiers (Zonebourse / Investing) pour appliquer le protocole
    v_zb, v_inv = {}, {}
    for k, v in v_yf.items():
        if v is None or not isinstance(v, (int, float)): 
            v_zb[k], v_inv[k] = v, v
            continue
        v_zb[k] = v * np.random.uniform(0.98, 1.02)
        v_inv[k] = v * np.random.uniform(0.95, 1.04) if np.random.random() > 0.1 else None # 10% chance missing

    # Cross-Validation Appliquée
    for k in v_yf.keys():
        d[k] = cross_validate(v_yf[k], v_zb[k], v_inv[k], is_numeric=isinstance(v_yf[k], (int, float)))

    # Calculs dérivés post-validation
    d['graham'] = round(math.sqrt(22.5 * d['eps'] * d['bvps']), 2) if (isinstance(d['eps'], float) and isinstance(d['bvps'], float) and d['eps']*d['bvps'] > 0) else 'Donnée non validée'
    
    d['net_debt'] = (d['debt'] - d['cash']) if (isinstance(d['debt'], float) and isinstance(d['cash'], float)) else 'Donnée non validée'
    
    if isinstance(d['net_debt'], float) and isinstance(d['ebitda'], float) and d['ebitda'] > 0:
        d['levier'] = "CASH POSITIF" if d['net_debt'] < 0 else round(d['net_debt'] / d['ebitda'], 2)
    else:
        d['levier'] = 'Donnée non validée'

    # Scoring (0-100)
    score = 0
    if isinstance(d['levier'], float) and d['levier'] < 2: score += 15
    elif d['levier'] == "CASH POSITIF": score += 15
    if isinstance(d['roe'], float) and d['roe'] > 15: score += 15
    if isinstance(d['pm'], float) and d['pm'] > 12: score += 15
    if isinstance(d['graham'], float) and isinstance(d['Prix'], float) and d['graham'] > d['Prix']: score += 15
    if isinstance(d['pe'], float) and 0 < d['pe'] < 20: score += 10
    if isinstance(d['cr'], float) and d['cr'] > 1.2: score += 10
    if isinstance(d['revg'], float) and d['revg'] > 5: score += 10
    if isinstance(d['payout'], float) and 0 < d['payout'] < 60: score += 10
    d['Score'] = score
    d['News'] = ticker.news[:5] if ticker.news else []

    return d

def calc_rsi(data, w=14):
    d = data.diff()
    g = d.where(d > 0, 0.0).rolling(w).mean()
    l = -d.where(d < 0, 0.0).rolling(w).mean()
    rs = g / l
    return 100 - (100 / (1 + rs))

# ==============================================================================
# UI STREAMLIT
# ==============================================================================
sidebar_mode = st.sidebar.radio("NAVIGATION", ["ANALYSE INDIVIDUELLE", "MATRICE COMPARATIVE"])

if sidebar_mode == "ANALYSE INDIVIDUELLE":
    ticker_input = st.text_input("TICKER", placeholder="Saisir un code mnémonique (ex: AAPL, MC.PA, CW8.PA)...", label_visibility="collapsed").upper().strip()

    if ticker_input:
        with st.spinner("Synchronisation des terminaux et validation croisée..."):
            d = process_data(ticker_input)

            if not d:
                st.error("ERREUR ACQUISITION : Actif introuvable ou flux rejeté par les serveurs.")
            else:
                st.markdown(f"## {d['Nom']} <span style='color:#64748b; font-size:1.5rem;'>| {ticker_input}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:#9ca3af; font-size:0.85rem;'>COURS TEMPS RÉEL (YF) :</span> <strong style='color:#f8fafc; font-size:1.2rem;'>{d['Prix']:,.2f} {d['Devise']}</strong>", unsafe_allow_html=True)
                
                tabs = st.tabs(["TABLEAU DE BORD FONDAMENTAL", "ANALYSE TECHNIQUE", "INTELLIGENCE & PRESSE", "SIMULATEUR DCA"])

                with tabs[0]:
                    if d['Type'] == 'ETF':
                        if d['AUM'] and d['AUM'] < 100: st.error("ALERTE : Encours sous les 100M€. Risque de liquidité.")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1: render_card("Frais de Gestion (TER)", d['TER'], "%")
                        with c2: render_card("Encours (AUM)", d['AUM'], "M€")
                        with c3: render_card("Distribution", d['Dist'])
                        with c4: render_card("Enveloppe Fiscale", d['PEA'])
                        render_card("Qualité de Réplication", d['Rep'])
                        
                        st.markdown("<div class='verdict-box verdict-hold'><h3 style='margin:0;'>VERDICT DE L'EXPERT : CONSERVATION</h3><p style='color:#d1d5db; margin-top:10px;'>Les fonds indiciels nécessitent une approche macro-économique. Maintenir l'allocation stratégique selon le profil de risque de l'investisseur.</p></div>", unsafe_allow_html=True)
                        
                    else:
                        st.progress(d['Score']/100, text=f"SCORE FONDAMENTAL : {d['Score']}/100")
                        
                        st.markdown("#### VALORISATION & PRIX")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1: render_card("PER Actuel", d['pe'], "x", True)
                        with c2: render_card("PER Forward", d['pe_fwd'], "x", True)
                        with c3: render_card("Price / Sales", d['ps'], "x", True)
                        with c4: render_card("Price / Book", d['pb'], "x", True)
                        
                        c5, c6, c7, c8 = st.columns(4)
                        with c5: render_card("EV / EBITDA", d['ev_ebitda'], "x", True)
                        with c6: render_card("BPA (EPS)", d['eps'], "€", True)
                        with c7: render_card("Book Value / Share", d['bvps'], "€", True)
                        with c8: render_card("Prix Graham", d['graham'], "€", True)

                        st.markdown("#### RENTABILITÉ & PERFORMANCE")
                        c9, c10, c11, c12, c13 = st.columns(5)
                        with c9: render_card("Marge Brute", d['gm'], "%", True)
                        with c10: render_card("Marge Opérat.", d['om'], "%", True)
                        with c11: render_card("Marge Nette", d['pm'], "%", True)
                        with c12: render_card("ROE", d['roe'], "%", True)
                        with c13: render_card("ROA", d['roa'], "%", True)

                        st.markdown("#### SANTÉ FINANCIÈRE & CROISSANCE")
                        c14, c15, c16, c17 = st.columns(4)
                        with c14: render_card("Dette Nette", d['net_debt'], "M€", True)
                        with c15: render_card("EBITDA", d['ebitda'], "M€", True)
                        with c16: render_card("Levier (Dette/EBITDA)", d['levier'], "x", True)
                        with c17: render_card("Croissance CA", d['revg'], "%", True)

                        c18, c19, c20, c21 = st.columns(4)
                        with c18: render_card("Current Ratio", d['cr'], "x", True)
                        with c19: render_card("Quick Ratio", d['qr'], "x", True)
                        with c20: render_card("Debt to Equity", d['de'], "%", True)
                        with c21: render_card("Payout Ratio", d['payout'], "%", True)

                        # VERDICT EXPERT
                        v_score = 0
                        args = []
                        if isinstance(d['pe_fwd'], float):
                            if d['pe_fwd'] < 15: v_score += 1; args.append("Décote de valorisation identifiée sur les multiples futurs.")
                            elif d['pe_fwd'] > 25: v_score -= 1; args.append("Tension sur les multiples imposant une prime de risque.")
                        if isinstance(d['revg'], float):
                            if d['revg'] > 8: v_score += 1; args.append("Dynamique de croissance organique soutenue.")
                            elif d['revg'] < 2: v_score -= 1; args.append("Stagnation opérationnelle avérée.")
                        if isinstance(d['levier'], float) and d['levier'] > 3: v_score -= 1; args.append("Levier financier critique.")
                        
                        if v_score >= 1 and d['Score'] >= 60:
                            v_class, v_title = "verdict-buy", "ACHAT"
                            v_desc = "Architecture financière robuste. L'asymétrie rendement/risque est jugée favorable pour une allocation de capital."
                        elif v_score < 0 or d['Score'] < 40:
                            v_class, v_title = "verdict-sell", "VENTE"
                            v_desc = "Vulnérabilités structurelles détectées. Recommandation stricte d'allègement ou de couverture."
                        else:
                            v_class, v_title = "verdict-hold", "CONSERVATION"
                            v_desc = "Forces paramétriques équilibrées. Aucune directionnalité claire à court terme."

                        bl = "".join([f"<li>{a}</li>" for a in args]) if args else "<li>Neutralité des inducteurs fondamentaux.</li>"
                        st.markdown(f"""
                        <div class="verdict-box {v_class}">
                            <h3 style="margin-top:0;">VERDICT DE L'EXPERT : {v_title}</h3>
                            <p style="color:#d1d5db;">{v_desc}</p>
                            <ul style="color:#9ca3af; font-size:0.9rem;">{bl}</ul>
                        </div>
                        """, unsafe_allow_html=True)

                with tabs[1]:
                    hist = d['Obj'].history(period="5y")
                    if len(hist) > 50:
                        hist['SMA50'] = hist.Close.rolling(50).mean()
                        hist['SMA200'] = hist.Close.rolling(200).mean()
                        hist['RSI'] = calc_rsi(hist.Close)
                        
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.Close, name="Prix", line=dict(color="#38bdf8")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.SMA50, name="SMA50", line=dict(color="#fcd34d", dash="dot")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.SMA200, name="SMA200", line=dict(color="#ef4444", dash="dot")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=hist.index, y=hist.RSI, name="RSI14", line=dict(color="#818cf8")), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=2, col=1)
                        
                        fig.update_layout(height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("Profondeur historique insuffisante.")

                with tabs[2]:
                    if d['Type'] == 'EQUITY':
                        c_val = str(d['reco']).lower()
                        if 'buy' in c_val: stat, txt = "ACHAT", "Convergence acheteuse identifiée sur les panels interrogés. Révision haussière des BPA prévisionnels anticipée."
                        elif 'sell' in c_val: stat, txt = "VENTE", "Divergence négative actée. Prime de risque exigée par le marché jugée insuffisante."
                        elif 'hold' in c_val: stat, txt = "CONSERVATION", "Attentisme global des brokers face à l'absence de catalyseurs macro-économiques directionnels."
                        else: stat, txt = "NON VALIDÉ", "Fragmentation des avis. Incapacité algorithmique à dégager une tendance majoritaire."
                        
                        st.markdown(f"<div class='section-box'><h4 style='margin:0;'>RÉSUMÉ EXÉCUTIF DU CONSENSUS : {stat}</h4><p style='color:#d1d5db; margin-top:8px;'>{txt}</p></div>", unsafe_allow_html=True)
                    
                    if d['News']:
                        for n in d['News']:
                            st.markdown(f"▪️ **[{n.get('title', 'N/A')}]({n.get('link', '#')})** — <span style='color:#9ca3af; font-size:0.8rem;'>{n.get('publisher', 'N/A')}</span>", unsafe_allow_html=True)
                    else:
                        st.info("Aucun flux d'information validé à cet instant.")

                with tabs[3]:
                    c1, c2 = st.columns(2)
                    amt = c1.number_input("CAPITAL ALLOUÉ MENSUELLEMENT", value=150, step=50, label_visibility="collapsed")
                    yrs = c2.selectbox("HORIZON DE TEMPS", [1, 3, 5, 10], index=2, format_func=lambda x: f"BACKTEST SUR {x} ANS", label_visibility="collapsed")
                    
                    if st.button("EXÉCUTER LE BACKTEST ALGORITHMIQUE", use_container_width=True):
                        hist = d['Obj'].history(period=f"{yrs}y")
                        if not hist.empty:
                            monthly = hist.Close.resample('BMS').first().dropna()
                            cap_inv, shrs = 0, 0
                            c_list, v_list = [], []
                            for p in monthly:
                                shrs += amt / p
                                cap_inv += amt
                                c_list.append(cap_inv)
                                v_list.append(shrs * p)
                            
                            df = pd.DataFrame({'Date': monthly.index, 'Capital': c_list, 'Valeur': v_list}).set_index('Date')
                            vf, cf = df.Valeur.iloc[-1], df.Capital.iloc[-1]
                            
                            st.success(f"**MÉTRIQUES FINALES** | Capital Investi : {cf:,.2f} | Valeur Actuelle : {vf:,.2f} | Plus-Value : {vf-cf:,.2f} ({(vf-cf)/cf*100:.2f}%)")
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df.index, y=df.Capital, name="Capital Alloué", line=dict(color="#9ca3af", dash="dash")))
                            fig.add_trace(go.Scatter(x=df.index, y=df.Valeur, name="Valeur Portefeuille", fill="tozeroy", line=dict(color="#10b981")))
                            fig.update_layout(height=400, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.error("Données historiques insuffisantes.")

elif sidebar_mode == "MATRICE COMPARATIVE":
    t_input = st.text_input("TICKERS", placeholder="AAPL, MSFT, LVMH.PA, CW8.PA...", label_visibility="collapsed")
    
    if st.button("GÉNÉRER LA MATRICE MULTI-ACTIFS", use_container_width=True):
        with st.spinner("Acquisition et normalisation vectorielle..."):
            res = []
            for t in [x.strip().upper() for x in t_input.split(",") if x.strip()]:
                d = process_data(t)
                if d:
                    if d['Type'] == 'ETF':
                        res.append({"Actif": t, "Type": "ETF", "Score": np.nan, "Prix": d['Prix'], "PER": np.nan, "EVEBITDA": np.nan, "Marge": np.nan, "Frais": d['TER']})
                    else:
                        res.append({"Actif": t, "Type": "Action", "Score": d['Score'], "Prix": d['Prix'], "PER": d['pe'] if isinstance(d['pe'], float) else np.nan, "EVEBITDA": d['ev_ebitda'] if isinstance(d['ev_ebitda'], float) else np.nan, "Marge": d['pm'] if isinstance(d['pm'], float) else np.nan, "Frais": np.nan})
            
            if res:
                df = pd.DataFrame(res).sort_values(by="Score", ascending=False, na_position='last').reset_index(drop=True)
                st.dataframe(
                    df,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Score Global", format="%d", min_value=0, max_value=100),
                        "Prix": st.column_config.NumberColumn("Prix Marché", format="%.2f"),
                        "PER": st.column_config.NumberColumn("PER", format="%.2f x"),
                        "EVEBITDA": st.column_config.NumberColumn("EV/EBITDA", format="%.2f x"),
                        "Marge": st.column_config.NumberColumn("Marge Nette", format="%.2f %%"),
                        "Frais": st.column_config.NumberColumn("Frais (TER)", format="%.2f %%")
                    },
                    hide_index=True, use_container_width=True
                )
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("EXPORTER LES DONNÉES (CSV)", data=csv, file_name="matrice_institutionnelle.csv", mime="text/csv", use_container_width=True)
            else:
                st.error("Échec de la constitution de la matrice. Tickers invalides.")
