import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Alpha Scanner", layout="wide")

st.title("🏛️ Kalshi Daily Alpha Scanner & Scoring Engine")
st.write("Algorithmic multi-market filter surfacing high-conviction event wagers.")

# Robust public gateway endpoint
URL = "https://external-api.kalshi.com/trade-api/v2/markets"

st.info("🔄 Connecting to Kalshi pricing feed to calculate algorithmic alpha models...")

try:
    # Query live open market entries
    params = {"status": "open", "limit": 120}
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
                ticker = m.get('ticker', 'N/A')
                volume = m.get('volume', 0)
                
                # Using 'last_price' which is reliably populated in bulk lookups
                last_price_cents = m.get('last_price', 0)
                
                # Only analyze if the market has been priced/traded
                if last_price_cents > 0 and last_price_cents < 100:
                    implied_prob = last_price_cents # In binary options, 65 cents = 65% implied probability
                    
                    # --- CORE ALGORITHMIC SCORING ENGINE ---
                    # 1. Consensus Score: Points for market certainty (furthest from a 50/50 toss-up)
                    distance_from_center = abs(implied_prob - 50)
                    consensus_score = (distance_from_center / 50) * 70  # Max 70 points
                    
                    # 2. Liquidity Score: Points for heavy market activity backing the data
                    liquidity_score = min(30, (volume / 15000) * 30)   # Max 30 points
                    
                    # Generate combined ultimate score
                    total_confidence_score = round(consensus_score + liquidity_score, 1)
                    
                    # Establish target entry side
                    if implied_prob >= 50:
                        recommended_position = "YES"
                        entry_cost = f"{int(last_price_cents)}¢"
                    else:
                        recommended_position = "NO"
                        entry_cost = f"{int(100 - last_price_cents)}¢"
                        
                    parsed_markets.append({
                        "Confidence Score": total_confidence_score,
                        "Category": category,
                        "Market Contract": title,
                        "Target Position": recommended_position,
                        "Current Price": entry_cost,
                        "Implied Prob": f"{implied_prob}%",
                        "Volume": volume
                    })
            
            # Print layout container
            if parsed_markets:
                df = pd.DataFrame(parsed_markets)
                df_sorted = df.sort_values(by="Confidence Score", ascending=False)
                
                # --- VIEW 1: TOP ALPHAS ---
                st.subheader("🎯 Top High-Conviction Trades")
                st.write("Highest-ranking trades based on statistical market consensus and historical volume blocks:")
                
                top_trades = df_sorted.head(10)
                st.dataframe(
                    top_trades[["Confidence Score", "Category", "Market Contract", "Target Position", "Current Price", "Volume"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                # --- VIEW 2: CATEGORIES ---
                st.markdown("---")
                st.subheader("📁 Explore Deep Market Scoring by Category")
                categories = df_sorted["Category"].unique()
                tabs = st.tabs(list(categories))
                
                for i, cat in enumerate(categories):
                    with tabs[i]:
                        cat_df = df_sorted[df_sorted["Category"] == cat]
                        st.dataframe(
                            cat_df[["Confidence Score", "Market Contract", "Target Position", "Current Price", "Implied Prob", "Volume"]],
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                st.warning("⚠️ Data received, but matching trading parameters are still forming for these slates.")

except Exception as e:
    st.error(f"An unexpected data pipeline error occurred: {e}")
