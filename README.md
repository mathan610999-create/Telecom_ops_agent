# 🛰️ Telecom Ops Intelligence Agent

A LangChain ReAct agent that automates the manual RCA (Root Cause Analysis) workflow from real telecom operations — specifically MNP (Mobile Number Portability) incidents and KYC/AML ETL pipeline monitoring.

Built with: **Python + LangChain + Claude (Anthropic) + SQLite**

---

## What It Does

Ask plain English questions like:

> *"Customer C001 raised a complaint about their MNP — what's happening?"*

The agent will:
1. **Reason** about what data it needs
2. **Check the schema** to understand table structure
3. **Write and run SQL** queries
4. **Interpret the results** in ops context
5. **Return a diagnosis + recommended action**

---

## The Database Schema

Mirrors real telecom/fintech ops systems:

| Table | What It Represents |
|---|---|
| `customers` | Customer accounts with KYC status, plan, region |
| `mnp_requests` | Port requests with current stage and stuck_since timestamp |
| `incidents` | Open/resolved incidents with RCA and assigned team |
| `etl_pipeline_logs` | KYC/AML/MNP ETL job runs with failure stage and error messages |

---

## How the ReAct Agent Works

```
User Question
    ↓
Thought: What do I need to know?
    ↓
Action: get_schema (understand tables)
    ↓
Observation: column names and types
    ↓
Thought: Now I can write the right SQL
    ↓
Action: run_sql (execute query)
    ↓
Observation: query results
    ↓
Thought: I have enough to answer
    ↓
Final Answer: diagnosis + recommended action
```

This is the **ReAct (Reason + Act)** loop — the foundation of all modern AI agents.

---

## Setup

```bash
# 1. Clone / copy the project files
cd telecom-ops-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Anthropic API key
cp .env.example .env
# Edit .env and paste your key from https://console.anthropic.com/

# 4. Create the database
python setup_db.py

# 5. Run the agent
python agent.py
```

---

## Sample Questions to Try

```
1. Customer C001 raised a complaint about their MNP — what's the current status and what should we do?
2. Which KYC files failed in the last 3 days and what were the errors?
3. Show me all open P1 and P2 incidents and their RCA
4. How many MNP requests are currently stuck and at which stage?
5. Which customers have pending KYC status and active accounts?
6. What ETL jobs ran today and how many failed?
7. Is there anything unusual about customer C005?
```

---

## Project Structure

```
telecom-ops-agent/
├── setup_db.py       # Creates SQLite DB with realistic mock data
├── agent.py          # Main ReAct agent (tools + prompt + executor)
├── requirements.txt
├── .env.example      # Copy to .env and add your API key
└── README.md
```

---

## Phase Roadmap

- [x] **Phase 1** — Core ReAct agent with SQL tools (this repo)
- [ ] **Phase 2** — Conversation memory (multi-turn follow-up questions)
- [ ] **Phase 3** — Streamlit UI + deploy to Streamlit Cloud (live demo link)

---

## Background

This agent automates workflows I performed manually as a Business Analyst at Prodapt Solutions (2021–2024), working on Liberty Global (MNP operations) and M-Pesa (KYC/AML ETL monitoring). The goal is to demonstrate how AI agents can reduce mean time to resolution (MTTR) for ops teams.
