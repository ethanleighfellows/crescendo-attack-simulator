# GUI Workflow Specification

## Overview

The GUI follows a four-phase workflow: **Setup → Run → Review → Export**.

## Phase 1: Setup Panel

### Attack Configuration
- **Objective** (required textarea): The target goal for the jailbreak.
- **Vulnerability** (optional select): Dropdown of common vulnerability categories.
- **Vulnerability Type** (optional text): Free-text vulnerability type.
- **Initial Prompt** (optional textarea): Seed prompt; auto-generated from objective if blank.

### Model Configuration
- **Target Provider** (select): OpenAI, Anthropic, Azure, Ollama, Gemini.
- **Target Model** (text): Model ID (e.g., "gpt-4o", "claude-3-sonnet").
- **Target API Key** (password input): Masked; stored in memory only.
- **Target Base URL** (optional text): For self-hosted or Azure endpoints.
- **Simulator Provider** (select): Same options as target.
- **Simulator Model** (text): Default "gpt-4o-mini".
- **Simulator API Key** (password input): Can share with target key.

### Engine Settings
- **Preset** (select): Conservative / Balanced / Aggressive / Custom.
- When preset is selected, auto-fill the fields below. "Custom" enables manual editing.
- **Max Rounds** (number slider): 1-50.
- **Max Backtracks** (number slider): 0-50.
- **Enhancement Probability** (number slider): 0.0-1.0.
- **Success Threshold** (number slider): 1-100.
- **Stop on First Success** (toggle).
- **Turn-Level Attacks** (multi-select chips): base64, leetspeak, rot13, roleplay, etc.

### Actions
- **Start Run** button (primary): Validates config, starts the Crescendo session.
- **Save Config** button (secondary): Save current config as a named preset.
- **Load Config** button (secondary): Load a previously saved config.

## Phase 2: Live Run Panel

### Layout
- **Left column (60%)**: Live transcript view showing conversation turns as they arrive.
- **Right column (40%)**: Run status sidebar.

### Live Transcript View
Each turn rendered as a card:
- **Round indicator**: "Round 3 / 10"
- **User message**: The attacker's generated question (highlighted if enhanced).
- **Assistant response**: The target model's response.
- **Turn-level attack badge**: Shows which attack was applied (if any).
- **Judge outcome badges**: Refusal (red/green) and Eval score (0-100 with color gradient).
- **Backtrack indicator**: Yellow warning banner when backtracking occurs.
- Turns stream in real-time via WebSocket.

### Run Status Sidebar
- **Status**: Running / Paused / Completed / Failed / Cancelled.
- **Current Round**: e.g., "7 / 10".
- **Backtrack Count**: e.g., "2 / 10".
- **Current Strategy**: Escalating / Backing off.
- **Elapsed Time**.
- **Latest Eval Score**: 0-100 gauge/bar.

### Run Controls
- **Pause** button: Pauses after current round completes.
- **Resume** button: Continues from paused state.
- **Cancel** button: Stops the run immediately.
- **Retry** button (visible after completion/failure): Reruns with same config.
- **Rerun with Changes** button: Returns to Setup with current config pre-filled.

## Phase 3: Review Panel

### Summary Header
- **Outcome**: Success / Failure / Max Rounds / Max Backtracks.
- **Total Rounds**: How many rounds were executed.
- **Total Backtracks**: How many times the engine backed off.
- **Final Eval Score**: The last eval judge score.
- **Duration**: Total run time.

### Full Transcript (scrollable)
- Same card layout as live view, but complete and non-streaming.
- Each turn expandable to show full judge rationale and attack metadata.
- Filter/search bar to find specific rounds or keywords.

### Escalation Path Visualization
- Horizontal timeline showing round progression with:
  - Green dots for successful escalation steps.
  - Red dots for refusals/backtracks.
  - Blue dots for enhanced turns.
  - Score progression line chart overlay.

## Phase 4: Export Panel

### Export Formats
- **XLSX** (primary): Multi-sheet workbook.
  - Sheet 1: Run Summary (outcome, config, timing).
  - Sheet 2: Configuration (all parameters).
  - Sheet 3: Full Transcript (one row per turn).
  - Sheet 4: Per-Turn Outcomes (round, backtrack, eval scores).
- **JSON** (secondary): Raw structured data export.
- **CSV** (secondary): Flat transcript export.

### Export Options
- **Include API keys**: Toggle (default off).
- **Redact sensitive content**: Toggle to apply basic redaction to responses.
- **Include judge rationale**: Toggle to include/exclude detailed judge reasoning.
- **Filename**: Auto-generated from objective + timestamp, editable.

### Actions
- **Download XLSX** button (primary).
- **Download JSON** button (secondary).
- **Copy to Clipboard** button: Copies transcript as formatted text.
