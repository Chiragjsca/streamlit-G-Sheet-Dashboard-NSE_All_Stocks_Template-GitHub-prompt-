import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="NSE Stock Dashboard", page_icon="📈", layout="wide")

# Dark theme CSS (same as before)
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c2333;
        border-radius: 6px;
        color: #c9d1d9;
        padding: 6px 14px;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0366d6 !important;
        color: white !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #1c2333, #21262d);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-val { font-size: 24px; font-weight: 700; color: #58a6ff; }
    .metric-lbl { font-size: 12px; color: #8b949e; }
    .positive { color: #3fb950 !important; }
    .negative { color: #f85149 !important; }
</style>
""", unsafe_allow_html=True)

SPREADSHEET_ID = "1T6OtF_3RW3uTPpxU9wF0DX3ZjLmlVtJ8tJk7VklcWns"

ALL_TABS = {
    "NSE Price Data": "239886835",
    "NSE Fundamentals": "1142746192",
    "Cumulative Average": "1334726852",
    "Final List": "693874166",
    "Final List-2": "18233668",
    "52W Low-GTT": "1033601192",
    "+%": "271681223",
    "-%": "696834813",
    "-Diff @ 200 DMA": "709383215",
    "+Diff @ 200 DMA": "191089560",
    "Dashboard": "1566642815",
    "Calc_Data": "151957193",
    "Stock Deep Dive": "1107023387",
    "Sector Analysis": "10101010",
    "Custom Screener": "88888888",
    "Fundamental Analysis": "123456789",
    "Pro Watchlist": "847592847",
    "Market Summary": "999999",
    "Smart Money Tracker": "1014038501",
    "Financial Health": "111111111",
    "Executive Summary": "987123654",
    "Volume & Price Action": "687046348",
    "Market Extremes": "888111222",
    "Technical Crossovers": "882766187",
    "Trading Signals & Alerts": "1866530472",
    "Shareholding Analysis": "888111333",
    "Elite Stock Screeners": "984280430",
    "Sector Deep Dive": "223456789",
    "Growth vs Value Playbook": "555555555",
    "Market Cap Playbook": "739281745",
    "All-Weather Portfolio": "888222111",
    "Quality & Compounders": "888123456",
    "Market Overview": "1234567890",
    "Dividend & Income Playbook": "12345678",
    "Smart Beta & Factor Investing": "1928374650",
    "Portfolio Tracker": "987654321",
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

@st.cache_resource(show_spinner=False)
def get_gspread_client():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Fix escaped newlines if any
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        # Test connection
        client.open_by_key(SPREADSHEET_ID)
        return client, None
    except Exception as e:
        return None, f"Auth error: {str(e)}"

@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(tab_name: str):
    client, err = get_gspread_client()
    if err:
        return pd.DataFrame(), err
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(tab_name)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame(), None
        df = pd.DataFrame(data[1:], columns=data[0])
        df.replace("", pd.NA, inplace=True)
        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df, None
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame(), f"Sheet '{tab_name}' not found"
    except Exception as e:
        return pd.DataFrame(), str(e)

def to_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip())
        except:
            pass
    return df

def show_searchable_table(df: pd.DataFrame, key: str):
    search = st.text_input("🔍 Search / Filter", key=f"search_{key}")
    if search:
        mask = df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    st.dataframe(df, use_container_width=True, height=480)

with st.sidebar:
    st.markdown("### 📈 NSE Dashboard")
    st.caption("Google Sheets → Streamlit")
    st.divider()
    group = st.radio("Section", [
        "🏠 Overview",
        "📊 Price & Technicals",
        "📋 Screeners & Lists",
        "🏭 Fundamentals",
        "🗂️ All Other Tabs",
    ])
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()

if group == "🏠 Overview":
    st.title("🏠 NSE Market Overview")
    df_price, err = load_sheet("NSE Price Data")
    if err:
        st.error(f"❌ Could not load data: {err}")
        st.stop()
    df_num = to_numeric_cols(df_price.copy())
    total = len(df_price)
    up = int((df_num["% Change"] > 0).sum()) if "% Change" in df_num else "—"
    down = int((df_num["% Change"] < 0).sum()) if "% Change" in df_num else "—"
    avg_chg = round(df_num["% Change"].mean(), 2) if "% Change" in df_num else "—"
    above_200 = int((df_num["Output"] == 1).sum()) if "Output" in df_num else "—"
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="metric-val">{total}</div><div class="metric-lbl">Total Stocks</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-val positive">{up}</div><div class="metric-lbl">↑ Gainers</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-val negative">{down}</div><div class="metric-lbl">↓ Losers</div></div>', unsafe_allow_html=True)
    color = "positive" if isinstance(avg_chg, float) and avg_chg >= 0 else "negative"
    c4.markdown(f'<div class="metric-card"><div class="metric-val {color}">{avg_chg}%</div><div class="metric-lbl">Avg % Change</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-val">{above_200}</div><div class="metric-lbl">Above 200 DMA</div></div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        if "% Change" in df_num:
            fig = px.histogram(df_num.dropna(subset=["% Change"]), x="% Change", nbins=40, color_discrete_sequence=["#58a6ff"], template="plotly_dark")
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with col_r:
        if "Sector" in df_price:
            sec = df_price["Sector"].dropna().value_counts().head(15).reset_index()
            sec.columns = ["Sector", "Count"]
            fig2 = px.bar(sec, x="Count", y="Sector", orientation="h", color="Count", color_continuous_scale="blues", template="plotly_dark")
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

elif group == "📊 Price & Technicals":
    tech_tabs = ["NSE Price Data", "Cumulative Average", "+%", "-%", "-Diff @ 200 DMA", "+Diff @ 200 DMA", "Volume & Price Action", "Technical Crossovers", "Trading Signals & Alerts", "Market Extremes"]
    tabs = st.tabs(tech_tabs)
    for i, name in enumerate(tech_tabs):
        with tabs[i]:
            st.subheader(name)
            df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found")
            else:
                show_searchable_table(df, name)

elif group == "📋 Screeners & Lists":
    screen_tabs = ["Final List", "Final List-2", "52W Low-GTT", "Elite Stock Screeners", "Custom Screener", "Pro Watchlist", "Market Overview", "Market Summary", "Smart Money Tracker", "Market Cap Playbook", "Growth vs Value Playbook", "All-Weather Portfolio", "Quality & Compounders", "Dividend & Income Playbook", "Smart Beta & Factor Investing"]
    tabs = st.tabs(screen_tabs)
    for i, name in enumerate(screen_tabs):
        with tabs[i]:
            st.subheader(name)
            df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found")
            else:
                show_searchable_table(df, name)

elif group == "🏭 Fundamentals":
    fund_tabs = ["NSE Fundamentals", "Fundamental Analysis", "Sector Analysis", "Sector Deep Dive", "Financial Health", "Executive Summary", "Shareholding Analysis", "Stock Deep Dive", "Portfolio Tracker"]
    tabs = st.tabs(fund_tabs)
    for i, name in enumerate(fund_tabs):
        with tabs[i]:
            st.subheader(name)
            df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found")
            else:
                show_searchable_table(df, name)

else:
    st.title("🗂️ All Sheets")
    tab_name = st.selectbox("Choose a sheet:", list(ALL_TABS.keys()))
    df, err = load_sheet(tab_name)
    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("No data found")
    else:
        st.success(f"Loaded {len(df)} rows")
        show_searchable_table(df, tab_name)

st.markdown("---")
st.caption("NSE Dashboard · Powered by Streamlit + Google Sheets")
