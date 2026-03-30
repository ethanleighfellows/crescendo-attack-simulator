# Architecture: Crescendo Jailbreak Generator

## Layer Diagram

```
┌─────────────────────────────────────────────┐
│                   GUI Layer                  │
│  React/TypeScript (Vite) + TailwindCSS      │
│  Setup → Live Run → Review → Export         │
├─────────────────────────────────────────────┤
│                  API Layer                   │
│  FastAPI (Python) — REST + WebSocket        │
│  /runs, /config, /export, /ws/run/{id}      │
├─────────────────────────────────────────────┤
│              Crescendo Engine                │
│  Standalone Python class wrapping the       │
│  core multi-turn orchestration loop         │
├─────────────────────────────────────────────┤
│           Provider Adapters                  │
│  OpenAI, Anthropic, Azure, Ollama, Gemini   │
│  Unified interface for target + simulator   │
├─────────────────────────────────────────────┤
│          Export Pipeline                     │
│  Transcript → XLSX (openpyxl)               │
│  Multi-sheet: summary, config, transcript   │
├─────────────────────────────────────────────┤
│        Configuration Storage                 │
│  Presets (YAML/JSON), runtime config,       │
│  environment-based secrets                   │
└─────────────────────────────────────────────┘
```

## Directory Structure

```
src/
  backend/
    main.py                  # FastAPI app entry
    api/
      routes.py              # REST endpoints
      websocket.py           # WebSocket for live streaming
    engine/
      crescendo.py           # Standalone Crescendo engine class
      memory.py              # Conversation memory system
      templates.py           # Prompt templates (extracted from source)
      schemas.py             # Pydantic schemas for structured output
      types.py               # Shared types (Turn, RunConfig, RunResult)
    providers/
      base.py                # Abstract provider interface
      openai_provider.py     # OpenAI / Azure OpenAI
      anthropic_provider.py  # Anthropic Claude
      ollama_provider.py     # Local Ollama models
    export/
      xlsx.py                # XLSX export with openpyxl
      schemas.py             # Output column definitions
    config/
      presets.py             # Conservative/balanced/aggressive presets
      settings.py            # App-level settings (Pydantic BaseSettings)
    safety/
      guardrails.py          # Research-use warnings, redaction, logging
  frontend/
    src/
      components/            # React UI components
      hooks/                 # Custom React hooks
      api/                   # API client (fetch wrapper)
      types/                 # TypeScript type definitions
      styles/                # Tailwind config + tokens
    index.html
    vite.config.ts
tests/
  backend/
    test_engine.py           # Crescendo engine unit tests
    test_providers.py        # Provider adapter tests
    test_export.py           # XLSX export tests
    test_presets.py          # Preset validation tests
    test_api.py              # API integration tests
```

## Key Design Decisions

1. **Python backend, TypeScript frontend**: The Crescendo engine is inherently Python (wrapping deepteam). The GUI is a separate React app communicating over HTTP/WebSocket. This keeps the engine testable and reusable outside the UI.

2. **WebSocket for live streaming**: Crescendo runs are multi-round and can take minutes. WebSocket provides real-time turn-by-turn updates to the UI without polling.

3. **Engine as standalone class**: `CrescendoEngine` is a pure Python class with no framework dependencies. It takes a config dict and provider instances, runs the attack, and yields turn events. This makes it testable without FastAPI or a browser.

4. **Provider interface**: A simple abstract class with `generate(prompt, system_prompt, history) -> str`. Each provider (OpenAI, Anthropic, Ollama) implements this. The engine doesn't know about specific providers.

5. **Separation of concerns**:
   - Engine knows nothing about HTTP, WebSocket, or UI.
   - API layer translates between HTTP requests and engine calls.
   - Export layer consumes structured `RunResult` objects, not raw engine internals.
   - Config layer validates and provides defaults independently of the engine.
