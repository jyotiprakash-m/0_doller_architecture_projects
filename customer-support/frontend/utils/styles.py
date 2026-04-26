"""
Custom CSS styles for SupportSim AI Streamlit frontend.
Premium dark theme with emerald/teal accents.
"""
import streamlit as st


def inject_custom_css():
    st.markdown("""
    <style>
        /* Dark theme overrides */
        .stApp {
            background-color: #0f172a;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid #334155;
            border-radius: 1rem;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #10b981;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #10b981, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-label {
            color: #9ca3af;
            font-size: 0.9rem;
            margin-top: 0.3rem;
        }

        /* Score badges */
        .score-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 2rem;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .score-high { background: #065f46; color: #34d399; }
        .score-medium { background: #78350f; color: #fbbf24; }
        .score-low { background: #7f1d1d; color: #f87171; }

        /* Chat bubbles */
        .chat-customer {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 1rem 1rem 1rem 0.25rem;
            padding: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
        }
        .chat-agent {
            background: linear-gradient(135deg, #064e3b, #0f172a);
            border: 1px solid #065f46;
            border-radius: 1rem 1rem 0.25rem 1rem;
            padding: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
            margin-left: auto;
        }

        /* Emotion indicator */
        .emotion-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .emotion-angry { background: #7f1d1d; color: #fca5a5; }
        .emotion-frustrated { background: #78350f; color: #fde68a; }
        .emotion-neutral { background: #1e3a5f; color: #93c5fd; }
        .emotion-satisfied { background: #064e3b; color: #6ee7b7; }
        .emotion-happy { background: #065f46; color: #34d399; }

        /* Difficulty badges */
        .diff-easy { background: #065f46; color: #34d399; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; }
        .diff-medium { background: #78350f; color: #fbbf24; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; }
        .diff-hard { background: #7f1d1d; color: #f87171; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; }

        /* Category tags */
        .category-tag {
            background: #1e293b;
            border: 1px solid #475569;
            color: #cbd5e1;
            padding: 0.2rem 0.6rem;
            border-radius: 0.5rem;
            font-size: 0.8rem;
        }

        /* Cards */
        .info-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 0.75rem;
            padding: 1.2rem;
            margin: 0.5rem 0;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid #1e293b;
        }

        /* Button styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #10b981, #059669);
            border: none;
            font-weight: 600;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #059669, #047857);
        }
    </style>
    """, unsafe_allow_html=True)


def score_badge(score: float) -> str:
    """Return HTML for a score badge with appropriate color."""
    if score >= 75:
        cls = "score-high"
    elif score >= 50:
        cls = "score-medium"
    else:
        cls = "score-low"
    return f'<span class="score-badge {cls}">{score:.0f}/100</span>'


def emotion_badge(emotion: str) -> str:
    """Return HTML for an emotion indicator badge."""
    emoji_map = {"angry": "😡", "frustrated": "😤", "neutral": "😐", "satisfied": "😊", "happy": "😄"}
    emoji = emoji_map.get(emotion, "😐")
    cls = f"emotion-{emotion}"
    return f'<span class="emotion-badge {cls}">{emoji} {emotion.title()}</span>'


def difficulty_badge(difficulty: str) -> str:
    """Return HTML for a difficulty badge."""
    cls = f"diff-{difficulty}"
    return f'<span class="{cls}">{difficulty.upper()}</span>'


def metric_card(value, label, emoji="📊") -> str:
    """Return HTML for a metric card."""
    return f"""
    <div class="metric-card">
        <div style="font-size: 1.5rem;">{emoji}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
