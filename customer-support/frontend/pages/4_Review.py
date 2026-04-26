"""
Review Page — Session review, AI evaluation scores, and coaching feedback.
"""
import streamlit as st
from utils.styles import inject_custom_css, score_badge, emotion_badge, difficulty_badge

inject_custom_css()

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

api = st.session_state.api
st.markdown("# 📝 Session Review & Feedback")

sessions = api.list_sessions(status="completed")
if not sessions:
    st.info("No completed sessions yet.")
    st.stop()

session_options = {
    f"{s.get('persona_name', '?')} — {s.get('category', '').replace('_', ' ').title()} ({s['started_at'][:10]})": s
    for s in sessions
}
selected_label = st.selectbox("Select session:", list(session_options.keys()))
selected = session_options[selected_label]

st.markdown("---")
session_data = api.get_session(selected["id"])
if not session_data:
    st.error("Failed to load session.")
    st.stop()

messages = session_data.get("messages", [])
scenario = session_data.get("scenario", {})

tab_eval, tab_transcript, tab_feedback = st.tabs(["📊 Evaluation", "💬 Transcript", "💡 Coaching"])

with tab_eval:
    evaluation = api.get_evaluation(selected["id"])
    if not evaluation:
        if st.button("🔍 Run AI Evaluation", type="primary"):
            with st.spinner("Evaluating..."):
                evaluation = api.run_evaluation(selected["id"])
                if evaluation:
                    st.rerun()
    if evaluation:
        overall = evaluation.get("overall_score", 0)
        st.markdown(f"<div style='text-align:center;padding:1rem;'><span style='font-size:3rem;font-weight:700;color:#10b981;'>{overall:.0f}/100</span></div>", unsafe_allow_html=True)

        cols = st.columns(4)
        for i, (name, key) in enumerate([("Empathy", "empathy_score"), ("Accuracy", "accuracy_score"), ("Resolution", "resolution_score"), ("Communication", "communication_score")]):
            with cols[i]:
                v = evaluation.get(key, 0)
                st.metric(name, f"{v:.0f}")

        col_s, col_i = st.columns(2)
        with col_s:
            st.subheader("✅ Strengths")
            for s in evaluation.get("strengths", []):
                st.success(f"• {s.get('point', s) if isinstance(s, dict) else s}")
        with col_i:
            st.subheader("🔧 Improve")
            for s in evaluation.get("improvements", []):
                st.warning(f"• {s.get('point', s) if isinstance(s, dict) else s}")

with tab_transcript:
    for msg in messages:
        avatar = "😤" if msg["role"] == "customer" else "🧑‍💼"
        with st.chat_message("user" if msg["role"] == "customer" else "assistant", avatar=avatar):
            st.write(msg["content"])

with tab_feedback:
    evaluation = api.get_evaluation(selected["id"])
    if not evaluation:
        st.info("Run evaluation first.")
    elif st.button("🎓 Generate Coaching", type="primary"):
        with st.spinner("Generating feedback..."):
            fb = api.get_feedback(selected["id"])
            if fb:
                st.session_state[f"fb_{selected['id']}"] = fb
                st.rerun()

    fb = st.session_state.get(f"fb_{selected['id']}")
    if fb:
        st.markdown(f"**Assessment:** {fb.get('overall_assessment', '')}")
        st.markdown("### ✅ Did Well")
        for item in fb.get("did_well", []):
            st.success(f"• {item.get('point', item) if isinstance(item, dict) else item}")
        st.markdown("### 🔧 Improve")
        for item in fb.get("improve", []):
            if isinstance(item, dict):
                st.warning(f"• {item.get('point', '')}")
                if item.get("better_alternative"):
                    st.info(f"💡 Try: *\"{item['better_alternative']}\"*")
            else:
                st.warning(f"• {item}")
        st.markdown("### 🔑 Takeaways")
        for tip in fb.get("key_takeaways", []):
            st.write(f"• {tip}")
        rec = fb.get("difficulty_recommendation", "maintain")
        st.info(f"Difficulty recommendation: **{rec.upper()}**")
        if fb.get("encouragement"):
            st.success(f"💪 {fb['encouragement']}")
