import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import json

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NSE Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
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
        font-weight: 500;
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
    .metric-lbl { font-size: 12px; color: #8b949e; margin-top: 4px; }
    .positive { color: #3fb950 !important; }
    .negative { color: #f85149 !important; }
    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    .stSelectbox label, .stMultiSelect label { color: #c9d1d9; }
    h1,h2,h3 { color: #e6edf3; }
    .sidebar-title { font-size: 18px; font-weight: 700; color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ─── SPREADSHEET CONFIG ────────────────────────────────────────────────────────
SPREADSHEET_ID = "1T6OtF_3RW3uTPpxU9wF0DX3ZjLmlVtJ8tJk7VklcWns"

# All tabs with their gid mapping
ALL_TABS = {
    "NSE Price Data":           "239886835",
    "NSE Fundamentals":         "1142746192",
    "Cumulative Average":       "1334726852",
    "Final List":               "693874166",
    "Final List-2":             "18233668",
    "52W Low-GTT":              "1033601192",
    "+%":                       "271681223",
    "-%":                       "696834813",
    "-Diff @ 200 DMA":          "709383215",
    "+Diff @ 200 DMA":          "191089560",
    "Dashboard":                "1566642815",
    "Calc_Data":                "151957193",
    "Stock Deep Dive":          "1107023387",
    "Sector Analysis":          "10101010",
    "Custom Screener":          "88888888",
    "Fundamental Analysis":     "123456789",
    "Pro Watchlist":            "847592847",
    "Market Summary":           "999999",
    "Smart Money Tracker":      "1014038501",
    "Financial Health":         "111111111",
    "Executive Summary":        "987123654",
    "Volume & Price Action":    "687046348",
    "Market Extremes":          "888111222",
    "Technical Crossovers":     "882766187",
    "Trading Signals & Alerts": "1866530472",
    "Shareholding Analysis":    "888111333",
    "Elite Stock Screeners":    "984280430",
    "Sector Deep Dive":         "223456789",
    "Growth vs Value Playbook": "555555555",
    "Market Cap Playbook":      "739281745",
    "All-Weather Portfolio":    "888222111",
    "Quality & Compounders":    "888123456",
    "Market Overview":          "1234567890",
    "Dividend & Income Playbook": "12345678",
    "Smart Beta & Factor Investing": "1928374650",
    "Portfolio Tracker":        "987654321",
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# ─── GOOGLE SHEETS CONNECTION ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    """Build gspread client from st.secrets."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # gspread needs 'private_key' with real newlines
        if "\\n" in creds_dict.get("private_key", ""):
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(tab_name: str) -> pd.DataFrame:
    """Load a single worksheet into a DataFrame."""
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
        # Drop fully empty rows / columns
        df.replace("", pd.NA, inplace=True)
        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df, None
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame(), f"Worksheet '{tab_name}' not found in the spreadsheet."
    except gspread.exceptions.APIError as e:
        return pd.DataFrame(), f"Google API error: {e}"
    except Exception as e:
        return pd.DataFrame(), str(e)


def to_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Try converting each column to numeric where possible."""
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip())
        except Exception:
            pass
    return df


# ─── HELPER: SHOW DATAFRAME WITH SEARCH ───────────────────────────────────────
def show_searchable_table(df: pd.DataFrame, key: str):
    search = st.text_input("🔍 Search / Filter (any column):", key=f"search_{key}")
    if search:
        mask = df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    st.dataframe(df, use_container_width=True, height=480)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📈 NSE Dashboard</div>', unsafe_allow_html=True)
    st.caption("Google Sheets → Streamlit")
    st.divider()
    st.markdown("**Navigation**")
    group = st.radio("Section", [
        "🏠 Overview",
        "📊 Price & Technicals",
        "📋 Screeners & Lists",
        "🏭 Fundamentals",
        "🗂️ All Other Tabs",
    ], label_visibility="collapsed")
    st.divider()
    if st.button("🔄 Refresh All Data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data auto-refreshes every 5 min")

# ─── SECTION: OVERVIEW ────────────────────────────────────────────────────────
if group == "🏠 Overview":
    st.title("🏠 NSE Market Overview")
    st.caption("Live data pulled from your Google Sheet")

    with st.spinner("Loading NSE Price Data…"):
        df_price, err = load_sheet("NSE Price Data")

    if err:
        st.error(f"❌ Could not load data: {err}")
        st.stop()

    df_num = to_numeric_cols(df_price.copy())

    # KPI row
    col1, col2, col3, col4, col5 = st.columns(5)
    total_stocks = len(df_price)

    try:
        up = int((df_num["% Change"] > 0).sum()) if "% Change" in df_num.columns else "—"
        down = int((df_num["% Change"] < 0).sum()) if "% Change" in df_num.columns else "—"
        avg_chg = round(df_num["% Change"].mean(), 2) if "% Change" in df_num.columns else "—"
        above_200 = int((df_num["Output"] == 1).sum()) if "Output" in df_num.columns else "—"
    except Exception:
        up = down = avg_chg = above_200 = "—"

    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{total_stocks}</div><div class="metric-lbl">Total Stocks</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-val positive">{up}</div><div class="metric-lbl">↑ Gainers</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-val negative">{down}</div><div class="metric-lbl">↓ Losers</div></div>', unsafe_allow_html=True)
    with col4:
        color = "positive" if isinstance(avg_chg, float) and avg_chg >= 0 else "negative"
        st.markdown(f'<div class="metric-card"><div class="metric-val {color}">{avg_chg}%</div><div class="metric-lbl">Avg % Change</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{above_200}</div><div class="metric-lbl">Above 200 DMA</div></div>', unsafe_allow_html=True)

    st.divider()

    col_l, col_r = st.columns(2)

    # % Change distribution
    with col_l:
        st.subheader("% Change Distribution")
        if "% Change" in df_num.columns:
            fig = px.histogram(
                df_num.dropna(subset=["% Change"]),
                x="% Change", nbins=40,
                color_discrete_sequence=["#58a6ff"],
                template="plotly_dark",
            )
            fig.update_layout(margin=dict(t=20, b=20), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    # Sector breakdown
    with col_r:
        st.subheader("Sector Breakdown")
        if "Sector" in df_price.columns:
            sec = df_price["Sector"].dropna().value_counts().head(15).reset_index()
            sec.columns = ["Sector", "Count"]
            fig2 = px.bar(sec, x="Count", y="Sector", orientation="h",
                          color="Count", color_continuous_scale="blues",
                          template="plotly_dark")
            fig2.update_layout(margin=dict(t=20, b=20), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

    # 200 DMA Sentiment Pie
    st.subheader("Market Sentiment: Price vs 200 DMA")
    if "Output" in df_num.columns:
        above = int((df_num["Output"] == 1).sum())
        below = total_stocks - above
        fig3 = go.Figure(data=[go.Pie(
            labels=["Above 200 DMA", "Below 200 DMA"],
            values=[above, below],
            hole=0.45,
            marker_colors=["#3fb950", "#f85149"],
        )])
        fig3.update_layout(template="plotly_dark", height=320, margin=dict(t=20),
                           paper_bgcolor="rgba(0,0,0,0)", showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)


# ─── SECTION: PRICE & TECHNICALS ──────────────────────────────────────────────
elif group == "📊 Price & Technicals":
    TECH_TABS = [
        "NSE Price Data", "Cumulative Average", "+%", "-%",
        "-Diff @ 200 DMA", "+Diff @ 200 DMA",
        "Volume & Price Action", "Technical Crossovers",
        "Trading Signals & Alerts", "Market Extremes",
    ]
    tabs = st.tabs(TECH_TABS)

    for i, tab_name in enumerate(TECH_TABS):
        with tabs[i]:
            st.subheader(tab_name)
            with st.spinner(f"Loading {tab_name}…"):
                df, err = load_sheet(tab_name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found in this sheet.")
            else:
                # Special chart for NSE Price Data
                if tab_name == "NSE Price Data":
                    df_num = to_numeric_cols(df.copy())
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if "% Change" in df_num.columns and "Symbol" in df_num.columns:
                            top10 = df_num.nlargest(10, "% Change")[["Symbol", "% Change"]].dropna()
                            fig = px.bar(top10, x="Symbol", y="% Change", title="Top 10 Gainers",
                                         color="% Change", color_continuous_scale="greens",
                                         template="plotly_dark")
                            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig, use_container_width=True)
                    with col_b:
                        if "% Change" in df_num.columns and "Symbol" in df_num.columns:
                            bot10 = df_num.nsmallest(10, "% Change")[["Symbol", "% Change"]].dropna()
                            fig2 = px.bar(bot10, x="Symbol", y="% Change", title="Top 10 Losers",
                                          color="% Change", color_continuous_scale="reds_r",
                                          template="plotly_dark")
                            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig2, use_container_width=True)

                    # DMA Scatter
                    if all(c in df_num.columns for c in ["200 DMA", "Close (₹)", "Symbol"]):
                        df_s = df_num.dropna(subset=["200 DMA", "Close (₹)"]).head(100)
                        fig3 = px.scatter(df_s, x="200 DMA", y="Close (₹)", text="Symbol",
                                          title="CMP vs 200 DMA (first 100 stocks)",
                                          template="plotly_dark",
                                          color_discrete_sequence=["#58a6ff"])
                        fig3.update_traces(textposition="top center", marker=dict(size=6))
                        fig3.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig3, use_container_width=True)

                show_searchable_table(df, tab_name)


# ─── SECTION: SCREENERS & LISTS ───────────────────────────────────────────────
elif group == "📋 Screeners & Lists":
    SCREEN_TABS = [
        "Final List", "Final List-2", "52W Low-GTT",
        "Elite Stock Screeners", "Custom Screener", "Pro Watchlist",
        "Market Overview", "Market Summary", "Smart Money Tracker",
        "Market Cap Playbook", "Growth vs Value Playbook",
        "All-Weather Portfolio", "Quality & Compounders",
        "Dividend & Income Playbook", "Smart Beta & Factor Investing",
    ]
    tabs = st.tabs(SCREEN_TABS)

    for i, tab_name in enumerate(SCREEN_TABS):
        with tabs[i]:
            st.subheader(tab_name)
            with st.spinner(f"Loading {tab_name}…"):
                df, err = load_sheet(tab_name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found in this sheet.")
            else:
                # For Final List, add mini charts
                if tab_name in ("Final List", "Final List-2"):
                    df_num = to_numeric_cols(df.copy())
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if "Market Cap (Cr)" in df_num.columns and "Sector" in df.columns:
                            mc = df_num.dropna(subset=["Market Cap (Cr)", "Sector"])
                            mc_grp = mc.groupby("Sector")["Market Cap (Cr)"].sum().reset_index().sort_values("Market Cap (Cr)", ascending=False).head(10)
                            fig = px.pie(mc_grp, values="Market Cap (Cr)", names="Sector",
                                         title="Market Cap by Sector", hole=0.35,
                                         template="plotly_dark")
                            fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig, use_container_width=True)
                    with col_b:
                        if "PE Ratio" in df_num.columns:
                            pe_data = df_num["PE Ratio"].dropna()
                            pe_data = pe_data[(pe_data > 0) & (pe_data < 200)]
                            fig2 = px.histogram(pe_data, nbins=30, title="PE Ratio Distribution",
                                                color_discrete_sequence=["#d2a8ff"],
                                                template="plotly_dark")
                            fig2.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig2, use_container_width=True)

                show_searchable_table(df, tab_name)


# ─── SECTION: FUNDAMENTALS ────────────────────────────────────────────────────
elif group == "🏭 Fundamentals":
    FUND_TABS = [
        "NSE Fundamentals", "Fundamental Analysis",
        "Sector Analysis", "Sector Deep Dive",
        "Financial Health", "Executive Summary",
        "Shareholding Analysis", "Stock Deep Dive",
        "Portfolio Tracker",
    ]
    tabs = st.tabs(FUND_TABS)

    for i, tab_name in enumerate(FUND_TABS):
        with tabs[i]:
            st.subheader(tab_name)
            with st.spinner(f"Loading {tab_name}…"):
                df, err = load_sheet(tab_name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data found in this sheet.")
            else:
                if tab_name == "NSE Fundamentals":
                    df_num = to_numeric_cols(df.copy())
                    charts_row = st.columns(3)

                    metrics_plots = [
                        ("PE Ratio", "PE Ratio Distribution", "#79c0ff"),
                        ("RONW%", "Return on Net Worth %", "#3fb950"),
                        ("D/E Ratio", "Debt-to-Equity Distribution", "#f85149"),
                    ]
                    for j, (col_name, title, color) in enumerate(metrics_plots):
                        with charts_row[j]:
                            if col_name in df_num.columns:
                                d = df_num[col_name].dropna()
                                d = d[(d > d.quantile(0.01)) & (d < d.quantile(0.99))]
                                fig = px.histogram(d, nbins=25, title=title,
                                                   color_discrete_sequence=[color],
                                                   template="plotly_dark")
                                fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=30))
                                st.plotly_chart(fig, use_container_width=True)

                    # Promoter vs FII vs DII
                    if all(c in df_num.columns for c in ["Promoter%", "FII%", "DII%"]):
                        avg_hold = {
                            "Promoter": df_num["Promoter%"].dropna().mean(),
                            "FII": df_num["FII%"].dropna().mean(),
                            "DII": df_num["DII%"].dropna().mean(),
                            "Public": df_num["Public%"].dropna().mean() if "Public%" in df_num.columns else 0,
                        }
                        fig4 = go.Figure(data=[go.Bar(
                            x=list(avg_hold.keys()), y=list(avg_hold.values()),
                            marker_color=["#58a6ff", "#3fb950", "#d2a8ff", "#f0883e"],
                        )])
                        fig4.update_layout(title="Avg Shareholding Pattern (%)", template="plotly_dark",
                                           height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig4, use_container_width=True)

                show_searchable_table(df, tab_name)


# ─── SECTION: ALL OTHER TABS ──────────────────────────────────────────────────
elif group == "🗂️ All Other Tabs":
    st.title("🗂️ All Sheets Raw View")
    st.caption("Browse every sheet from your Google Spreadsheet")

    tab_name = st.selectbox("Choose a sheet:", list(ALL_TABS.keys()))

    with st.spinner(f"Loading '{tab_name}'…"):
        df, err = load_sheet(tab_name)

    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("This sheet has no data or could not be found.")
        st.markdown(f"[Open in Google Sheets ↗](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={ALL_TABS[tab_name]})")
    else:
        col_info, col_link = st.columns([3, 1])
        with col_info:
            st.success(f"✅ Loaded: {len(df):,} rows × {len(df.columns)} columns")
        with col_link:
            st.markdown(f"[📄 Open in Sheets ↗](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={ALL_TABS[tab_name]})")

        # Auto numeric charts if sensible columns found
        df_num = to_numeric_cols(df.copy())
        num_cols = df_num.select_dtypes(include="number").columns.tolist()

        if num_cols:
            with st.expander("📊 Quick Chart", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    x_col = st.selectbox("X axis", df.columns.tolist(), key="qx")
                with c2:
                    y_col = st.selectbox("Y axis", num_cols, key="qy")
                chart_type = st.radio("Chart type", ["Bar", "Line", "Scatter", "Histogram"], horizontal=True)
                plot_df = df_num[[x_col, y_col]].dropna().head(100)
                if not plot_df.empty:
                    if chart_type == "Bar":
                        fig = px.bar(plot_df, x=x_col, y=y_col, template="plotly_dark",
                                     color_discrete_sequence=["#58a6ff"])
                    elif chart_type == "Line":
                        fig = px.line(plot_df, x=x_col, y=y_col, template="plotly_dark")
                    elif chart_type == "Scatter":
                        fig = px.scatter(plot_df, x=x_col, y=y_col, template="plotly_dark",
                                         color_discrete_sequence=["#58a6ff"])
                    else:
                        fig = px.histogram(plot_df, x=y_col, template="plotly_dark",
                                           color_discrete_sequence=["#58a6ff"])
                    fig.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

        show_searchable_table(df, tab_name)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("NSE Dashboard · Powered by Streamlit + Google Sheets · Auto-refresh every 5 min")
