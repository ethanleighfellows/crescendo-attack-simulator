# Theory: Crescendo Jailbreak Generator — Standalone Research Tool

## Problem

LLM red-teaming researchers need a way to generate and inspect Crescendo-style progressive escalation attack transcripts without deploying the full deepteam red-teaming suite. The deepteam framework is powerful but monolithic — its Crescendo implementation is tightly coupled to the vulnerability simulation pipeline, the AttackSimulator orchestrator, and the deepeval model abstraction layer. A researcher who wants to test a single Crescendo attack against a specific model with specific parameters has to navigate a complex dependency graph that includes risk frameworks, metric modules, and CLI infrastructure they don't need.

The structural challenge is extraction without reimplementation. The Crescendo logic is well-defined (progressive escalation, refusal-aware backtracking, dual judging, memory branching), but it's interleaved with framework concerns (progress bars, vulnerability type grouping, model callback conventions, deepeval's structured generation interface).

## Operating Theory

The Crescendo attack works through a feedback loop between three roles: an attacker model that generates progressively escalating questions, a target model that responds, and a judge (same model as attacker) that evaluates each response for refusal and objective fulfillment. The key dynamics are:

1. **Escalation**: The attacker uses a detailed system prompt with worked examples to gradually move from benign to sensitive territory over multiple rounds.
2. **Backtracking**: When the target refuses, the engine forks the target's conversation history (removing the refused exchange) and provides refusal feedback to the attacker, giving it a second chance without the target "remembering" the refused path.
3. **Turn augmentation**: Individual rounds can be optionally wrapped with single-turn attack techniques (base64, leetspeak, etc.) to evade content filters.

The leverage point for a standalone product is that the entire attack loop can be expressed as a pure async generator that takes two LLM providers (simulator and target) and a config, then yields turn-by-turn events. Everything else — the UI, the export, the provider wiring — is a separate concern.

## Strategy

The approach is to build a clean three-layer architecture:

1. **Engine layer** (Python): A standalone `CrescendoEngine` class that faithfully reproduces the source attack loop with no framework dependencies. It takes a `RunConfig` and two `BaseProvider` instances, runs the attack as an async generator, and yields structured `TurnEvent` objects. This makes the core logic testable and reusable.

2. **API layer** (FastAPI): REST endpoints for configuration management and XLSX export, plus a WebSocket endpoint that streams turn events to the UI in real time. The API owns provider construction and run lifecycle management.

3. **GUI layer** (React/TypeScript): A four-phase workflow (Setup → Run → Review → Export) that provides the researcher with full visibility into the attack progression — live transcript streaming, judge decision badges, escalation path visualization, and multi-format export.

The key improvements over the source implementation are: configurable enhancement probability (not hard-coded at 0.5), configurable success threshold (not hard-coded at 100), consistent sync/async behavior (the source diverges on JSON confinement), and a clean provider abstraction that doesn't depend on deepeval's model layer.

## Key Discoveries

The source audit revealed several implementation quirks that informed the standalone design:

- The source's `generate_attack` (sync) omits the `attack_json_confinement()` system message that the async path includes. The standalone engine always includes it for consistency.
- The source's `get_eval_score` is annotated as returning `Dict[str, Any]` but actually returns a tuple `(bool, int)`. The standalone uses properly typed return values.
- After backtracking, the source's `last_response` reference may point to a popped turn object. The standalone captures the response text before any list mutation.
- The source's `progress()` method overwrites results per vulnerability type — only the last attack is kept. The standalone doesn't use this pattern.
- `ImprovementPrompt` in the source schema is dead code, never imported by the Crescendo module.

## Open Questions

- **Provider parity**: The standalone uses direct OpenAI/Anthropic/Ollama clients instead of deepeval's `DeepEvalBaseLLM`. The structured generation behavior (JSON mode vs response_format) may differ subtly for edge-case models. Integration testing against real models will be needed to validate.
- **Turn-level attack fidelity**: The source's `enhance_attack` dispatches to each attack's `enhance()` method, which may use the simulator model internally. The standalone's simpler prefix-based enhancement is an approximation — it may need per-attack specialization if researchers need exact parity.
- **Scalability**: The in-memory run storage in the API layer works for single-user research use but won't scale to concurrent multi-user deployments. A persistence layer (SQLite or similar) would be needed for that.
