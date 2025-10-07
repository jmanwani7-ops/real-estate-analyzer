import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json

# Page config
st.set_page_config(page_title="Real Estate Deal Analyzer", page_icon="🏠", layout="wide")

# Initialize session state for saved properties
if 'properties' not in st.session_state:
    st.session_state.properties = []

# Helper functions
def calculate_seller_net(price, is_mls=True):
    """Calculate seller net proceeds"""
    listing_agent = price * 0.03
    buyer_agent = price * 0.02 if is_mls else 0
    
    if is_mls:
        prep_costs = 8000 + 6000 + 1500 + 5000 + 3000 + 1000  # paint, clean, repairs, staging, landscaping
        holding_costs = 2000 + 600 + 333  # 2 months property tax, utilities, insurance
    else:
        prep_costs = 0
        holding_costs = 0
    
    transfer_tax = price * 0.0011
    escrow_fees = 1500
    
    total_costs = listing_agent + buyer_agent + prep_costs + holding_costs + transfer_tax + escrow_fees
    net = price - total_costs
    
    return {
        'price': price,
        'listing_agent': listing_agent,
        'buyer_agent': buyer_agent,
        'prep_costs': prep_costs,
        'holding_costs': holding_costs,
        'transaction_costs': transfer_tax + escrow_fees,
        'total_costs': total_costs,
        'net': net
    }

def calculate_buyer_costs(purchase_price, down_pct, interest_rate, remodel_cost, months=4):
    """Calculate buyer all-in costs"""
    down_payment = purchase_price * (down_pct / 100)
    loan_amount = purchase_price * (1 - down_pct / 100)
    
    # Closing costs
    loan_origination = loan_amount * 0.01
    closing_costs = loan_origination + 600 + 500 + 1500 + 1500 + 200
    
    # Seller's agent commission
    seller_agent = purchase_price * 0.03
    
    # Cash to acquire
    cash_to_acquire = down_payment + closing_costs + seller_agent
    
    # Holding costs
    monthly_interest = (loan_amount * (interest_rate / 100)) / 12
    total_interest = monthly_interest * months
    monthly_holding = 1000 + 300 + 167  # property tax, utilities, insurance
    holding_costs = total_interest + (monthly_holding * months)
    
    # Total cash invested
    total_cash = cash_to_acquire + holding_costs + remodel_cost
    
    return {
        'purchase_price': purchase_price,
        'down_payment': down_payment,
        'loan_amount': loan_amount,
        'closing_costs': closing_costs,
        'seller_agent': seller_agent,
        'cash_to_acquire': cash_to_acquire,
        'interest': total_interest,
        'holding_costs': holding_costs,
        'remodel_cost': remodel_cost,
        'total_cash': total_cash
    }

def calculate_flip_profit(buy_costs, sell_price):
    """Calculate profit from flip"""
    commission_4pct = sell_price * 0.04
    transfer_fees = (sell_price * 0.0011) + 3000
    
    net_proceeds = sell_price - commission_4pct - transfer_fees - buy_costs['loan_amount']
    profit = net_proceeds - buy_costs['total_cash']
    roi = (profit / buy_costs['total_cash']) * 100
    
    return {
        'sell_price': sell_price,
        'commission': commission_4pct,
        'transfer_fees': transfer_fees,
        'net_proceeds': net_proceeds,
        'profit': profit,
        'roi': roi
    }

# Main App
st.title("🏠 Real Estate Deal Analyzer")
st.markdown("---")

# Sidebar - Property Input
with st.sidebar:
    st.header("Property Details")
    
    property_name = st.text_input("Property Name/Address", "38173 Canyon Oaks Ct")
    
    col1, col2 = st.columns(2)
    with col1:
        bedrooms = st.number_input("Beds", min_value=1, value=4)
        sqft = st.number_input("Sq Ft", min_value=100, value=2523)
    with col2:
        bathrooms = st.number_input("Baths", min_value=1, value=3)
        year_built = st.number_input("Year Built", min_value=1900, value=1991)
    
    st.markdown("---")
    st.header("Deal Parameters")
    
    analysis_type = st.radio("Analysis Type", ["Seller Analysis", "Buyer/Flip Analysis", "Both"])
    
    if analysis_type in ["Seller Analysis", "Both"]:
        st.subheader("Seller Scenario")
        mls_price = st.number_input("Expected MLS Sale Price", min_value=0, value=950000, step=10000)
        direct_offer_1 = st.number_input("Direct Offer #1", min_value=0, value=850000, step=10000)
        direct_offer_2 = st.number_input("Direct Offer #2", min_value=0, value=875000, step=10000)
        direct_offer_3 = st.number_input("Direct Offer #3", min_value=0, value=900000, step=10000)
    
    if analysis_type in ["Buyer/Flip Analysis", "Both"]:
        st.subheader("Buyer Scenario")
        purchase_price = st.number_input("Purchase Price", min_value=0, value=900000, step=10000)
        down_payment_pct = st.slider("Down Payment %", 5, 50, 10, 5)
        interest_rate = st.slider("Interest Rate %", 3.0, 10.0, 6.0, 0.25)
        remodel_cost = st.number_input("Remodel Cost", min_value=0, value=100000, step=5000)
        remodel_months = st.slider("Remodel Timeline (months)", 1, 12, 4)
        
        st.subheader("Sale Price Scenarios")
        sale_price_1 = st.number_input("Sale Price #1", min_value=0, value=1100000, step=10000)
        sale_price_2 = st.number_input("Sale Price #2", min_value=0, value=1120000, step=10000)
        sale_price_3 = st.number_input("Sale Price #3", min_value=0, value=1150000, step=10000)
    
    st.markdown("---")
    
    notes = st.text_area("Notes", placeholder="e.g., backs to mobile home park, needs foundation work, etc.")
    
    if st.button("💾 Save Property", type="primary"):
        property_data = {
            'name': property_name,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'sqft': sqft,
            'year_built': year_built,
            'notes': notes,
            'saved_date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        st.session_state.properties.append(property_data)
        st.success(f"✅ Saved {property_name}")

# Main Content Area
tab1, tab2, tab3 = st.tabs(["📊 Analysis", "📁 Saved Properties", "ℹ️ About"])

with tab1:
    if analysis_type in ["Seller Analysis", "Both"]:
        st.header("Seller Net Proceeds Analysis")
        st.markdown("**Comparison: Traditional MLS vs. Direct Sale**")
        
        # Calculate all scenarios
        mls_calc = calculate_seller_net(mls_price, is_mls=True)
        offer1_calc = calculate_seller_net(direct_offer_1, is_mls=False)
        offer2_calc = calculate_seller_net(direct_offer_2, is_mls=False)
        offer3_calc = calculate_seller_net(direct_offer_3, is_mls=False)
        
        # Create comparison table
        comparison_data = {
            'Cost Item': [
                'Gross Sale Price',
                'Listing Agent (3%)',
                'Buyer Agent',
                'Prep Costs',
                'Holding Costs (60 days)',
                'Transaction Costs',
                'TOTAL COSTS',
                'NET TO SELLER',
                'Difference vs MLS'
            ],
            f'MLS @ ${mls_price/1000:.0f}K': [
                f"${mls_calc['price']:,.0f}",
                f"-${mls_calc['listing_agent']:,.0f}",
                f"-${mls_calc['buyer_agent']:,.0f}",
                f"-${mls_calc['prep_costs']:,.0f}",
                f"-${mls_calc['holding_costs']:,.0f}",
                f"-${mls_calc['transaction_costs']:,.0f}",
                f"-${mls_calc['total_costs']:,.0f}",
                f"${mls_calc['net']:,.0f}",
                f"$0"
            ],
            f'Offer ${direct_offer_1/1000:.0f}K': [
                f"${offer1_calc['price']:,.0f}",
                f"-${offer1_calc['listing_agent']:,.0f}",
                f"$0 ✓",
                f"$0 ✓",
                f"$0 ✓",
                f"-${offer1_calc['transaction_costs']:,.0f}",
                f"-${offer1_calc['total_costs']:,.0f}",
                f"${offer1_calc['net']:,.0f}",
                f"${offer1_calc['net'] - mls_calc['net']:,.0f}"
            ],
            f'Offer ${direct_offer_2/1000:.0f}K': [
                f"${offer2_calc['price']:,.0f}",
                f"-${offer2_calc['listing_agent']:,.0f}",
                f"$0 ✓",
                f"$0 ✓",
                f"$0 ✓",
                f"-${offer2_calc['transaction_costs']:,.0f}",
                f"-${offer2_calc['total_costs']:,.0f}",
                f"${offer2_calc['net']:,.0f}",
                f"${offer2_calc['net'] - mls_calc['net']:,.0f}"
            ],
            f'Offer ${direct_offer_3/1000:.0f}K': [
                f"${offer3_calc['price']:,.0f}",
                f"-${offer3_calc['listing_agent']:,.0f}",
                f"$0 ✓",
                f"$0 ✓",
                f"$0 ✓",
                f"-${offer3_calc['transaction_costs']:,.0f}",
                f"-${offer3_calc['total_costs']:,.0f}",
                f"${offer3_calc['net']:,.0f}",
                f"${offer3_calc['net'] - mls_calc['net']:,.0f}"
            ]
        }
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
        
        # Key Insights
        st.markdown("### 💡 Key Insights")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            savings = mls_calc['buyer_agent'] + mls_calc['prep_costs'] + mls_calc['holding_costs']
            st.metric("Cost Savings (Direct Sale)", f"${savings:,.0f}")
        
        with col2:
            best_offer = max([offer1_calc['net'], offer2_calc['net'], offer3_calc['net']])
            diff = best_offer - mls_calc['net']
            st.metric("Best Offer Gap vs MLS", f"${diff:,.0f}", 
                     delta=f"{(diff/mls_calc['net']*100):.1f}%",
                     delta_color="inverse")
        
        with col3:
            timeline_diff = "60-90 days" if diff < -10000 else "21 days"
            st.metric("Timeline Advantage", timeline_diff, delta="Fast Close")
        
        st.markdown("---")
    
    if analysis_type in ["Buyer/Flip Analysis", "Both"]:
        st.header("Buyer/Flip Analysis")
        
        # Calculate buyer costs
        buy_costs = calculate_buyer_costs(purchase_price, down_payment_pct, interest_rate, remodel_cost, remodel_months)
        
        # Show acquisition costs
        st.subheader("📥 Acquisition & Investment")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Purchase Price", f"${purchase_price:,.0f}")
            st.metric("Down Payment", f"${buy_costs['down_payment']:,.0f}")
        with col2:
            st.metric("Loan Amount", f"${buy_costs['loan_amount']:,.0f}")
            st.metric("Cash to Acquire", f"${buy_costs['cash_to_acquire']:,.0f}")
        with col3:
            st.metric("Remodel Cost", f"${remodel_cost:,.0f}")
            st.metric("Total Cash Invested", f"${buy_costs['total_cash']:,.0f}")
        
        # Calculate profit scenarios
        st.subheader("💰 Profit Scenarios")
        
        profit1 = calculate_flip_profit(buy_costs, sale_price_1)
        profit2 = calculate_flip_profit(buy_costs, sale_price_2)
        profit3 = calculate_flip_profit(buy_costs, sale_price_3)
        
        profit_data = {
            'Sale Price': [f"${sale_price_1:,.0f}", f"${sale_price_2:,.0f}", f"${sale_price_3:,.0f}"],
            'Gross Proceeds': [f"${p['sell_price']:,.0f}" for p in [profit1, profit2, profit3]],
            'Commission (4%)': [f"-${p['commission']:,.0f}" for p in [profit1, profit2, profit3]],
            'Fees': [f"-${p['transfer_fees']:,.0f}" for p in [profit1, profit2, profit3]],
            'Loan Payoff': [f"-${buy_costs['loan_amount']:,.0f}"] * 3,
            'Net Proceeds': [f"${p['net_proceeds']:,.0f}" for p in [profit1, profit2, profit3]],
            'Cash Invested': [f"-${buy_costs['total_cash']:,.0f}"] * 3,
            'NET PROFIT': [f"${p['profit']:,.0f}" for p in [profit1, profit2, profit3]],
            'ROI': [f"{p['roi']:.1f}%" for p in [profit1, profit2, profit3]]
        }
        
        df_profit = pd.DataFrame(profit_data)
        st.dataframe(df_profit, use_container_width=True, hide_index=True)
        
        # ROI Chart
        st.subheader("📈 ROI Comparison")
        
        fig = go.Figure(data=[
            go.Bar(
                x=[f"${sale_price_1/1000:.0f}K", f"${sale_price_2/1000:.0f}K", f"${sale_price_3/1000:.0f}K"],
                y=[profit1['roi'], profit2['roi'], profit3['roi']],
                text=[f"{p['roi']:.1f}%" for p in [profit1, profit2, profit3]],
                textposition='auto',
                marker_color=['red' if p['roi'] < 0 else 'green' if p['roi'] > 15 else 'orange' 
                             for p in [profit1, profit2, profit3]]
            )
        ])
        
        fig.update_layout(
            title="ROI by Sale Price",
            xaxis_title="Sale Price",
            yaxis_title="ROI %",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Breakeven calculation
        total_all_in = buy_costs['total_cash'] + buy_costs['loan_amount']
        selling_percent = 0.04 + 0.0011 + (3000 / 1000000)
        breakeven_price = total_all_in / (1 - selling_percent)
        
        st.info(f"🎯 **Breakeven Sale Price:** ${breakeven_price:,.0f}")
        
        # Decision helper
        st.subheader("🎯 Deal Assessment")
        
        best_roi = max([profit1['roi'], profit2['roi'], profit3['roi']])
        best_profit = max([profit1['profit'], profit2['profit'], profit3['profit']])
        
        if best_roi < 0:
            st.error(f"⚠️ **WARNING:** All scenarios show negative returns. Highest ROI is {best_roi:.1f}%. Reconsider this deal.")
        elif best_roi < 10:
            st.warning(f"⚠️ **MARGINAL DEAL:** Best ROI is {best_roi:.1f}% with profit of ${best_profit:,.0f}. Risk vs. reward may not justify.")
        elif best_roi < 20:
            st.success(f"✓ **DECENT DEAL:** Best ROI is {best_roi:.1f}% with profit of ${best_profit:,.0f}. Reasonable margins.")
        else:
            st.success(f"🎉 **STRONG DEAL:** Best ROI is {best_roi:.1f}% with profit of ${best_profit:,.0f}. Excellent margins!")

with tab2:
    st.header("📁 Saved Properties")
    
    if len(st.session_state.properties) == 0:
        st.info("No properties saved yet. Use the sidebar to add properties.")
    else:
        for idx, prop in enumerate(st.session_state.properties):
            with st.expander(f"{prop['name']} - {prop['bedrooms']}bd/{prop['bathrooms']}ba, {prop['sqft']} sqft"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Year Built:** {prop['year_built']}")
                    st.write(f"**Saved:** {prop['saved_date']}")
                with col2:
                    st.write(f"**Size:** {prop['sqft']} sqft")
                    st.write(f"**Beds/Baths:** {prop['bedrooms']}/{prop['bathrooms']}")
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                        st.session_state.properties.pop(idx)
                        st.rerun()
                
                if prop.get('notes'):
                    st.markdown(f"**Notes:** {prop['notes']}")

with tab3:
    st.header("ℹ️ About This Tool")
    
    st.markdown("""
    ### Real Estate Deal Analyzer
    
    This tool helps you analyze real estate deals from both **seller** and **buyer/investor** perspectives.
    
    **Features:**
    - **Seller Analysis:** Compare net proceeds from traditional MLS listing vs. direct sale offers
    - **Buyer/Flip Analysis:** Calculate all-in costs, profit, and ROI for fix-and-flip deals
    - **Property Database:** Save and compare multiple properties
    - **Automated Calculations:** All the complex math done for you
    
    **Assumptions:**
    - Listing agent: 3%
    - Buyer agent (MLS): 2%
    - Selling commission (when you sell): 4% total
    - MLS prep costs: ~$25K (paint, staging, repairs, etc.)
    - Holding costs: Based on 2 months for MLS, instant for direct sale
    - Construction loan interest calculated monthly
    
    **How to Use:**
    1. Enter property details in the sidebar
    2. Choose your analysis type
    3. Adjust deal parameters
    4. Review the analysis in the main area
    5. Save properties you're tracking
    
    **Tips:**
    - Always account for location issues (mobile homes, busy roads, etc.) in your offers
    - Use conservative sale price estimates for flip scenarios
    - Factor in 10-20% buffer for unexpected remodel costs
    """)

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit • Real Estate Deal Analyzer v1.0*")