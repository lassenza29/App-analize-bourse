import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import feedparser
import urllib.parse
import traceback

# Configuration (identique)
st.set_page_config(page_title="Alpha Terminal Pro", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# CSS (identique)
st.markdown("""
<style>
    .stApp { background-color: #09090b; color: #ededed; font-family: 'Inter', sans-serif; }
    .bento-card { background: linear-gradient(145deg, #121214 0%, #0d0d0f 100%); border: 1px solid #27272a; border-radius: 20px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); }
    .bento-header { font-size: 0.9rem; color: #a1a1aa; text-transform: uppercase; margin-bottom: 16px; font-weight: 500; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; }
    .metric-label { font-size: 0.85rem; color: #71717a; margin-bottom: 4px; }
    .metric-value { font-size: 1.6rem; color: #ffffff; font-weight: 700; }
    .score-display { font-size: 4.5rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .expert-verdict-box { background-color: #18181b; border-left: 4px solid #3b82f6; padding: 20px; border-radius: 0 16px 16px 0; }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def safe_float(val, multiplier=1.0, precision=2):
    try:
        if val is None or pd.isna(val) or val == "": return None
        return round(float(val) * multiplier, precision)
    except: return None

def format_metric(val, suffix="", special_class=""):
    if val is None: return "<span style='color:#71717a'>N/A</span>"
    if isinstance(val, (int, float)): formatted = f"{val:,.2f}".replace(",", " ")
    else: formatted = str(val)
    return f"<span class='metric-value {special_class}'>{formatted} <span style='font-size:1rem;color:#71717a'>{suffix}</span></span>"

# --- LOGIQUE PRINCIPALE ---
ticker_input = st.text_input("Recherche Ticker", placeholder="Ex: AAPL ou LVMH.PA").upper().strip()

if ticker_input:
    with st.spinner("Récupération des données..."):
        try:
            tk = yf.Ticker(ticker_input)
            info = tk.info
            
            # Vérification basique de l'existence du ticker
            if 'regularMarketPrice' not in info and 'currentPrice' not in info and 'symbol' not in info:
                st.error("Données insuffisantes pour ce Ticker. Essayez d'ajouter .PA pour les actions françaises.")
                st.stop()

            # Extraction sécurisée (Exemple pour les actions)
            data = {
                'Prix': safe_float(info.get('currentPrice') or info.get('regularMarketPrice')),
                'Score': 0, # Placeholder calcul simplifié
                'Target': safe_float(info.get('targetMeanPrice')),
                'Reco': info.get('recommendationKey', 'N/A').replace('_', ' ').title(),
                'Sector': info.get('sector', 'N/A'),
                'Rev_Growth': safe_float(info.get('revenueGrowth'), 100),
                'Marge_Nette': safe_float(info.get('profitMargins'), 100),
                'ROE': safe_float(info.get('returnOnEquity'), 100),
                'BPA': safe_float(info.get('trailingEps')),
                'PER_Actuel': safe_float(info.get('trailingPE')),
                'Dette_Nette': safe_float(info.get('totalDebt'))
            }

            # Affichage Bento (Exemple)
            st.markdown(f"<h1>{info.get('longName', ticker_input)}</h1>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="bento-card">
                    <div class="bento-header">Marché</div>
                    <div class="metric-label">Prix Actuel</div>
                    <div class="metric-value">{format_metric(data['Prix'], '€')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="bento-card">
                    <div class="bento-header">Analyse</div>
                    <div class="metric-label">Secteur</div>
                    <div class="metric-value">{data['Sector']}</div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erreur technique : {e}")
            with st.expander("Voir les détails"):
                st.code(traceback.format_exc())
