"""
agent.py - Telecom Ops Intelligence Agent (Phase 2 — with Memory)
A LangGraph ReAct agent that answers telecom ops questions using SQL.
Now with conversation memory — handles follow-up questions naturally.

Built to mirror real workflows from Liberty Global (MNP incidents)
and M-Pesa AML/KYC (ETL pipeline monitoring).
"""

import sqlite3
import os
import uuid
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# looks in the same folder as this script
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telecom_ops.db")


# ─────────────────────────────────────────────
# TOOL 1: get_schema
# ─────────────────────────────────────────────
@tool
def get_schema(table_name: str = "") -> str:
    """
    Returns the schema for a specific table, or all tables if input is empty.
    Use this FIRST before writing any SQL to understand column names and types.
    Input: a table name like 'mnp_requests', or empty string for all tables.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if table_name.strip():
        cur.execute(f"PRAGMA table_info({table_name.strip()})")
        cols = cur.fetchall()
        if not cols:
            conn.close()
            return f"Table '{table_name}' not found. Available tables: customers, mnp_requests, incidents, etl_pipeline_logs"
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


# ─────────────────────────────────────────────
# TOOL 2: run_sql
# ─────────────────────────────────────────────
@tool
def run_sql(query: str) -> str:
    """
    Executes a SQL SELECT query against the telecom ops database.
    Input: a valid SQLite SELECT statement.
    Tables: customers, mnp_requests, incidents, etl_pipeline_logs.
    Only SELECT is allowed — no INSERT, UPDATE, or DELETE.
    """
    query = query.strip()

    if not query.upper().startswith("SELECT"):
        return "Only SELECT queries are allowed. No data modifications permitted."

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
        return f"SQL Error: {str(e)}\nQuery attempted: {query}"


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Telecom Operations Intelligence Agent with deep expertise in:
- MNP (Mobile Number Portability) incident diagnosis and resolution
- KYC/AML ETL pipeline monitoring (M-Pesa style workflows)
- Customer account troubleshooting across Liberty Global-style systems

Your job is to help ops engineers quickly diagnose issues, find root causes, and suggest workarounds.

You have memory of the full conversation — use it to handle follow-up questions naturally.
For example if the user asks "now show only the P1 ones" or "what about that customer's KYC status",
refer back to what was already discussed without re-explaining everything.

WORKFLOW:
1. Use get_schema to check relevant table columns before writing SQL
2. Run targeted SQL queries using run_sql
3. Interpret the results in ops context
4. Give a clear diagnosis + recommended action

Always lead with the diagnosis, show key data, and end with a concrete next step."""


# ─────────────────────────────────────────────
# BUILD THE AGENT — with MemorySaver checkpointer
# This is the only change from Phase 1:
# MemorySaver stores the full conversation history
# so the agent remembers previous turns
# ─────────────────────────────────────────────
def build_agent():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # MemorySaver = in-memory conversation store
    # Each "thread_id" is one conversation session
    memory = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=[get_schema, run_sql],
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,        # <-- this is the only new line vs Phase 1
    )
    return agent


# ─────────────────────────────────────────────
# CLI RUNNER
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  TELECOM OPS INTELLIGENCE AGENT  [Phase 2 - Memory]")
    print("  Powered by LangGraph + Claude")
    print("="*60)
    print("I remember the full conversation — ask follow-up questions!")
    print("Type 'new' to start a fresh session. Type 'quit' to exit.\n")

    agent = build_agent()

    # Each session gets a unique thread_id
    # This is how LangGraph tracks which conversation to load from memory
    thread_id = str(uuid.uuid4())
    print(f"Session ID: {thread_id[:8]}...\n")

    samples = [
        "Show me all stuck MNP requests",
        "  → follow up: Which of those has been stuck the longest?",
        "  → follow up: What is the RCA for that incident?",
        "",
        "Which KYC files failed recently?",
        "  → follow up: Which customer is affected by the first failure?",
        "  → follow up: What is that customer's account status?",
    ]

    print("Try this multi-turn conversation:")
    for s in samples:
        print(f"  {s}")
    print()

    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if user_input.lower() == "new":
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            print(f"\nNew session started. ID: {thread_id[:8]}...\n")
            continue

        if not user_input:
            continue

        print()
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,      # <-- passes thread_id so agent loads memory
            )

            final = result["messages"][-1].content
            print("\n" + "="*60)
            print("Agent:")
            print(final)
            print("="*60 + "\n")

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()