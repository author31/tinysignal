# TinySignal
TinySignal is a local-first, lightweight app that clusters Hacker News posts and delivers trending discussions straight to your Telegram.

<img src="assets/TinySignal-screen-recording.gif" width="300">

# How to run
```bash
make run
```

# Hot News Summarization Feature
1. Fetch stories from a news source. In this project, we are using "https://news.ycombinator.com/".
2. Cluster all stories based on the embeddings of each story.
3. Use an LLM to generate a title for each cluster.
4. Deliver the summaries to Telegram as `InlineKeyboardButton` elements.

# Local-First, Standalone Application
Powered by DuckDB, a fast in-process database system.
No extra services are required (e.g., Postgres, Redis, vector databases, etc.).

- DuckDB as a database SQL engine
- DuckDB as a vectory databases
- DuckDB as a cache handler (see app/services/cache.py)

# Design
Layers inside `app`:
- infrastructure – handles database connections
- models – contains Pydantic models
- repositories – handles database operations
- services – handles business logic
