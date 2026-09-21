# KAHNA Security Model

Security is baked into the architecture, ensuring that KAHNA acts safely on the host computer.

## Tool Permission Levels

Every tool registered in the `ToolRegistry` is assigned a `RiskLevel`.

1. **READ_ONLY**: Safe operations that do not modify state (e.g., `get_system_info`, `read_text_file`). Allowed automatically in Phase 1.
2. **LOW**: Minor state changes with negligible impact (e.g., `create_directory`). Allowed automatically in Phase 1.
3. **MEDIUM**: Operations that modify standard files (e.g., `write_text_file`). May require confirmation depending on the directory.
4. **HIGH**: Operations that can delete files or run standard applications. Requires user confirmation.
5. **CRITICAL**: Arbitrary shell execution, modifying system files, installing software. **Explicitly blocked in Phase 1.**

## Guardrails

- **No Arbitrary Shell**: The agent cannot run `subprocess.Popen(llm_generated_string)`. All execution must pass through structured python functions defined as Tools.
- **Environment Driven Secrets**: API keys (OpenRouter, Telegram) are never logged, never returned in API responses, and never hardcoded.
- **Localhost Default**: The FastAPI server binds to `127.0.0.1` preventing external access by default.
- **Iteration Limits**: The Agent Runtime loop has a hard limit (e.g., max 5 iterations) to prevent infinite loops of tool-calling.
