import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Alpha Scanner", layout="wide")

st.title("🏛️ Kalshi Daily Alpha Scanner & Scoring Engine")
st.write("Algorithmic multi-market filter surfacing high-conviction event wagers.")

# Reliable external API route
URL = "https://external-api.kalshi.com/trade-api/v2/markets"

st.info("🔄 Connecting to Kalshi Order Book to process raw algorithmic arrays...")

try:
    # Query live open market books
    params = {"status": "open", "limit": 100}
    response = requests.get(URL, params=params)
    
    if response.status_code != 200:
        st.error(f"⚠️ Unable to reach Kalshi exchange servers. Status: {response.status_code}")
    else:
        market_data = response.json().get('markets', [])
        
        if not market_data:
            st.warning("📅 No open trading contracts returned from the board currently.")
        else:
            parsed_markets = []
            for m in market_data:
                category = str(m.get('category', 'General')).upper()
                title = m.get('title', 'Unknown Contract')
                
                # Correcting target endpoint payload keys
                ticker = m.get('ticker', 'N/A')
                
                # Pull raw buy/sell prices from the central limit order book
                yes_bid_raw = m.get('yes_bid', 0)
                yes_ask_raw = m.get('yes_ask', 0)
                volume = m.get('volume', 0)
                
                # Default safety values if book is depth-empty
                yes_bid = yes_bid_raw / 100 if yes_bid_raw else 0
                yes_ask = yes_ask_raw / 100 if yes_ask_raw else 0
                
                # Process only if active pricing exists on the line
                if yes_bid > 0 and yes_ask > 0:
                    midpoint = (yes_bid + yes_ask) / 2
                    implied_prob = midpoint * 100
                    
                    # --- CORE ALGORITHMIC SCORING ENGINE ---
                    # 1. Consensus Score: Marks deep certainty distributions away from a coin-flip (50%)
                    distance_from_center = abs(implied_prob - 50)
                    consensus_score = (distance_from_center / 50) * 60  # Max 60 points
                    
                    # 2. Liquidity Score: Rewards deep active backing profiles
                    liquidity_score = min(30, (volume / 25000) * 30)   # Max 30 points
                    
                    # 3. Spread Score: Rewards tight books with low friction/drag
                    spread = abs(yes_ask - yes_bid) * 100
                    spread_score = max(0, 10 - spread)                 # Max 10 points
                    
                    # Combined Ultimate Score Matrix
                    total_confidence_score = round(consensus_score + liquidity_score + spread_score, 1)
                    
                    # Establish target positions
                    if implied_prob >= 50:
                        recommended_position = "YES"
                        entry_cost = f"{int(yes_ask_raw)}¢"
                    else:
                        recommended_position = "NO"
                        entry_cost = f"{int(100 - yes_bid_raw)}¢"
                        
                    parsed_markets.append({
                        "Confidence Score": total_confidence_score,
                        "Category": category,
                        "Market Contract": title,
                        "Target Position": recommended_position,
                        "Entry Cost": entry_cost,
                        "Implied Prob": f"{implied_prob:.1f}%",
                        "Volume": volume
                    })
            
            # Construct display logic with defensive verification
            if parsed_markets:
                df = pd.DataFrame(parsed_markets)
                df_sorted = df.sort_values(by="Confidence Score", ascending=False)
                
                # --- VIEW 1: TOP ALPHAS ---
                st.subheader("🎯 Top High-Conviction Trades")
                st.write("Highest-ranking trades based on statistical market consensus and book depth:")
                
                top_trades = df_sorted.head(7)
                st.dataframe(
                    top_trades[["Confidence Score", "Category", "Market Contract", "Target Position", "Entry Cost", "Volume"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- VIEW 2: TABS ---
                st.markdown("---")
                st.subheader("📁 Explore Deep Market Scoring by Category")
                categories = df_sorted["Category"].unique()
                tabs = st.tabs(list(categories))
                
                for i, cat in enumerate(categories):
                    with tabs[i]:
                        cat_df = df_sorted[df_sorted["Category"] == cat]
                        st.dataframe(
                            cat_df[["Confidence Score", "Market Contract", "Target Position", "Entry Cost", "Implied Prob", "Volume"]],
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                st.warning("⚠️ Market data fetched successfully, but active bid/ask lines were completely empty for current items.")

except Exception as e:
    st.error(f"An unexpected data pipeline error occurred: {e}")
