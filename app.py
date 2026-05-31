import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import pathlib

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
    h1,h2,h3 { color: #e6edf3; }
    .sidebar-title { font-size: 18px; font-weight: 700; color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1T6OtF_3RW3uTPpxU9wF0DX3ZjLmlVtJ8tJk7VklcWns"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

ALL_TABS = {
    "NSE Price Data":                "239886835",
    "NSE Fundamentals":              "1142746192",
    "Cumulative Average":            "1334726852",
    "Final List":                    "693874166",
    "Final List-2":                  "18233668",
    "52W Low-GTT":                   "1033601192",
    "+%":                            "271681223",
    "-%":                            "696834813",
    "-Diff @ 200 DMA":               "709383215",
    "+Diff @ 200 DMA":               "191089560",
    "Dashboard":                     "1566642815",
    "Calc_Data":                     "151957193",
    "Stock Deep Dive":               "1107023387",
    "Sector Analysis":               "10101010",
    "Custom Screener":               "88888888",
    "Fundamental Analysis":          "123456789",
    "Pro Watchlist":                 "847592847",
    "Market Summary":                "999999",
    "Smart Money Tracker":           "1014038501",
    "Financial Health":              "111111111",
    "Executive Summary":             "987123654",
    "Volume & Price Action":         "687046348",
    "Market Extremes":               "888111222",
    "Technical Crossovers":          "882766187",
    "Trading Signals & Alerts":      "1866530472",
    "Shareholding Analysis":         "888111333",
    "Elite Stock Screeners":         "984280430",
    "Sector Deep Dive":              "223456789",
    "Growth vs Value Playbook":      "555555555",
    "Market Cap Playbook":           "739281745",
    "All-Weather Portfolio":         "888222111",
    "Quality & Compounders":         "888123456",
    "Market Overview":               "1234567890",
    "Dividend & Income Playbook":    "12345678",
    "Smart Beta & Factor Investing": "1928374650",
    "Portfolio Tracker":             "987654321",
}

# ─── GOOGLE SHEETS CONNECTION ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    try:
        key_path = pathlib.Path(__file__).parent / "service_account.json"
        creds = Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=SCOPES,
            )
            client = gspread.authorize(creds)
            return client, None
        except Exception as e2:
            return None, str(e2)


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
        return pd.DataFrame(), f"Sheet '{tab_name}' not found."
    except Exception as e:
        return pd.DataFrame(), str(e)


def to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
            )
        except Exception:
            pass
    return df


def searchable_table(df: pd.DataFrame, key: str):
    q = st.text_input("🔍 Search / Filter:", key=f"s_{key}")
    if q:
        mask = df.apply(lambda c: c.astype(str).str.contains(q, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    st.dataframe(df, use_container_width=True, height=480)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">📈 NSE Dashboard</div>', unsafe_allow_html=True)
    st.caption("Google Sheets → Streamlit")
    st.divider()
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
    st.caption("Auto-refreshes every 5 min")


# ─── OVERVIEW ─────────────────────────────────────────────────────────────────
if group == "🏠 Overview":
    st.title("🏠 NSE Market Overview")
    st.caption("Live data pulled from your Google Sheet")

    with st.spinner("Loading NSE Price Data…"):
        df_price, err = load_sheet("NSE Price Data")

    if err:
        st.error(f"❌ Could not load data: {err}")
        st.stop()

    df_num = to_numeric(df_price)
    total = len(df_price)

    try:
        up   = int((df_num["% Change"] > 0).sum()) if "% Change" in df_num.columns else "—"
        down = int((df_num["% Change"] < 0).sum()) if "% Change" in df_num.columns else "—"
        avg  = round(float(df_num["% Change"].mean()), 2) if "% Change" in df_num.columns else "—"
        above200 = int((df_num["Output"] == 1).sum()) if "Output" in df_num.columns else "—"
    except Exception:
        up = down = avg = above200 = "—"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="metric-card"><div class="metric-val">{total}</div><div class="metric-lbl">Total Stocks</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-val positive">{up}</div><div class="metric-lbl">↑ Gainers</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-val negative">{down}</div><div class="metric-lbl">↓ Losers</div></div>', unsafe_allow_html=True)
    color = "positive" if isinstance(avg, float) and avg >= 0 else "negative"
    c4.markdown(f'<div class="metric-card"><div class="metric-val {color}">{avg}%</div><div class="metric-lbl">Avg % Change</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="metric-card"><div class="metric-val">{above200}</div><div class="metric-lbl">Above 200 DMA</div></div>', unsafe_allow_html=True)

    st.divider()
    cl, cr = st.columns(2)

    with cl:
        st.subheader("% Change Distribution")
        if "% Change" in df_num.columns:
            fig = px.histogram(df_num.dropna(subset=["% Change"]), x="% Change",
                               nbins=40, color_discrete_sequence=["#58a6ff"], template="plotly_dark")
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)

    with cr:
        st.subheader("Sector Breakdown")
        if "Sector" in df_price.columns:
            sec = df_price["Sector"].dropna().value_counts().head(15).reset_index()
            sec.columns = ["Sector", "Count"]
            fig2 = px.bar(sec, x="Count", y="Sector", orientation="h",
                          color="Count", color_continuous_scale="blues", template="plotly_dark")
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=10), coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Market Sentiment: Price vs 200 DMA")
    if "Output" in df_num.columns:
        above = int((df_num["Output"] == 1).sum())
        below = total - above
        fig3 = go.Figure(go.Pie(labels=["Above 200 DMA", "Below 200 DMA"],
                                values=[above, below], hole=0.45,
                                marker_colors=["#3fb950", "#f85149"]))
        fig3.update_layout(template="plotly_dark", height=320, margin=dict(t=20),
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)


# ─── PRICE & TECHNICALS ───────────────────────────────────────────────────────
elif group == "📊 Price & Technicals":
    TECH = ["NSE Price Data", "Cumulative Average", "+%", "-%",
            "-Diff @ 200 DMA", "+Diff @ 200 DMA",
            "Volume & Price Action", "Technical Crossovers",
            "Trading Signals & Alerts", "Market Extremes"]
    tabs = st.tabs(TECH)
    for i, name in enumerate(TECH):
        with tabs[i]:
            st.subheader(name)
            with st.spinner(f"Loading {name}…"):
                df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data in this sheet.")
            else:
                if name == "NSE Price Data":
                    dfn = to_numeric(df)
                    ca, cb = st.columns(2)
                    with ca:
                        if "% Change" in dfn.columns and "Symbol" in dfn.columns:
                            top = dfn.nlargest(10, "% Change")[["Symbol", "% Change"]].dropna()
                            fig = px.bar(top, x="Symbol", y="% Change", title="Top 10 Gainers",
                                         color_discrete_sequence=["#3fb950"], template="plotly_dark")
                            fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig, use_container_width=True)
                    with cb:
                        if "% Change" in dfn.columns and "Symbol" in dfn.columns:
                            bot = dfn.nsmallest(10, "% Change")[["Symbol", "% Change"]].dropna()
                            fig2 = px.bar(bot, x="Symbol", y="% Change", title="Top 10 Losers",
                                          color_discrete_sequence=["#f85149"], template="plotly_dark")
                            fig2.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig2, use_container_width=True)
                searchable_table(df, name)


# ─── SCREENERS & LISTS ────────────────────────────────────────────────────────
elif group == "📋 Screeners & Lists":
    SCREEN = ["Final List", "Final List-2", "52W Low-GTT",
              "Elite Stock Screeners", "Custom Screener", "Pro Watchlist",
              "Market Overview", "Market Summary", "Smart Money Tracker",
              "Market Cap Playbook", "Growth vs Value Playbook",
              "All-Weather Portfolio", "Quality & Compounders",
              "Dividend & Income Playbook", "Smart Beta & Factor Investing"]
    tabs = st.tabs(SCREEN)
    for i, name in enumerate(SCREEN):
        with tabs[i]:
            st.subheader(name)
            with st.spinner(f"Loading {name}…"):
                df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data in this sheet.")
            else:
                if name in ("Final List", "Final List-2"):
                    dfn = to_numeric(df)
                    ca, cb = st.columns(2)
                    with ca:
                        if "Market Cap (Cr)" in dfn.columns and "Sector" in df.columns:
                            mc = dfn.dropna(subset=["Market Cap (Cr)", "Sector"])
                            mc_grp = mc.groupby("Sector")["Market Cap (Cr)"].sum().reset_index().sort_values("Market Cap (Cr)", ascending=False).head(10)
                            fig = px.pie(mc_grp, values="Market Cap (Cr)", names="Sector",
                                         title="Market Cap by Sector", hole=0.35, template="plotly_dark")
                            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig, use_container_width=True)
                    with cb:
                        if "PE Ratio" in dfn.columns:
                            pe = dfn["PE Ratio"].dropna()
                            pe = pe[(pe > 0) & (pe < 200)]
                            fig2 = px.histogram(pe, nbins=30, title="PE Ratio Distribution",
                                                color_discrete_sequence=["#d2a8ff"], template="plotly_dark")
                            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                            st.plotly_chart(fig2, use_container_width=True)
                searchable_table(df, name)


# ─── FUNDAMENTALS ─────────────────────────────────────────────────────────────
elif group == "🏭 Fundamentals":
    FUND = ["NSE Fundamentals", "Fundamental Analysis",
            "Sector Analysis", "Sector Deep Dive",
            "Financial Health", "Executive Summary",
            "Shareholding Analysis", "Stock Deep Dive", "Portfolio Tracker"]
    tabs = st.tabs(FUND)
    for i, name in enumerate(FUND):
        with tabs[i]:
            st.subheader(name)
            with st.spinner(f"Loading {name}…"):
                df, err = load_sheet(name)
            if err:
                st.warning(f"⚠️ {err}")
            elif df.empty:
                st.info("No data in this sheet.")
            else:
                if name == "NSE Fundamentals":
                    dfn = to_numeric(df)
                    cols3 = st.columns(3)
                    for j, (col_name, title, color) in enumerate([
                        ("PE Ratio", "PE Ratio", "#79c0ff"),
                        ("RONW%",    "RONW %",   "#3fb950"),
                        ("D/E Ratio","D/E Ratio", "#f85149"),
                    ]):
                        with cols3[j]:
                            if col_name in dfn.columns:
                                d = dfn[col_name].dropna()
                                d = d[(d > d.quantile(0.01)) & (d < d.quantile(0.99))]
                                fig = px.histogram(d, nbins=25, title=title,
                                                   color_discrete_sequence=[color],
                                                   template="plotly_dark")
                                fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                                  plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=30))
                                st.plotly_chart(fig, use_container_width=True)

                    if all(c in dfn.columns for c in ["Promoter%", "FII%", "DII%"]):
                        avg_h = {
                            "Promoter": dfn["Promoter%"].dropna().mean(),
                            "FII":      dfn["FII%"].dropna().mean(),
                            "DII":      dfn["DII%"].dropna().mean(),
                            "Public":   dfn["Public%"].dropna().mean() if "Public%" in dfn.columns else 0,
                        }
                        fig4 = go.Figure(go.Bar(x=list(avg_h.keys()), y=list(avg_h.values()),
                                                marker_color=["#58a6ff","#3fb950","#d2a8ff","#f0883e"]))
                        fig4.update_layout(title="Avg Shareholding Pattern (%)", template="plotly_dark",
                                           height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig4, use_container_width=True)
                searchable_table(df, name)


# ─── ALL OTHER TABS ───────────────────────────────────────────────────────────
elif group == "🗂️ All Other Tabs":
    st.title("🗂️ All Sheets Raw View")
    tab_name = st.selectbox("Choose a sheet:", list(ALL_TABS.keys()))

    with st.spinner(f"Loading '{tab_name}'…"):
        df, err = load_sheet(tab_name)

    if err:
        st.error(f"❌ {err}")
    elif df.empty:
        st.info("No data or sheet not found.")
        st.markdown(f"[Open in Google Sheets ↗](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={ALL_TABS[tab_name]})")
    else:
        col_i, col_l = st.columns([3, 1])
        col_i.success(f"✅ {len(df):,} rows × {len(df.columns)} columns")
        col_l.markdown(f"[📄 Open in Sheets ↗](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={ALL_TABS[tab_name]})")

        dfn = to_numeric(df)
        num_cols = dfn.select_dtypes(include="number").columns.tolist()
        if num_cols:
            with st.expander("📊 Quick Chart", expanded=False):
                cx, cy = st.columns(2)
                x_col = cx.selectbox("X axis", df.columns.tolist(), key="qx")
                y_col = cy.selectbox("Y axis", num_cols, key="qy")
                chart_type = st.radio("Chart type", ["Bar","Line","Scatter","Histogram"], horizontal=True)
                plot_df = dfn[[x_col, y_col]].dropna().head(100)
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

        searchable_table(df, tab_name)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("NSE Dashboard · Streamlit + Google Sheets · Auto-refresh every 5 min")
