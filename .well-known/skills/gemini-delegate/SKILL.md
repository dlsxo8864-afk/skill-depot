---
name: gemini-delegate
description: Delegate substantial foundation implementation, batches of draft files, and repetitive scaffolding to the user's Google CLI bridge to reduce GPT and Claude usage, then review, test, and finish with the main LLM. Use for explicit Gemini delegation or substantial coding foundation work under this user's routing preference.
---

Use the installed `gemini-bridge` MCP server. This user wants Google to handle substantial foundation work and the main desktop LLM to finish. Small edits and simple answers remain direct work.

Send a concrete task with acceptance criteria, a project absolute path, only necessary relative `context_files`, and exact writable `target_files` to `gemini_submit`. Batch related work into one task. Existing targets must be included as context. The bridge accepts text-file generation; it does not run the provider's shell, install project dependencies, delete files, or deploy. Main LLM handles those authorized actions when needed.

Default provider `agy` uses Antigravity CLI, the current Google CLI path for personal free/AI Pro/Ultra accounts. `gemini` is for enterprise Gemini Code Assist. Neither route uses API-key billing. Do not claim one chat equals one quota request or promise a fixed savings percentage.

The job runs asynchronously. Read the returned status and wait between polls. When ready, use `gemini_review`; if truncated, inspect each changed file via its `path` argument. Treat the generated content as a draft and review it within the user's task scope. Then call `gemini_apply`, run meaningful relevant checks, and perform final integration and corrections. Source conflicts block application; resolve based on the current source rather than overwriting it.

Authentication, quota, or service errors stop the Google attempt without retries or automatic provider/API fallback. Explain the specific blocker, continue independent useful work, and leave any Google sign-in to the user. Do not expose credential contents. Only selected files are sent to the provider; never include secrets or full chat history by default.

If MCP has not loaded yet, use the installed CLI at `C:/Users/<사용자>/Documents/Codex/gemini-bridge/bridge_core.py`. Read `C:/Users/<사용자>/Documents/Codex/gemini-bridge/README.ko.md` for command examples and login instructions. MCP registrations are loaded by a new Codex chat or a restarted Claude Desktop.
