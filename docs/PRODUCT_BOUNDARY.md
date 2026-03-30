# Product Boundary: Crescendo Jailbreak Generator

## What Ships

The standalone product ships **only** the Crescendo multi-turn jailbreak generation flow. It is a focused research tool for generating, inspecting, and exporting Crescendo-style progressive escalation attack transcripts against LLMs.

### In Scope

- **Crescendo engine**: Multi-turn progressive escalation with refusal-aware backtracking.
- **Refusal + eval judging**: Binary refusal detection and 0-100 success scoring using the same judge model patterns from the source.
- **Turn-level attack augmentation**: Optional single-turn attack wrappers (base64, leetspeak, ROT13, roleplay, etc.) applied probabilistically per-round.
- **Memory system**: Conversation branching on backtrack (target-side fork, red-team memory continuity).
- **Provider abstraction**: Pluggable LLM backends for both the attacker/judge model and the target model.
- **Configuration presets**: Conservative/balanced/aggressive modes varying escalation depth, backtracking tolerance, and augmentation usage.
- **Transcript capture**: Structured per-turn records with prompt, response, judge outcomes, enhancement applied, timestamps.
- **XLSX export**: Multi-sheet workbook with run summary, configuration, full transcript, and per-turn outcomes.
- **Web GUI**: Setup → Run → Review → Export workflow with live transcript streaming.
- **Safety guardrails**: Research-use warnings, secure key handling, logging controls, optional redaction.

### Out of Scope

- The full deepteam red-teaming suite (vulnerabilities framework, risk assessment, metrics, OWASP/NIST/MITRE frameworks).
- Other multi-turn attacks (Linear, Tree, Sequential, BadLikertJudge).
- Vulnerability simulation and synthetic test case generation.
- The deepteam CLI (`deepteam run`).
- The Confident AI integration.
- Guardrails/guards modules.
- Risk assessment scoring and reporting.

## Core Multi-Turn Behavior Preserved

The product faithfully preserves these Crescendo behaviors from the source:

1. **Progressive escalation**: Red-team model generates strategically escalating questions guided by a detailed system prompt with examples.
2. **Refusal-aware backtracking**: When target refuses, the engine branches the target conversation (minus last exchange), provides refusal feedback to the attacker, decrements the round counter, and retries.
3. **Dual judging**: Separate refusal judge and eval judge calls using structured output schemas.
4. **Turn-level augmentation**: Random application (configurable, not hard-coded at 50%) of single-turn attacks to the generated question.
5. **Memory system**: Separate conversation threads for red-team and target, with target-side forking on backtrack.
6. **Structured LLM calls**: Pydantic schema-validated responses with retry and exponential backoff.

## Improvements Over Source

The standalone product addresses these source quirks:

- **Configurable enhancement probability** (source hard-codes 0.5).
- **Configurable success threshold** (source hard-codes 100).
- **Consistent sync/async behavior** (source diverges on `attack_json_confinement`).
- **Correct type annotations** (source `get_eval_score` returns tuple, annotated as Dict).
- **Non-destructive backtracking** (avoids stale `last_response` reference after pop).
