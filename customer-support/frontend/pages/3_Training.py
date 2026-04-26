"""
Training Page — Real-time chat simulation with AI customer persona.
"""
import streamlit as st
from utils.styles import inject_custom_css, emotion_badge, difficulty_badge

inject_custom_css()

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

api = st.session_state.api

# Initialize training session state
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "session_scenario" not in st.session_state:
    st.session_state.session_scenario = None
if "emotional_state" not in st.session_state:
    st.session_state.emotional_state = "neutral"

st.markdown("# 🎭 Training Simulator")


def show_scenario_selection():
    """Show scenario selection interface."""
    st.caption("Select a scenario to start your training session.")

    scenarios = api.list_scenarios()

    if not scenarios:
        st.info("No scenarios available. Go to the **Scenarios** page to create or generate some.")
        return

    # Group by difficulty
    for difficulty in ["easy", "medium", "hard"]:
        filtered = [s for s in scenarios if s.get("difficulty") == difficulty]
        if filtered:
            st.markdown(f"### {difficulty_badge(difficulty)} {difficulty.title()} Scenarios", unsafe_allow_html=True)

            for scenario in filtered:
                with st.container():
                    col_info, col_action = st.columns([4, 1])

                    with col_info:
                        category = scenario.get("category", "").replace("_", " ").title()
                        st.markdown(f"""
                        <div class="info-card">
                            <h4 style="margin: 0;">🎭 {scenario['persona_name']}</h4>
                            <p style="color: #9ca3af; margin: 0.3rem 0; font-size: 0.9rem;">
                                {scenario['persona_description'][:150]}...
                            </p>
                            <p style="font-size: 0.85rem;"><strong>Issue:</strong> {scenario.get('issue_description', '')[:100]}...</p>
                            <span class="category-tag">{category}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_action:
                        if st.button("▶️ Start", key=f"start_{scenario['id']}", type="primary"):
                            with st.spinner("Starting training session..."):
                                result = api.start_session(scenario["id"])
                                if result:
                                    st.session_state.active_session = result["session"]
                                    st.session_state.session_scenario = result["scenario"]
                                    st.session_state.emotional_state = result["emotional_state"]
                                    st.session_state.chat_messages = [
                                        {"role": "customer", "content": result["customer_message"],
                                         "emotional_state": result["emotional_state"]}
                                    ]
                                    # Update credits
                                    if "credits_remaining" in result:
                                        st.session_state.user["credits"] = result["credits_remaining"]
                                    st.rerun()


def show_training_chat():
    """Show the active training chat interface."""
    session = st.session_state.active_session
    scenario = st.session_state.session_scenario

    # Scenario info panel
    col_title, col_info, col_emotion = st.columns([2, 2, 1])

    with col_title:
        st.markdown(f"### 🎭 {scenario['persona_name']}")
    with col_info:
        category = scenario.get("category", "").replace("_", " ").title()
        st.markdown(
            f"{difficulty_badge(scenario.get('difficulty', 'medium'))} "
            f"<span class='category-tag'>{category}</span>",
            unsafe_allow_html=True
        )
    with col_emotion:
        st.markdown(
            f"**Mood:** {emotion_badge(st.session_state.emotional_state)}",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Chat messages
    for msg in st.session_state.chat_messages:
        if msg["role"] == "customer":
            with st.chat_message("user", avatar="😤"):
                st.write(msg["content"])
                if msg.get("emotional_state"):
                    st.markdown(
                        f"<small>{emotion_badge(msg['emotional_state'])}</small>",
                        unsafe_allow_html=True
                    )
        else:
            with st.chat_message("assistant", avatar="🧑‍💼"):
                st.write(msg["content"])

    # Check if session is still active
    if session.get("status") == "completed" or st.session_state.get("session_completed"):
        st.success("🎉 Session completed! Go to the **Review** page to see your evaluation.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Get Evaluation", type="primary", use_container_width=True):
                with st.spinner("AI is evaluating your performance..."):
                    result = api.run_evaluation(session["id"])
                    if result:
                        st.success(f"Overall Score: {result.get('overall_score', 0):.0f}/100")
        with col2:
            if st.button("🔄 New Session", use_container_width=True):
                st.session_state.active_session = None
                st.session_state.chat_messages = []
                st.session_state.session_scenario = None
                st.session_state.session_completed = False
                st.rerun()
        return

    # Agent input
    agent_input = st.chat_input("Type your response as the support agent...")

    if agent_input:
        # Add agent message to display
        st.session_state.chat_messages.append({"role": "agent", "content": agent_input})

        # Send to backend and get customer response
        with st.spinner("Customer is typing..."):
            result = api.send_response(session["id"], agent_input)

        if result:
            st.session_state.chat_messages.append({
                "role": "customer",
                "content": result["customer_message"],
                "emotional_state": result["emotional_state"],
            })
            st.session_state.emotional_state = result["emotional_state"]

            if result.get("is_resolved"):
                st.session_state.session_completed = True
                st.session_state.active_session["status"] = "completed"

        st.rerun()

    # End session button
    st.markdown("---")
    if st.button("⏹️ End Session", use_container_width=True):
        api.end_session(session["id"])
        st.session_state.session_completed = True
        st.session_state.active_session["status"] = "completed"
        st.rerun()


# Main logic
if st.session_state.active_session:
    show_training_chat()
else:
    show_scenario_selection()
