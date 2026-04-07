"""
app.py - Streamlit UI for Telecom Ops Intelligence Agent
Phase 3 — Chat interface with memory, session management, and quick actions
"""

import streamlit as st
import sqlite3
import os
import uuid
from dotenv import load_dotenv
# Auto-create DB if it doesn't exist
from setup_db import setup_database
if not os.path.exists(DB_PATH):
    setup_database()
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telecom_ops.db")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Telecom Ops Agent",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — dark ops terminal aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0a0e1a;
    color: #c9d1e0;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }

/* Header */
.ops-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a3a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.ops-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00d4ff, #0066ff, #00d4ff);
}
.ops-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    color: #00d4ff;
    margin: 0;
    letter-spacing: -0.5px;
}
.ops-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4a7fa5;
    margin-top: 0.3rem;
    letter-spacing: 1px;
}
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #00ff88;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Chat messages */
.chat-user {
    background: #0d1f35;
    border: 1px solid #1e3a5f;
    border-radius: 12px 12px 4px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 0 0.6rem 15%;
    font-size: 0.92rem;
    color: #a8c8e8;
}
.chat-agent {
    background: #0a1520;
    border: 1px solid #163045;
    border-left: 3px solid #00d4ff;
    border-radius: 4px 12px 12px 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.6rem 15% 0.6rem 0;
    font-size: 0.92rem;
    color: #c9d1e0;
    line-height: 1.65;
}
.chat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    opacity: 0.6;
}
.user-label { color: #4a9fd4; }
.agent-label { color: #00d4ff; }

/* Thinking indicator */
.thinking {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #00d4ff;
    opacity: 0.7;
    padding: 0.5rem 0;
}

/* Quick action buttons */
.stButton > button {
    background: #0d1b2a !important;
    border: 1px solid #1e3a5f !important;
    color: #7ab3d4 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    padding: 0.5rem 0.8rem !important;
    width: 100% !important;
    text-align: left !important;
    transition: all 0.2s !important;
    white-space: normal !important;
    height: auto !important;
    line-height: 1.4 !important;
}
.stButton > button:hover {
    background: #132035 !important;
    border-color: #00d4ff !important;
    color: #00d4ff !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #080c16 !important;
    border-right: 1px solid #1a2a3a !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Sidebar stats */
.stat-card {
    background: #0d1b2a;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}
.stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #4a7fa5;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.stat-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.4rem;
    color: #00d4ff;
    line-height: 1.2;
}
.stat-sub {
    font-size: 0.72rem;
    color: #4a7fa5;
}

/* Input */
.stTextInput > div > div > input {
    background: #0d1b2a !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #c9d1e0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 0 1px #00d4ff22 !important;
}

/* Divider */
hr { border-color: #1a2a3a; }

/* Scrollable chat area */
.chat-container {
    max-height: 58vh;
    overflow-y: auto;
    padding-right: 4px;
    scrollbar-width: thin;
    scrollbar-color: #1e3a5f #080c16;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TOOLS (same as agent.py)
# ─────────────────────────────────────────────
@tool
def get_schema(table_name: str = "") -> str:
    """
    Returns the schema for a specific table, or all tables if input is empty.
    Use this FIRST before writing any SQL to understand column names and types.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if table_name.strip():
        cur.execute(f"PRAGMA table_info({table_name.strip()})")
        cols = cur.fetchall()
        if not cols:
            conn.close()
            return f"Table '{table_name}' not found."
        schema = f"Table: {table_name}\nColumns:\n"
        for col in cols:
            schema += f"  - {col[1]} ({col[2]})\n"
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        schema = "Available tables:\n"
        for t in tables:
            cur.execute(f"PRAGMA table_info({t})")
            cols = cur.fetchall()
            schema += f"\n[{t}]\n"
            for col in cols:
                schema += f"  - {col[1]} ({col[2]})\n"
    conn.close()
    return schema


@tool
def run_sql(query: str) -> str:
    """
    Executes a SQL SELECT query against the telecom ops database.
    Tables: customers, mnp_requests, incidents, etl_pipeline_logs.
    Only SELECT is allowed.
    """
    query = query.strip()
    if not query.upper().startswith("SELECT"):
        return "Only SELECT queries are allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        conn.close()
        if not rows:
            return "Query returned 0 rows."
        result = " | ".join(cols) + "\n"
        result += "-" * (len(result) - 1) + "\n"
        for row in rows[:25]:
            result += " | ".join(str(v) if v is not None else "NULL" for v in row) + "\n"
        if len(rows) > 25:
            result += f"... ({len(rows) - 25} more rows truncated)"
        return result
    except sqlite3.Error as e:
        return f"SQL Error: {str(e)}"


SYSTEM_PROMPT = """You are a Telecom Operations Intelligence Agent with deep expertise in:
- MNP (Mobile Number Portability) incident diagnosis and resolution
- KYC/AML ETL pipeline monitoring (SwiftPay style workflows)
- Customer account troubleshooting across NovaTel Communications-style systems

You have memory of the full conversation — use it to handle follow-up questions naturally.

WORKFLOW:
1. Use get_schema to check relevant table columns before writing SQL
2. Run targeted SQL queries using run_sql
3. Interpret results in ops context
4. Give a clear diagnosis + recommended action

Always lead with the diagnosis and end with a concrete next step."""


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "agent" not in st.session_state:
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    memory = MemorySaver()
    st.session_state.agent = create_react_agent(
        model=llm,
        tools=[get_schema, run_sql],
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )

if "quick_action" not in st.session_state:
    st.session_state.quick_action = None


# ─────────────────────────────────────────────
# DB STATS for sidebar
# ─────────────────────────────────────────────
@st.cache_data
def get_db_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mnp_requests WHERE stuck_since IS NOT NULL")
        stuck = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('OPEN','IN_PROGRESS','ESCALATED')")
        open_inc = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM etl_pipeline_logs WHERE status='FAILED'")
        etl_fail = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM customers WHERE kyc_status != 'VERIFIED'")
        kyc_pend = cur.fetchone()[0]
        conn.close()
        return stuck, open_inc, etl_fail, kyc_pend
    except:
        return 0, 0, 0, 0

stuck, open_inc, etl_fail, kyc_pend = get_db_stats()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛰️ System Status")
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Stuck MNP Requests</div>
        <div class="stat-value">{stuck}</div>
        <div class="stat-sub">awaiting resolution</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Open Incidents</div>
        <div class="stat-value">{open_inc}</div>
        <div class="stat-sub">P1/P2/P3 combined</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">ETL Failures</div>
        <div class="stat-value">{etl_fail}</div>
        <div class="stat-sub">pipeline jobs failed</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">KYC Pending/Failed</div>
        <div class="stat-value">{kyc_pend}</div>
        <div class="stat-sub">customers unverified</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    quick_questions = [
        "Show all stuck MNP requests",
        "Which KYC files failed recently?",
        "Show open P1 and P2 incidents",
        "Any customers with compound failures?",
        "Summarize today's ETL pipeline status",
        "Which region has the most issues?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"qa_{q}"):
            st.session_state.quick_action = q

    st.markdown("---")
    if st.button("🔄 New Session", key="new_session"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.62rem; color:#2a4a6a; margin-top:1rem;">
    SESSION: {st.session_state.thread_id[:12]}...<br>
    TURNS: {len(st.session_state.messages) // 2}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
st.markdown("""
<div class="ops-header">
    <div class="ops-title">🛰️ Telecom Ops Intelligence Agent</div>
    <div class="ops-subtitle">
        <span class="status-dot"></span>
        LANGGRAPH · CLAUDE · SQLITE · LIBERTY GLOBAL + SWIFTPAY WORKFLOWS
    </div>
</div>
""", unsafe_allow_html=True)

# Chat history
chat_html = '<div class="chat-container">'
if not st.session_state.messages:
    chat_html += """
    <div style="text-align:center; padding:3rem 1rem; opacity:0.4;">
        <div style="font-size:2rem; margin-bottom:0.8rem;">🛰️</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#4a7fa5;">
            Ask me about MNP incidents, KYC failures,<br>ETL pipeline issues, or customer status
        </div>
    </div>
    """
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_html += f"""
            <div class="chat-user">
                <div class="chat-label user-label">YOU</div>
                {msg["content"]}
            </div>"""
        else:
            content = msg["content"].replace("\n", "<br>")
            chat_html += f"""
            <div class="chat-agent">
                <div class="chat-label agent-label">AGENT</div>
                {content}
            </div>"""
chat_html += "</div>"
st.markdown(chat_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INPUT — handles both typed and quick actions
# ─────────────────────────────────────────────
user_input = st.chat_input("Ask about MNP incidents, KYC failures, ETL pipeline, customer status...")

# Trigger from quick action button
if st.session_state.quick_action:
    user_input = st.session_state.quick_action
    st.session_state.quick_action = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.spinner("Agent is thinking..."):
        try:
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
            )
            answer = result["messages"][-1].content
        except Exception as e:
            answer = f"Error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
