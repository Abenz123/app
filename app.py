import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Buffett Market Scanner", layout="wide", page_icon="🧙‍♂️")

st.title("🧙‍♂️ Warren Buffett Market Scanner (NSE)")
st.markdown("""
**The Philosophy:**
This scanner filters stocks through a "Value Investing Funnel" to find high-quality companies trading at a fair price.
""")

# 

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Scanner Settings")

# Default NIFTY 50 List (Hardcoded for speed/reliability)
NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE",
    "KOTAKBANK", "LT", "HCLTECH", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "BAJAJFINSV",
    "WIPRO", "NESTLEIND", "ONGC", "JSWSTEEL", "POWERGRID", "M&M", "TATASTEEL", "ADANIENT", "NTPC", "GRASIM",
    "TATAMOTORS", "COALINDIA", "HDFCLIFE", "BRITANNIA", "BAJAJ-AUTO", "ADANIPORTS", "CIPLA", "APOLLOHOSP", "DRREDDY",
    "EICHERMOT", "DIVISLAB", "TECHM", "BPCL", "TATACONSUM", "SBILIFE", "HINDALCO", "HEROMOTOCO", "UPL", "INDUSINDBK"
]

# Input method selection
input_method = st.sidebar.radio("Select Stock List:", ("NIFTY 50 (Fast)", "Custom List (Paste Symbols)"))

if input_method == "NIFTY 50 (Fast)":
    tickers_to_scan = [f"{x}.NS" for x in NIFTY_50]
else:
    custom_input = st.sidebar.text_area("Paste NSE Symbols (comma separated):", "TATAELXSI, IRCTC, RVNL, ZOMATO")
    if custom_input:
        cleaned_list = [x.strip().upper() for x in custom_input.split(",")]
        tickers_to_scan = [f"{x}.NS" if not x.endswith(".NS") else x for x in cleaned_list]
    else:
        tickers_to_scan = []

st.sidebar.info(f"Ready to scan **{len(tickers_to_scan)}** stocks.")

# --- ANALYSIS FUNCTION ---
def analyze_stock(ticker):
    """
    Fetches data and calculates the Buffett Score for a single stock.
    Returns a dictionary of results or None if data fails.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic Data Checks
        if not info or 'regularMarketPrice' not in info:
            return None

        # 1. Extraction
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        debt_to_equity = (info.get('debtToEquity', 0) or 0) / 100
        op_margin = (info.get('operatingMargins', 0) or 0) * 100
        eps = info.get('trailingEps', 0)
        
        # 2. Intrinsic Value Calculation (Graham Formula)
        # We cap growth at 15% to be conservative
        growth_estimate = (info.get('earningsGrowth', 0.05) or 0.05) * 100
        capped_growth = min(growth_estimate, 15)
        capped_growth = max(capped_growth, 0)
        
        intrinsic_value = 0
        if eps > 0:
            intrinsic_value = eps * (8.5 + (2 * capped_growth))
        
        # 3. Scoring
        score = 0
        
        # Criteria A: Undervalued?
        is_cheap = (current_price < intrinsic_value) and (intrinsic_value > 0)
        if is_cheap: score += 1
        
        # Criteria B: High ROE?
        is_efficient = roe > 15
        if is_efficient: score += 1
        
        # Criteria C: Low Debt?
        is_safe = debt_to_equity < 0.5
        if is_safe: score += 1
        
        # Criteria D: Moat (High Margins)?
        is_moat = op_margin > 20
        if is_moat: score += 1
        
        # Recommendation Label
        recommendation = "Avoid"
        if score == 4: recommendation = "Strong Buy"
        elif score == 3: recommendation = "Buy"
        elif score == 2: recommendation = "Watch"
        
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Price": round(current_price, 2),
            "Intrinsic Value": round(intrinsic_value, 2),
            "Upside (%)": round(((intrinsic_value - current_price) / current_price) * 100, 1) if current_price else 0,
            "Score": score,
            "Recommendation": recommendation,
            "ROE (%)": round(roe, 1),
            "Debt/Eq": round(debt_to_equity, 2),
            "Op. Margin (%)": round(op_margin, 1)
        }

    except Exception:
        return None

# --- MAIN DASHBOARD ---
if st.sidebar.button("🚀 Start Scanner"):
    if not tickers_to_scan:
        st.error("No symbols found! Please enter symbols or select NIFTY 50.")
    else:
        results_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Limit for demo purposes to avoid getting banned by Yahoo if list is huge
        # (Though NIFTY 50 is safe)
        
        for i, ticker in enumerate(tickers_to_scan):
            status_text.text(f"Scanning {ticker}...")
            data = analyze_stock(ticker)
            if data:
                results_data.append(data)
            
            # Update progress
            progress_bar.progress((i + 1) / len(tickers_to_scan))
        
        status_text.text("Scanning Complete!")
        progress_bar.empty()
        
        # --- DISPLAY RESULTS ---
        if results_data:
            df = pd.DataFrame(results_data)
            
            # Sort by Score (Desc) then Upside (Desc)
            df = df.sort_values(by=["Score", "Upside (%)"], ascending=[False, False])
            
            # Top Stats
            st.write("### 🏆 Top Picks (Buffett Style)")
            
            # Separate High Quality Picks
            top_picks = df[df["Score"] >= 3]
            
            if not top_picks.empty:
                st.success(f"Found {len(top_picks)} potential candidates!")
                st.dataframe(
                    top_picks.style.map(
                        lambda x: 'color: green; font-weight: bold' if x in ['Strong Buy', 'Buy'] else ''
                    ),
                    use_container_width=True
                )
            else:
                st.warning("No stocks met the strict 'Buy' criteria (Score 3 or 4). Market might be overvalued.")

            # Show Full Data in Expander
            with st.expander("📊 View All Scanned Stocks"):
                st.dataframe(df, use_container_width=True)
                
                # CSV Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Download Report as CSV",
                    csv,
                    "buffett_scan_results.csv",
                    "text/csv",
                    key='download-csv'
                )
        else:
            st.error("No valid data found. Check your internet connection or symbols.")

# --- EXPLANATION SECTION ---
st.divider()
st.markdown("""
### 🧠 How this Scanner Works
This tool automates the core checklist of Value Investing.

1.  **Intrinsic Value (Graham's Formula):** We calculate the "Real Value" based on Earnings Per Share (EPS) and Growth. If `Price < Intrinsic Value`, it's on sale.
2.  **ROE (Return on Equity):** Measures how efficient the management is. We look for **>15%**.
3.  **Debt-to-Equity:** High debt kills companies in bad times. We strictly filter for **< 0.5**.
4.  **Operating Margin:** A proxy for a "Moat" or competitive advantage. We look for **>20%**.
""")
