"""
Scenarios Page — Create, generate, and manage training scenarios.
"""
import streamlit as st
from utils.styles import inject_custom_css, difficulty_badge

inject_custom_css()

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

api = st.session_state.api
st.markdown("# 🎭 Scenario Manager")
st.caption("Create custom scenarios or auto-generate from your knowledge base.")

# Auto-generate section
st.subheader("🤖 Auto-Generate from Knowledge Base")
kbs = api.list_kbs()

if kbs:
    col_kb, col_count, col_btn = st.columns([3, 1, 1])
    with col_kb:
        kb_options = {kb["name"]: kb["id"] for kb in kbs}
        selected_kb = st.selectbox("Knowledge Base:", list(kb_options.keys()))
    with col_count:
        count = st.number_input("Count:", min_value=1, max_value=10, value=3)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Generate", type="primary"):
            with st.spinner("AI is creating realistic scenarios..."):
                result = api.generate_scenarios(kb_options[selected_kb], count)
                if result:
                    st.success(f"✅ Generated {len(result.get('scenarios', []))} scenarios!")
                    st.rerun()
else:
    st.info("Create a Knowledge Base first to auto-generate scenarios.")

st.markdown("---")

# Manual create
with st.expander("✏️ Create Custom Scenario", expanded=False):
    with st.form("create_scenario"):
        persona_name = st.text_input("Customer Name", placeholder="e.g., Alex Johnson")
        persona_desc = st.text_area("Customer Background", placeholder="Brief personality and backstory...", height=80)
        issue_desc = st.text_area("Issue Description", placeholder="What problem is this customer facing?", height=80)

        col1, col2, col3 = st.columns(3)
        with col1:
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
        with col2:
            category = st.selectbox("Category", [
                "billing", "technical_support", "complaint", "feature_request",
                "onboarding", "cancellation", "account_issue", "general_inquiry"
            ])
        with col3:
            emotion = st.selectbox("Initial Emotion", ["neutral", "frustrated", "angry"])

        expected = st.text_area("Expected Resolution", placeholder="What should a good agent do?", height=60)

        kb_id = None
        if kbs:
            kb_select = st.selectbox("Link to KB (optional):", ["None"] + [kb["name"] for kb in kbs])
            if kb_select != "None":
                kb_id = next(kb["id"] for kb in kbs if kb["name"] == kb_select)

        if st.form_submit_button("Create Scenario", type="primary", use_container_width=True):
            if persona_name and issue_desc:
                result = api.create_scenario({
                    "persona_name": persona_name,
                    "persona_description": persona_desc,
                    "issue_description": issue_desc,
                    "difficulty": difficulty,
                    "category": category,
                    "initial_emotional_state": emotion,
                    "expected_resolution": expected,
                    "kb_id": kb_id,
                })
                if result:
                    st.success("✅ Scenario created!")
                    st.rerun()
            else:
                st.warning("Name and issue description are required.")

st.markdown("---")

# List all scenarios
st.subheader("📋 All Scenarios")
scenarios = api.list_scenarios()

if not scenarios:
    st.info("No scenarios yet. Create or generate some above!")
else:
    for scenario in scenarios:
        with st.container():
            col_info, col_meta, col_action = st.columns([3, 2, 1])
            with col_info:
                auto = "🤖" if scenario.get("is_auto_generated") else "✏️"
                st.markdown(f"**{auto} {scenario['persona_name']}**")
                st.caption(scenario.get("issue_description", "")[:120])
            with col_meta:
                cat = scenario.get("category", "").replace("_", " ").title()
                st.markdown(f"{difficulty_badge(scenario.get('difficulty', 'medium'))} · {cat}", unsafe_allow_html=True)
            with col_action:
                if st.button("🗑️", key=f"del_scen_{scenario['id']}"):
                    api.delete_scenario(scenario["id"])
                    st.rerun()
