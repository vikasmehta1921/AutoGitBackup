"""
pages/2_History.py — Backup History
======================================
Full backup history with:
  - Search / filter by status and date range
  - Plotly bar chart of daily backup activity
  - CSV export
  - Error details expansion
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_backup_dataframe, get_stats

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Backup History — AutoGitBackup",
    page_icon="📋",
    layout="wide",
)

# ── Shared CSS (must be included on every page) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d1b2a 0%,#1a2744 100%); border-right:1px solid #243354; }
section[data-testid="stSidebar"] * { color: #c8d6f0 !important; }
.badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:0.78rem; font-weight:600; letter-spacing:0.05em; }
.badge-success { background:#1a3a1f; color:#4caf50; border:1px solid #2e6b33; }
.badge-failed  { background:#3a1a1a; color:#f44336; border:1px solid #6b2e2e; }
.badge-warn    { background:#3a2e1a; color:#ff9800; border:1px solid #6b521a; }
.badge-info    { background:#1a2a3a; color:#4f8ef7; border:1px solid #2e4a6b; }
.info-box { background:linear-gradient(135deg,#141e30,#1c2d4a); border:1px solid #2a3f63; border-left:4px solid #4f8ef7; border-radius:8px; padding:16px 20px; margin:10px 0; }
h1 { color:#e8f0fe !important; font-weight:700 !important; }
h2 { color:#c8d6f0 !important; font-weight:600 !important; }
div[data-testid="metric-container"] { background:linear-gradient(135deg,#141e30,#1c2d4a); border:1px solid #2a3f63; border-radius:12px; padding:18px 22px; }
div[data-testid="metric-container"] label { color:#8aabdd !important; font-size:0.8rem !important; font-weight:500 !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color:#e8f0fe !important; font-size:2rem !important; font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📋 Backup History")
st.markdown("*View, search, and export all backup records.*")
st.divider()

# ── Load Data ─────────────────────────────────────────────────────────────────
df = get_backup_dataframe()

if df.empty:
    st.info("No backup records found yet. Run your first backup to see history here.")
    st.stop()

# ── Summary KPIs ─────────────────────────────────────────────────────────────
stats = get_stats()
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Runs", stats["total_backups"])
with c2:
    st.metric("✅ Successful", stats["successful"])
with c3:
    st.metric("❌ Failed", stats["failed"])
with c4:
    st.metric("🎯 Success Rate", f"{stats['success_rate']}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
with st.expander("📊 Backup Activity Charts", expanded=True):
    chart_df = df.copy()
    chart_df["date"] = chart_df["backup_datetime"].dt.date

    tab1, tab2 = st.tabs(["Daily Activity", "Status Distribution"])

    with tab1:
        daily = (
            chart_df.groupby(["date", "status"])
            .size()
            .reset_index(name="count")
        )
        color_map = {"success": "#4caf50", "failed": "#f44336", "no_changes": "#4f8ef7"}
        fig = px.bar(
            daily, x="date", y="count", color="status",
            color_discrete_map=color_map,
            title="Backups Per Day",
            labels={"date": "Date", "count": "Count", "status": "Status"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8d6f0"),
            title_font=dict(color="#e8f0fe"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="#1c2d4a"),
            yaxis=dict(gridcolor="#1c2d4a"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        status_counts = df["status"].value_counts()
        fig2 = go.Figure(go.Pie(
            labels=status_counts.index.tolist(),
            values=status_counts.values.tolist(),
            hole=0.55,
            marker=dict(colors=["#4caf50", "#f44336", "#4f8ef7"]),
            textfont=dict(color="#e8f0fe"),
        ))
        fig2.update_layout(
            title="Status Distribution",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8d6f0"),
            title_font=dict(color="#e8f0fe"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown("### 🔍 Filter Records")
fcol1, fcol2, fcol3 = st.columns([2, 1, 1])

with fcol1:
    search_term = st.text_input(
        "Search commit messages or repo names",
        placeholder="e.g. Daily Backup, assignments...",
        label_visibility="collapsed",
    )
with fcol2:
    status_filter = st.selectbox(
        "Status",
        options=["All", "success", "failed", "no_changes"],
        label_visibility="collapsed",
    )
with fcol3:
    sort_order = st.selectbox(
        "Sort",
        options=["Newest First", "Oldest First"],
        label_visibility="collapsed",
    )

# Apply filters
filtered = df.copy()
if search_term:
    mask = (
        filtered["commit_message"].str.contains(search_term, case=False, na=False)
        | filtered["repository_name"].str.contains(search_term, case=False, na=False)
    )
    filtered = filtered[mask]
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]
if sort_order == "Oldest First":
    filtered = filtered.sort_values("backup_datetime", ascending=True)

st.markdown(f"*Showing **{len(filtered)}** of **{len(df)}** records*")
st.markdown("<br>", unsafe_allow_html=True)

# ── Records Table ─────────────────────────────────────────────────────────────
for _, row in filtered.iterrows():
    status = row["status"]
    badge_class = {"success": "badge-success", "failed": "badge-failed", "no_changes": "badge-info"}.get(status, "badge-info")
    icon = {"success": "✅", "failed": "❌", "no_changes": "ℹ️"}.get(status, "•")
    dt_str = row["backup_datetime"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row["backup_datetime"]) else "—"
    duration = f"{row['duration_seconds']:.1f}s" if pd.notna(row.get("duration_seconds")) else "—"

    with st.container():
        st.markdown(f"""
        <div class="info-box" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div style="font-size:0.95rem;font-weight:600;color:#e8f0fe;">{icon} {row['commit_message']}</div>
                    <div style="font-size:0.78rem;color:#6a8ab0;margin-top:4px;">
                        🕐 {dt_str} &nbsp;·&nbsp; 📁 {row['files_uploaded']} file(s) &nbsp;·&nbsp; ⏱ {duration}
                        {f"&nbsp;·&nbsp; 🔗 {row['repository_name']}" if row.get('repository_name') else ''}
                    </div>
                </div>
                <span class="badge {badge_class}">{status.upper().replace('_', ' ')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if status == "failed" and pd.notna(row.get("error_message")):
            with st.expander("⚠️ Error Details"):
                st.code(row["error_message"], language=None)

st.markdown("<br>", unsafe_allow_html=True)

# ── CSV Export ────────────────────────────────────────────────────────────────
st.markdown("### 📥 Export Data")
csv_data = filtered.to_csv(index=False)
st.download_button(
    label="⬇️  Download as CSV",
    data=csv_data,
    file_name="backup_history.csv",
    mime="text/csv",
    use_container_width=False,
)
