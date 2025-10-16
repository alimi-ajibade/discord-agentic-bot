# Discord Agentic Bot

An agentic discord bot that leverages LangGraph, Google Gemini, and PostgreSQL with pgvector to provide context-aware assistance in your server.

## Highlights

- **Agent-first interactions** – Mention the bot to spin up a LangGraph agent that can call Discord-aware tools (send messages, react, fetch user/channel/server context) and the Google Search API.
- **Retrieval with pgvector** – Every message is persisted to PostgreSQL and embedded with `gemini-embedding-001`; the `/find` command surfaces relevant history via vector search.
- **Owner-tunable behavior** – Guild owners can update channel-specific agent instructions through the `/instruction` command.
- **FastAPI control plane** – A FastAPI app orchestrates the Discord bot lifecycle and exposes a ready-to-integrate `/health` check.
- **Observability hooks** – Loguru streams rich logs to stdout and `logs/app.log`, and optional LangSmith tracing is built in.

## Architecture at a Glance

```
FastAPI lifespan startup
│
├─ Discord bot (discord.py)
│  ├─ Events: on_ready, on_guild_join, on_message
│  ├─ Commands: /instruction, /find
│  └─ Agent invocations (LangGraph + Gemini)
│
├─ Background task    ──▶  Batch message embedding generator
│
└─ PostgreSQL (pgvector)
	├─ Users / Guilds / Channels / Agents / Messages tables
	└─ Vector indexes for cosine & L2 similarity
```

## Prerequisites

- Python **3.12** (the project targets `>=3.12,<4.0`).
- [Poetry](https://python-poetry.org/) for dependency management.
- PostgreSQL 14+ with the [`pgvector`](https://github.com/pgvector/pgvector) extension enabled.
- A Discord application & bot token with the `MESSAGE CONTENT` intent.
- Google Generative AI API access (Gemini) and a Programmable Search Engine (CSE ID) for Internet Search.
- (Optional) [LangSmith](https://smith.langchain.com/) credentials for tracing.

## Environment Variables

Create a `.env` file in the project root - Copy .env.example to the .env and fill in real values.

> Enable `pgvector` in your database before the first migration: `CREATE EXTENSION IF NOT EXISTS vector;`

## Setup

1. **Install dependencies**

   ```bash
   poetry install
   ```

2. **Create and migrate the database**

   ```bash
   poetry run alembic upgrade head
   ```

## Running the Service

Launch the FastAPI app (which also boots the Discord bot via the lifespan hook):

```bash
poetry run uvicorn src.main:app --reload
```

- `GET /health` returns a simple readiness payload.
- On startup the bot logs in, and a background coroutine continuously embeds uncached messages in batches (default batch size `50`).
- Logs stream to stdout and `logs/app.log`; rotate/retention are managed by Loguru.

## Discord Usage

- **Mention-driven conversations** – Mention the bot (`@YourBot what can you do?`) to trigger the agent. Messages are stored, embedded, and the agent replies using the `send_message` tool.
- **`/instruction <prompt>`** – Guild owners can set or update an instruction for the current channel. The text is stored on the associated `Agent` record and injected into the LangGraph prompt on subsequent mentions.
- **`/find <query>`** – Runs a semantic search across stored messages and summarizes the most relevant hits using Gemini.
- **Reactions & context tools** – The agent can programmatically react to messages and inspect users, channels, or the guild via its built-in toolset.

## Retrieval & Embeddings

- Messages are saved to the `messages` table with a nullable `embedding` column (`pgvector.Vector(768)`).
- `generate_embeddings` polls for messages lacking embeddings, fetches vectors from `gemini-embedding-001`, and writes them back.
- `find_similar_messages` uses `ORDER BY embedding <-> query` (via `cosine_distance`) to power semantic recall for the `/find` command and agent context.
