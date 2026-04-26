"""
Dashboard Page — Training stats, performance trends, and recent sessions.
"""
import streamlit as st
from utils.styles import inject_custom_css, metric_card, score_badge

inject_custom_css()

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

api = st.session_state.api
st.markdown("# 📊 Training Dashboard")

# Fetch dashboard data
data = api.get_dashboard()

if not data:
    st.info("No data yet. Start training to see your dashboard!")
    st.stop()

# KPI Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(metric_card(data.get("completed_sessions", 0), "Sessions Completed", "🎯"), unsafe_allow_html=True)
with col2:
    avg = data.get("avg_overall_score", 0)
    st.markdown(metric_card(f"{avg:.0f}", "Avg Score", "⭐"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card(data.get("total_knowledge_bases", 0), "Knowledge Bases", "📚"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card(data.get("total_scenarios", 0), "Scenarios", "🎭"), unsafe_allow_html=True)
with col5:
    st.markdown(metric_card(f"{data.get('user_credits', 0):.1f}", "Credits", "💎"), unsafe_allow_html=True)

st.markdown("---")

# Score Breakdown
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Score Breakdown")

    scores = {
        "Empathy": data.get("avg_empathy_score", 0),
        "Accuracy": data.get("avg_accuracy_score", 0),
        "Resolution": data.get("avg_resolution_score", 0),
        "Communication": data.get("avg_communication_score", 0),
    }

    for name, score in scores.items():
        col_name, col_bar, col_val = st.columns([1, 3, 1])
        with col_name:
            st.write(f"**{name}**")
        with col_bar:
            st.progress(min(score / 100, 1.0))
        with col_val:
            st.markdown(score_badge(score), unsafe_allow_html=True)

with col_right:
    st.subheader("🏆 Best Category")
    best = data.get("best_category")
    if best:
        cat = best.get("category", "N/A").replace("_", " ").title()
        score = best.get("avg_score", 0)
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <div style="font-size: 2rem;">🥇</div>
            <h3 style="margin: 0.5rem 0;">{cat}</h3>
            <p style="color: #10b981; font-size: 1.5rem; font-weight: 700;">{score:.0f}/100</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Complete training sessions to see your best category.")

# Score Trend
st.markdown("---")
st.subheader("📊 Performance Trend")

trend = data.get("score_trend", [])
if trend:
    import pandas as pd
    df = pd.DataFrame(trend)
    df["date"] = pd.to_datetime(df["date"])
    st.line_chart(df.set_index("date")["score"], use_container_width=True)
else:
    st.info("Complete more sessions to see your performance trend.")

# Recent Sessions
st.markdown("---")
st.subheader("🕐 Recent Sessions")

recent = data.get("recent_sessions", [])
if recent:
    for session in recent[:5]:
        col_info, col_score, col_status = st.columns([3, 1, 1])
        with col_info:
            persona = session.get("persona_name", "Unknown")
            category = session.get("category", "").replace("_", " ").title()
            st.write(f"**{persona}** — {category}")
        with col_score:
            score = session.get("overall_score")
            if score:
                st.markdown(score_badge(score), unsafe_allow_html=True)
            else:
                st.write("—")
        with col_status:
            status = session.get("status", "unknown")
            if status == "completed":
                st.success("✅ Done")
            elif status == "active":
                st.warning("⏳ Active")
            else:
                st.write(status)
else:
    st.info("No sessions yet. Start training from the Training page!")
