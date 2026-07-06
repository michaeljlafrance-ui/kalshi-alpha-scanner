import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Alpha Scanner", layout="wide")

st.title("🏛️ Kalshi Daily Alpha Scanner & Scoring Engine")
st.write("Algorithmic multi-market filter surfacing high-conviction event wagers.")

# Public cluster endpoints
URL = "https://external-api.kalshi.com/trade-api/v2/markets"

st.info("🔄 Connecting to Kalshi live market arrays...")

try:
    # Query live open contracts
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
                volume = m.get('volume', 0)
                
                # Resilient pricing grab (checks for last_price, yes_bid, or defaults to a stable 50 midpoint)
                last_price = m.get('last_price') or m.get('yes_bid') or 50
                
                # Enforce safe bounds
                if last_price <= 0 or last_price >= 100:
                    last_price = 50
                    
                implied_prob = last_price
                
                # --- ALGORITHMIC SCORING ENGINE ---
                # 1. Consensus Weight: Higher points for entries showing extreme market skew
                distance_from_center = abs(implied_prob - 50)
                consensus_score = (distance_from_center / 50) * 50  # Max 50 points
                
                # 2. Activity Weight: Points awarded based on institutional market liquidity
                liquidity_score = min(50, (volume / 10000) * 50)   # Max 50 points
                
                # Ultimate Weighted Metric Score
                total_confidence_score = round(consensus_score + liquidity_score, 1)
                
                # Formulate target recommendation sides
                if implied_prob >= 50:
                    recommended_position = "YES"
                    entry_cost = f"{int(last_price)}¢"
                else:
                    recommended_position = "NO"
                    entry_cost = f"{int(100 - last_price)}¢"
                    
                parsed_markets.append({
                    "Confidence Score": total_confidence_score,
                    "Category": category,
                    "Market Contract": title,
                    "Target Position": recommended_position,
                    "Est Entry Cost": entry_cost,
                    "Implied Prob": f"{int(implied_prob)}%",
                    "Volume": volume
                })
            
            # Render out Data Frames
            if parsed_markets:
                df = pd.DataFrame(parsed_markets)
                
                # Sort everything solely by your custom confidence metric
                df_sorted = df.sort_values(by="Confidence Score", ascending=False)
                
                # --- VIEW 1: LEADERBOARD ---
                st.subheader("🎯 Top High-Conviction Trades")
                st.write("Highest-ranking trades based on current platform consensus and transaction volume:")
                
                top_trades = df_sorted.head(10)
                st.dataframe(
                    top_trades[["Confidence Score", "Category", "Market Contract", "Target Position", "Est Entry Cost", "Volume"]],
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
                            cat_df[["Confidence Score", "Market Contract", "Target Position", "Est Entry Cost", "Implied Prob", "Volume"]],
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                st.warning("⚠️ High-volume structures are organizing lines. Refresh in a few moments.")

except Exception as e:
    st.error(f"An unexpected mathematical data pipeline error occurred: {e}")
