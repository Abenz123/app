import streamlit as st
import yfinance as yf
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Buffett Stock Analyzer", layout="wide", page_icon="📈")

st.title("🧙‍♂️ Warren Buffett Style Stock Analyzer (NSE)")
st.markdown("""
This tool analyzes NSE stocks based on 4 key Buffett/Graham principles:
1.  **Margin of Safety:** Is the price below the intrinsic value?
2.  **Efficiency:** Is ROE > 15%?
3.  **Financial Health:** Is Debt-to-Equity < 0.5?
4.  **Economic Moat:** Is Operating Margin > 20%?
""")

# --- HELPER FUNCTION WITH CACHING ---
@st.cache_data(ttl=300)  # Cache data for 5 minutes to speed up the app
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

# --- INPUT SECTION ---
col_input, col_btn = st.columns([3, 1])
with col_input:
    symbol_input = st.text_input("Enter Stock Symbol (NSE)", value="INFY", placeholder="e.g., TATAMOTORS").upper()
with col_btn:
    st.write("##") # Spacer
    analyze_btn = st.button("Analyze Stock", type="primary")

if analyze_btn:
    # Append .NS for NSE stocks if not present
    ticker_symbol = f"{symbol_input}.NS" if not symbol_input.endswith(".NS") else symbol_input
    
    with st.spinner(f'Fetching fundamental data for {ticker_symbol}...'):
        try:
            info = get_stock_data(ticker_symbol)
            
            if not info or 'regularMarketPrice' not in info:
                st.error("Could not fetch data. The stock might be delisted or the symbol is incorrect.")
            else:
                # --- 1. DATA EXTRACTION (With Safe Defaults) ---
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                market_cap = info.get('marketCap', 0)
                pe_ratio = info.get('trailingPE', 0)
                roe = (info.get('returnOnEquity', 0) or 0) * 100
                debt_to_equity = (info.get('debtToEquity', 0) or 0) / 100
                op_margin = (info.get('operatingMargins', 0) or 0) * 100
                eps = info.get('trailingEps', 0)
                
                # --- 2. CALCULATE INTRINSIC VALUE (Graham's Formula) ---
                # Fallback: If earnings growth is missing, assume a modest 5%
                growth_estimate = (info.get('earningsGrowth', 0.05) or 0.05) * 100
                
                # Cap growth at 15% (Buffett rarely projects higher for perpetuity)
                capped_growth = min(growth_estimate, 15)
                capped_growth = max(capped_growth, 0) # Ensure no negative growth in formula
                
                # Graham's Formula: V = EPS * (8.5 + 2g)
                # Note: If EPS is negative, intrinsic value logic breaks. We handle that below.
                if eps > 0:
                    intrinsic_value = eps * (8.5 + (2 * capped_growth))
                else:
                    intrinsic_value = 0 # Company is losing money
                
                # --- 3. BUFFETT'S CHECKLIST ---
                score = 0
                results = []

                # Check 1: Cheap? (Margin of Safety)
                is_cheap = current_price < intrinsic_value and intrinsic_value > 0
                if is_cheap: score += 1
                results.append({
                    "Criteria": "Undervalued (Margin of Safety)", 
                    "Value": f"₹{current_price} vs ₹{intrinsic_value:.2f}", 
                    "Pass": "✅" if is_cheap else "❌"
                })

                # Check 2: Efficient? (ROE > 15%)
                is_efficient = roe > 15
                if is_efficient: score += 1
                results.append({
                    "Criteria": "High ROE (>15%)", 
                    "Value": f"{roe:.2f}%", 
                    "Pass": "✅" if is_efficient else "❌"
                })

                # Check 3: Safe? (Debt to Equity < 0.5)
                # Note: Financial stocks (Banks/NBFCs) naturally have high D/E.
                is_safe = debt_to_equity < 0.5
                if is_safe: score += 1
                results.append({
                    "Criteria": "Low Debt (D/E < 0.5)", 
                    "Value": f"{debt_to_equity:.2f}", 
                    "Pass": "✅" if is_safe else "❌"
                })

                # Check 4: Moat? (High Margins)
                is_moat = op_margin > 20
                if is_moat: score += 1
                results.append({
                    "Criteria": "Strong Moat (Op. Margin > 20%)", 
                    "Value": f"{op_margin:.2f}%", 
                    "Pass": "✅" if is_moat else "❌"
                })

                # --- 4. DISPLAY DASHBOARD ---
                st.divider()
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("Verdict")
                    final_verdict = "WAIT / WATCH"
                    color = "orange"
                    if score == 4:
                        final_verdict = "STRONG BUY"
                        color = "green"
                    elif score == 3:
                        final_verdict = "BUY"
                        color = "lightgreen"
                    elif score <= 1:
                        final_verdict = "AVOID"
                        color = "red"
                    
                    st.markdown(f"## :{color}[{final_verdict}]")
                    st.metric(label="Score", value=f"{score}/4")
                    
                    st.info(f"**Growth Used:** {capped_growth:.1f}% (Capped at 15%)")

                with col2:
                    st.subheader("Financial Checklist")
                    df_results = pd.DataFrame(results)
                    st.table(df_results)
                    
                    with st.expander("📖 Read Company Profile"):
                        st.write(info.get('longBusinessSummary', 'No description available.'))

        except Exception as e:
            st.error(f"Error analyzing {symbol_input}. Details: {e}")
