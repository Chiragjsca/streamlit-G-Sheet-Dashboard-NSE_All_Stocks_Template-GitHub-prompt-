import streamlit as st
import gspread
import pandas as pd

# Set page configuration to wide for a dashboard layout
st.set_page_config(layout="wide", page_title="Google Sheets Dashboard")
st.title("📊 Google Sheets Multi-Tab Dashboard")

# 1. Authenticate using Streamlit secrets
try:
    credentials = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(credentials)
except Exception as e:
    st.error("Missing or incorrect credentials secrets.")
    st.stop()

# 2. Open the Google Sheet using its Unique ID
# Replace this string with your actual Sheet ID found in your Google Sheet URL
SPREADSHEET_ID = "1T6OtF_3RW3uTPpxU9wF0DX3ZjLmlVtJ8tJk7VklcWns" 

@st.cache_data(ttl=600)  # Caches data for 10 minutes to avoid hitting API limits
def load_all_tabs(sheet_id):
    spreadsheet = gc.open_by_key(sheet_id)
    worksheets = spreadsheet.worksheets() # Fetches all tabs
    
    # Store dataframes in a dictionary: { "Tab Name": Dataframe }
    all_data = {}
    for sheet in worksheets:
        records = sheet.get_all_records()
        if records:
            all_data[sheet.title] = pd.DataFrame(records)
        else:
            # Fallback if tab is empty or only has headers
            all_data[sheet.title] = pd.DataFrame()
    return all_data

# Load the data
with st.spinner("Fetching data from Google Sheets..."):
    tabs_dict = load_all_tabs(SPREADSHEET_ID)

if tabs_dict:
    # 3. Dynamically create Streamlit tabs based on Google Sheet tabs
    tab_names = list(tabs_dict.keys())
    st_tabs = st.tabs(tab_names)
    
    # 4. Render content inside each tab
    for i, tab_name in enumerate(tab_names):
        with st_tabs[i]:
            st.subheader(f"Data Overview: {tab_name}")
            df = tabs_dict[tab_name]
            
            if df.empty:
                st.warning("This tab is empty.")
            else:
                # Display data table
                st.dataframe(df, use_container_width=True)
                
                # Example metric card or dashboard breakdown
                st.metric(label="Total Rows", value=len(df))
                
                # Quick data visualization helper
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if len(numeric_cols) >= 1:
                    st.markdown("### 📈 Quick Visualizations")
                    selected_col = st.selectbox(f"Select column to view distribution ({tab_name})", numeric_cols, key=f"select_{tab_name}")
                    st.bar_chart(df[selected_col])
else:
    st.info("No tabs found in the specified Google Sheet.")
