import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Alpha Scanner", layout="wide")

st.title("🏛️ Kalshi Daily Alpha Scanner & Scoring Engine")
st.write("Algorithmic multi-market filter surfacing high-conviction event trades.")

URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

st.info("🔄 Connecting to Kalshi Order Book to process algorithmic scores...")

try:
    # Pull active open contracts
    params = {"status": "open", "limit": 150}
    response = requests.get(URL, params=params)
    
    if response.status_code != 200:
        st.error(f"⚠️ Unable to reach Kalshi exchange servers. Status: {response.status_code}")
    else:
        market_data = response.json().get('markets', [])
        
        if not market_data:
            st.warning("📅 No open trading contracts returned from the board.")
        else:
            parsed_markets = []
            for m in market_data:
                category = m.get('category', 'General').upper()
                title = m.get('title', 'Unknown Contract')
                ticker = m.get('ticker_ticker', 'N/A')
                
                # Pricing details
                yes_bid = m.get('yes_bid', 0) / 100
                yes_ask = m.get('yes_ask', 0) / 100
                volume = m.get('volume', 0)
                
                if yes_bid and yes_ask:
                    midpoint = (yes_bid + yes_ask) / 2
                    implied_prob = midpoint * 100
                    
                    # --- CORE ALGORITHMIC SCORING ENGINE ---
                    # 1. Consensus Score: Reward extreme high or low probabilities
                    distance_from_center = abs(implied_prob - 50)
                    consensus_score = (distance_from_center / 50) * 60 # Weights up to 60 points
                    
                    # 2. Liquidity Score: Reward deep volume profiles
                    liquidity_score = min(30, (volume / 50000) * 30) # Weights up to 30 points
                    
                    # 3. Spread Score: Reward tight bid-ask spreads (lower transaction drag)
                    spread = abs(yes_ask - yes_bid) * 100
                    spread_score = max(0, 10 - spread) # Weights up to 10 points
                    
                    # Generate ultimate combined conviction metric
                    total_confidence_score = consensus_score + liquidity_score + spread_score
                    
                    # Map the target optimal trade orientation
                    if implied_prob >= 50:
                        recommended_position = "YES"
                        market_price = f"{int(yes_ask * 100)}¢"
                    else:
                        recommended_position = "NO"
                        market_price = f"{int((1 - yes_bid) * 100)}¢"
                        
                    parsed_markets.append({
                        "Confidence Score": round(total_confidence_score, 1),
                        "Category": category,
                        "Market Contract": title,
                        "Target Position": recommended_position,
                        "Entry Cost": market_price,
                        "Implied Prob": f"{implied_prob:.1f}%",
                        "Volume": volume
                    })
            
            # Convert arrays to structural DataFrame
            df = pd.DataFrame(parsed_markets)
            
            # Sort solely by the highest scoring trades on the entire exchange
            df_sorted = df.sort_values(by="Confidence Score", ascending=False)
            
            # --- VIEW 1: TOP HIGH-CONFIDENCE TRADES FOR TODAY ---
            st.subheader("🎯 Top High-Conviction Trades")
            st.write("The highest scoring contracts based on extreme statistical consensus and institutional liquidity:")
            
            top_trades = df_sorted.head(7)
            
            # Display beautifully using customized Streamlit metric cards or data table
            st.dataframe(
                top_trades[["Confidence Score", "Category", "Market Contract", "Target Position", "Entry Cost", "Volume"]],
                use_container_width=True,
                hide_index=True
            )
            
            # --- VIEW 2: CATEGORY EXPLORATION ---
            st.markdown("---")
            st.subheader("📁 Explore Deep Market Scoring by Category")
            categories = df["Category"].unique()
            tabs = st.tabs(list(categories))
            
            for i, cat in enumerate(categories):
                with tabs[i]:
                    cat_df = df_sorted[df_sorted["Category"] == cat]
                    st.dataframe(
                        cat_df[["Confidence Score", "Market Contract", "Target Position", "Entry Cost", "Implied Prob", "Volume"]],
                        use_container_width=True,
                        hide_index=True
                    )

except Exception as e:
    st.error(f"An unexpected mathematical data pipeline failure occurred: {e}")
