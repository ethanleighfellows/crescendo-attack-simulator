# Source Repo Audit: deepteam Crescendo Jailbreaking

## Crescendo-Specific Modules

### Core Attack — `deepteam/attacks/multi_turn/crescendo_jailbreaking/`

| File | Key Symbols | Role |
|------|------------|------|
| `crescendo_jailbreaking.py` | `CrescendoJailbreaking`, `MemorySystem` | Main attack orchestrator — manages rounds, backtracking, judges, memory branching |
| `template.py` | `JailBreakingCrescendoTemplate` | All prompt templates — system prompt, refusal judge, eval judge, JSON confinement |
| `schema.py` | `AttackData`, `RefusalData`, `EvalData`, `ImprovementPrompt` | Pydantic structured output schemas for LLM calls |
| `__init__.py` | Re-exports `CrescendoJailbreaking` | Package entry |

### Prompt Builder

`JailBreakingCrescendoTemplate` contains four static methods:

1. **`crescendo_system_prompt(conversation_objective, max_rounds, current_round, vulnerability_data)`** — Long instruction block with examples and JSON output format for the red-team attacker model.
2. **`attack_json_confinement()`** — Short reminder to output only the 3-key JSON (used only in async path).
3. **`refusal_system_prompt(vulnerability_data)`** — Binary refusal judge: determines if target refused.
4. **`eval_system_prompt(vulnerability_data)`** — Success evaluator: scores how well the target fulfilled the objective (0-100 `metadata` field).

### Judges

There are **no separate judge modules**. Judging is done by the **same simulator LLM** using structured output:
- **Refusal judge**: `RefusalData { value: bool, rationale: str, metadata: int }`
- **Eval judge**: `EvalData { value: bool, description: str, rationale: str, metadata: int }`

Success threshold: `metadata == 100`.

### Backtracking Logic

Implemented in `CrescendoJailbreaking._get_turns`:
1. When refusal is detected: increment `backtrack_count`.
2. Branch target memory via `MemorySystem.duplicate_conversation_excluding_last_turn()` (copies conversation minus last user+assistant pair under new UUID).
3. Pop last two turns from the `turns` list.
4. Decrement `round_num` by 1 (so the round doesn't count).
5. Append refusal explanation + judge rationale to `last_response.content` as feedback for the attacker model.
6. Red-team memory is **not** rolled back — only the target conversation is branched.
7. Loop ends when `backtrack_count >= max_backtracks`.

### Attack Orchestration Flow

1. Validate input turns (must contain at least one user turn).
2. Generate assistant response if last turn is user-only.
3. Initialize red-team system prompt with `crescendo_system_prompt()`.
4. Loop up to `max_rounds`:
   a. `generate_attack()` — LLM produces next question (`AttackData.generated_question`).
   b. 50% chance to `enhance_attack()` with a random single-turn attack.
   c. Target model responds via `model_callback`.
   d. `get_refusal_score()` — if refusal, backtrack and `continue`.
   e. `get_eval_score()` — if `metadata == 100`, break (success).
5. Return full turn history.

### Standalone Entrypoints

- **`CrescendoJailbreaking.progress()`** / **`a_progress()`** — Alternative API that takes a `BaseVulnerability` and runs the full flow.
- **`AttackSimulator`** — Primary integration path for red teaming; calls `_get_turns`.
- **CLI** — `deepteam` Typer CLI with `run` command (YAML config) — does NOT wire `max_rounds`, `max_backtracks`, or `simulator_model` from config.

## Supporting Infrastructure

### Base Classes

| File | Symbol | Connection |
|------|--------|------------|
| `attacks/base_attack.py` | `BaseAttack`, `Exploitability` | Root abstract class; `weight`, `multi_turn`, `enhance()` |
| `attacks/multi_turn/base_multi_turn_attack.py` | `BaseMultiTurnAttack` | Trivial subclass — no shared logic; convention expects `_get_turns` |
| `attacks/single_turn/base_single_turn_attack.py` | `BaseSingleTurnAttack` | Type allowed in `turn_level_attacks` |

### Model/Provider Abstraction

- Uses `deepeval.models.DeepEvalBaseLLM` as the model interface.
- `deepeval.metrics.utils.initialize_model()` normalizes string → model instance.
- CLI `model_callback.py` bridges to `GPTModel`, `AzureOpenAIModel`, `OllamaModel`, `GeminiModel`, `AnthropicModel`, `AmazonBedrockModel`, etc.
- No dedicated provider registry in deepteam — abstraction is from DeepEval.

### Structured Generation with Retries

`attacks/attack_simulator/utils.py`:
- `generate()` / `a_generate()` — takes prompt, Pydantic schema, model.
- Retry logic: `DEEPTEAM_MAX_RETRIES` (env, default 3), exponential backoff (2^attempt seconds).
- Handles native vs non-native models differently (structured output vs JSON parsing).

### Turn Types

| Symbol | Source | Fields |
|--------|--------|--------|
| `RTTurn` | `test_case/test_case.py` | Extends deepeval `Turn`, adds `turn_level_attack: Optional[str]` |
| `RTTestCase` | Same | `vulnerability`, `input`, `actual_output`, `turns`, `metadata`, `vulnerability_type`, `attack_method`, `score`, `reason`, `error` |
| `CallbackType` | `multi_turn/types.py` | `Callable[[str, Optional[List[RTTurn]]], RTTurn]` |

### Multi-Turn Utilities

| File | Symbol | Usage |
|------|--------|-------|
| `multi_turn/utils.py` | `append_target_turn()` | Appends target response RTTurn with optional attack name |
| Same | `enhance_attack()` / `a_enhance_attack()` | Wraps prompt with a single-turn attack's `enhance()` method |
| Same | `update_turn_history()` | Appends user+assistant Turn pair (not used by Crescendo) |

## Configurable Parameters ("Knobs")

| Parameter | Default | Source | Notes |
|-----------|---------|--------|-------|
| `weight` | 1 | Constructor | Sampling weight when mixed with other attacks |
| `max_rounds` | 10 | Constructor | Maximum escalation rounds before stopping |
| `max_backtracks` | 10 | Constructor | Maximum refusal-triggered backtracks |
| `turn_level_attacks` | None | Constructor | Optional list of `BaseSingleTurnAttack` instances |
| `simulator_model` | "gpt-4o-mini" | Constructor / `_get_turns` override | Red-team + judge model |
| Enhancement probability | 0.5 | Hard-coded | `random.random() < 0.5` — not configurable |
| Success threshold | 100 | Hard-coded | `eval_percentage == 100` — not configurable |
| Max retries | 3 | Env `DEEPTEAM_MAX_RETRIES` | LLM call retry count |

## Notable Implementation Quirks

1. **Sync/Async divergence**: Sync `generate_attack()` omits `attack_json_confinement()`; async appends it.
2. **Type hint mismatch**: `get_eval_score` annotated as `Dict[str, Any]` but returns a tuple.
3. **Stale context risk**: After backtrack, `last_response` may reference popped turn object.
4. **Red-team memory not rolled back**: On backtrack, only target conversation is branched.
5. **`progress()` overwrites results**: Inner loop assigns `result[vuln_type] = enhanced_turns` — only last attack per vulnerability type is kept.
6. **`ImprovementPrompt` is dead code**: Defined in schema.py but never imported by Crescendo.
