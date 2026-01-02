import streamlit as st
import yfinance as yf
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Buffett Stock Analyzer", layout="wide")

st.title("🧙‍♂️ Warren Buffett Style Stock Analyzer (NSE)")
st.markdown("Enter an NSE Stock Symbol (e.g., `TCS`, `INFY`, `RELIANCE`) to check if it fits Buffett's criteria.")

# --- INPUT SECTION ---
symbol_input = st.text_input("Enter Stock Symbol (NSE)", value="INFY").upper()

if st.button("Analyze Stock"):
    # Append .NS for NSE stocks if not present
    ticker_symbol = f"{symbol_input}.NS" if not symbol_input.endswith(".NS") else symbol_input
    stock = yf.Ticker(ticker_symbol)
    
    with st.spinner(f'Fetching data for {symbol_input}...'):
        try:
            info = stock.info
            
            # --- 1. DATA EXTRACTION ---
            current_price = info.get('currentPrice', 0)
            eps = info.get('trailingEps', 0)
            roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
            debt_to_equity = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
            op_margin = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0
            
            # --- 2. CALCULATE INTRINSIC VALUE (Graham's Formula) ---
            growth_estimate = info.get('earningsGrowth', 0.10) * 100
            if growth_estimate > 15: growth_estimate = 15 # Cap growth at 15% (conservative)
            if growth_estimate < 0: growth_estimate = 0
            
            intrinsic_value = eps * (8.5 + (2 * growth_estimate))
            
            # --- 3. BUFFETT'S CHECKLIST ---
            score = 0
            results = []

            # Check 1: Cheap?
            is_cheap = current_price < intrinsic_value
            if is_cheap: score += 1
            results.append({"Criteria": "Undervalued (Margin of Safety)", "Value": f"₹{current_price} vs ₹{intrinsic_value:.2f}", "Pass": "✅" if is_cheap else "❌"})

            # Check 2: Efficient?
            is_efficient = roe > 15
            if is_efficient: score += 1
            results.append({"Criteria": "High ROE (>15%)", "Value": f"{roe:.2f}%", "Pass": "✅" if is_efficient else "❌"})

            # Check 3: Safe?
            is_safe = debt_to_equity < 0.5
            if is_safe: score += 1
            results.append({"Criteria": "Low Debt (D/E < 0.5)", "Value": f"{debt_to_equity:.2f}", "Pass": "✅" if is_safe else "❌"})

            # Check 4: Moat?
            is_moat = op_margin > 20
            if is_moat: score += 1
            results.append({"Criteria": "Strong Moat (Margin > 20%)", "Value": f"{op_margin:.2f}%", "Pass": "✅" if is_moat else "❌"})

            # --- 4. DISPLAY DASHBOARD ---
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric(label="Current Price", value=f"₹{current_price}")
                st.metric(label="Intrinsic Value (Est.)", value=f"₹{intrinsic_value:.2f}", 
                          delta=f"{round(((intrinsic_value-current_price)/current_price)*100, 1)}% Upside" if is_cheap else f"{round(((intrinsic_value-current_price)/current_price)*100, 1)}% Overvalued")
                
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
                
                st.markdown(f"### Verdict: :{color}[{final_verdict}]")
                st.write(f"**Score: {score}/4 Criteria Passed**")

            with col2:
                st.subheader("Buffett's Checklist")
                st.table(pd.DataFrame(results))

            # --- 5. NEW: PRICE CHART SECTION ---
            st.markdown("---")
            st.subheader(f"📉 {symbol_input} 5-Year Price History")
            
            # Fetch history
            hist = stock.history(period="5y")
            
            if not hist.empty:
                # Plot the 'Close' column
                st.line_chart(hist['Close'])
            else:
                st.warning("No price history available.")

        except Exception as e:
            st.error(f"Error analyzing {symbol_input}: {e}")
