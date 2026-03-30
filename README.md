# Crescendo Attack Simulator

Standalone UI + API app for running multi-turn Crescendo-style attack simulations and exporting run results.

## What is the Crescendo jailbreak?

**Crescendo** is a multi-turn jailbreak against large language models (LLMs). It does not ask for disallowed content in the first message. Instead it **ramps the conversation** from harmless topics toward a prohibited goal. The method was introduced by Microsoft researchers in [*The Crescendo Multi-Turn LLM Jailbreak Attack*](https://arxiv.org/abs/2404.01833) (arXiv:2404.01833, April 2024) and presented at **USENIX Security 2025** ([conference site](https://www.usenix.org/conference/usenixsecurity25)). A [dedicated project page](https://crescendo-the-multiturn-jailbreak.github.io) summarizes the work.

Crescendo leans on two tendencies in chat models: they follow **coherent dialogue**, and they weight **recent text** heavily—**including their own prior outputs**. That lets each turn build on what the model already said.

**Typical attack flow**

1. **Start benign** — Open with a harmless, on-topic question (e.g., history or education) related to the eventual target.
2. **Escalate gradually** — Each later turn references earlier answers and nudges slightly closer to the goal.
3. **Backtrack if refused** — If the model pushes back, soften the prompt and retry from a weaker angle.
4. **Use the model’s words** — Pivot using phrases the model already produced as a foothold for the next step.

In the paper’s setting, jailbreaks often succeed in **fewer than five** interactions, with a **cap of ten** rounds. Because language stays ordinary, the attack can slip past detectors aimed at weird tokens, symbol stuffing, or obvious toxic keywords. It does not require model weights or internals—only **steered conversation**.

**Crescendomation** is an automated form: a **second LLM** writes and refines the escalating prompts. On AdvBench, the authors report large gains over other strong jailbreak baselines—for example roughly **29–61%** on GPT‑4 and **49–71%** on Gemini Pro—and **100%** success on some evaluated tasks (e.g., election misinformation scenarios).

**Models evaluated in the paper** (all reported successfully jailbroken in their experiments) include ChatGPT (GPT‑4), Gemini Pro and Ultra, LLaMA‑2 70B Chat, LLaMA‑3 70B Chat, and Anthropic Claude.

For a security- and mitigations-oriented angle, a **representation-engineering** follow-up ([arXiv:2507.02956](https://arxiv.org/abs/2507.02956)) studies *why* Crescendo works: attacker turns can keep internal activations in a **benign-looking** region of representation space while still steering toward harmful completions.

## Credits

This project is based on and inspired by the Crescendo multi-turn attack implementation in DeepTeam:

- DeepTeam repo: [confident-ai/deepteam](https://github.com/confident-ai/deepteam)
- Crescendo module reference: `deepteam/attacks/multi_turn/crescendo_jailbreaking`

DeepTeam provides the original attack strategy and framework foundations. This repo extracts and packages a focused local simulator workflow.

## What this app does

- Configure and run Crescendo multi-turn attack sessions
- Stream turn-by-turn progress live in the UI
- Support multiple providers (OpenAI, Together, Anthropic, Ollama, Azure-compatible)
- Export run data to XLSX/JSON

## Architecture map

```text
┌──────────────────────────────────────────────────────────────────────┐
│                           Frontend (Vite)                           │
│                   React + TypeScript + Tailwind CSS                 │
│                                                                      │
│  SetupPanel  LiveRunPanel  ReviewPanel  ExportPanel                 │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                     HTTP + WebSocket (/api/*)
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│                        Backend API (FastAPI)                         │
│                                                                      │
│  REST routes: start/pause/resume/cancel/result/export               │
│  WS route: /api/ws/run (streams run_started/turn_completed/etc.)    │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────┐
│                        Crescendo Engine Core                         │
│                                                                      │
│  - Multi-turn escalation loop                                        │
│  - Refusal + eval judging                                            │
│  - Backtracking + memory branching                                   │
│  - Turn transcript normalization                                     │
└───────────────────────┬───────────────────────────────┬──────────────┘
                        │                               │
         ┌──────────────▼──────────────┐   ┌────────────▼──────────────┐
         │      Provider Adapters      │   │      Export Pipeline       │
         │  OpenAI / Together / etc.   │   │   XLSX + JSON generation   │
         └──────────────────────────────┘   └────────────────────────────┘
```

## Tech stack

### Frontend
- **React 19** + **TypeScript** (UI and app state)
- **Vite 6** (dev server and build pipeline)
- **Tailwind CSS** (styling and design system)
- Native browser WebSocket API (live run streaming)

### Backend
- **Python 3** + **FastAPI** (REST + WebSocket API)
- **Uvicorn** (ASGI server)
- **Pydantic / pydantic-settings** (request/response/config validation)
- **python-dotenv** (env loading)

### Model/provider integration
- **OpenAI SDK** (OpenAI/Azure-compatible endpoints)
- **Together AI** via OpenAI-compatible endpoint
- **Anthropic SDK**
- **httpx** for Ollama/local HTTP integrations

### Export + testing
- **openpyxl** (XLSX workbook export)
- **pytest** + **pytest-asyncio** (backend tests)

## Export contents (XLSX)

The XLSX export includes 4 sheets:

1. **Run Summary**  
   Run ID, objective, outcome, total rounds, backtracks, final score, timing.
2. **Configuration**  
   Full run config used for the session.
3. **Full Transcript**  
   Round-by-round attacker prompt + target response.
4. **Per-Turn Outcomes**  
   Refusal/eval decisions and metadata per turn.

## Local setup (copy/paste)

### 1) Clone and enter repo

```bash
git clone https://github.com/ethanleighfellows/crescendo-attack-simulator.git
cd crescendo-attack-simulator
```

### 2) Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` and set at least one provider key:

```bash
OPENAI_API_KEY=...
TOGETHER_API_KEY=...
ANTHROPIC_API_KEY=...
```

Start backend:

```bash
PYTHONPATH=. .venv/bin/python -m uvicorn src.backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 3) Frontend setup (new terminal)

```bash
cd src/frontend
npm install
npm run dev
```

Open:

- UI: <http://localhost:5173>
- API docs: <http://127.0.0.1:8000/docs>

## Quick usage

1. Open the UI.
2. Choose provider/model for simulator + target.
3. Set objective and run parameters.
4. Click **Start Crescendo Run**.
5. Review transcript/results.
6. Export XLSX or JSON.

## Notes

- If a run fails quickly, check backend logs first (auth/model errors are surfaced there and in UI).
- Some Together models require dedicated endpoints and are not serverless-available for all accounts.
- This repo intentionally focuses on Crescendo simulation flow (not the full DeepTeam suite).
