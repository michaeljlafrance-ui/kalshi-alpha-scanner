import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Alpha Scanner", layout="wide")

st.title("🏛️ Kalshi Daily Alpha Scanner")
st.write("Real-time data pipeline scanning multi-market contract inefficiencies across Kalshi.")

# Kalshi V2 Public Markets API Endpoint
URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

st.info("🔄 Connecting to Kalshi Central Limit Order Book...")

try:
    # Query open, active markets on the platform
    params = {"status": "open", "limit": 100}
    response = requests.get(URL, params=params)
    
    if response.status_code != 200:
        st.error(f"⚠️ Unable to reach Kalshi exchange servers. Status: {response.status_code}")
    else:
        market_data = response.json().get('markets', [])
        
        if not market_data:
            st.warning("📅 No open trading contracts returned from the board.")
        else:
            st.success(f"📈 Successfully ingested {len(market_data)} active global Kalshi contracts!")
            
            # Parse the contracts into a clean structure
            parsed_markets = []
            for m in market_data:
                category = m.get('category', 'General')
                title = m.get('title', 'Unknown Contract')
                ticker = m.get('ticker_ticker', 'N/A')
                
                # Get current market pricing
                yes_bid = m.get('yes_bid', 0) / 100  # Convert to cents dollar format
                yes_ask = m.get('yes_ask', 0) / 100
                
                # Calculate market implied probability midpoint
                if yes_bid and yes_ask:
                    implied_prob = ((yes_bid + yes_ask) / 2) * 100
                else:
                    implied_prob = 0
                    
                volume = m.get('volume', 0)
                
                parsed_markets.append({
                    "Category": category.upper(),
                    "Market Description": title,
                    "Ticker": ticker,
                    "Implied Probability": f"{implied_prob:.1f}%",
                    "Volume": volume,
                    "Yes Bid (¢)": f"{int(yes_bid*100)}¢",
                    "Yes Ask (¢)": f"{int(yes_ask*100)}¢"
                })
                
            # Convert to a DataFrame for clean sorting and display
            df = pd.DataFrame(parsed_markets)
            
            # --- HIGHEST CONFIDENCE SCANNER VIEW ---
            st.subheader("🎯 High-Volume Baseline Conviction Contracts")
            st.write("These contracts show heavy market participation and tight pricing arrays:")
            
            # Sort by highest trade volume to see where the market is most confident
            high_vol_df = df.sort_values(by="Volume", ascending=False).head(10)
            st.dataframe(high_vol_df, use_container_width=True, hide_index=True)
            
            # --- CROSS CATEGORY BREAKDOWNS ---
            st.markdown("---")
            st.subheader("📁 Categorized Market Boards")
            categories = df["Category"].unique()
            
            # Create interactive tabs for each category on Kalshi
            tabs = st.tabs(list(categories))
            for i, cat in enumerate(categories):
                with tabs[i]:
                    cat_df = df[df["Category"] == cat]
                    st.dataframe(cat_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"An unexpected data pipeline failure occurred: {e}")
