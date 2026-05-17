# AI Routing Guide — VSCode
> **Goal:** Use the right AI for each task. Save tokens. Avoid context bloat.

---

## ⚠️ SLASH COMMAND PROTOCOL — ALL AIs MUST FOLLOW THIS

> **This section overrides everything else. No exceptions. No AI is exempt.**

### The Rule

When the user types a slash command, your job is **one step only**:

```
TRIGGER DETECTED → RUN THE PYTHON SCRIPT → REPORT OUTPUT
```

**YOU MUST NOT:**
- Read or open any CSV file yourself
- Interpret, parse, or analyze any CSV content
- Ask the user for information already in the CSV
- Call another AI model to help
- Generate or guess values
- Do anything before running the script

**YOU MUST:**
- Execute the full Python script as written in the skill file
- Report the terminal output exactly as returned
- Only use AI reasoning AFTER the script completes (e.g. Section 1 narrative in `/chiffre`)

---

### Slash Command → Script Mapping

| Command | Skill File | Script Does | AI Step After? |
|---|---|---|---|
| `/chiffre` | `chiffre.md` | Fills Sections 2, 3, 7 from SUC CSVs | ✅ Write Section 1 from `kpis` dict only |
| `/ratios` | `ratios_prioritaires.md` | Fills Section 4 from ratios CSV | ❌ None |
| `/suivi-vendeur` or `/suivi_vendeur` | `suivi_vendeur.md` | Fills Section 5 LS from Suivi CSV | ❌ None |
| `/defectuosite` | `defectuosite.md` | Fills Section 5 Atelier from defect CSV | ❌ None |

**Also triggers `/chiffre`:** "remplis le rapport", "mets à jour les chiffres", "analyse les CSV", "fill the weekly report"

**Auto-chain:** `/chiffre` automatically calls `/ratios` on completion.

---

### Why Python Does Everything

The scripts handle all parsing, formatting, and file writing.
The AI only touches data that the script explicitly hands to it (the `kpis` dict for Section 1).
**Any AI that reads a CSV directly wastes tokens and risks errors.**

---

## General Task Routing

### Quick Reference Table

| Task Type | Best AI | Why |
|---|---|---|
| Code completion / boilerplate | **Codex** | Fastest, lowest cost, inline-optimized |
| Bug fix (isolated, < 50 lines) | **Codex** | No reasoning overhead needed |
| Full function / module writing | **Qwen** | Strong code gen, efficient on mid-size tasks |
| Refactoring / architecture review | **Claude** | Best reasoning + code structure understanding |
| Explain code / write docs | **Claude** | Clear, structured natural language output |
| Long file analysis (> 500 lines) | **Gemini** | Longest context window |
| Research / web-grounded answers | **Gemini** | Native search integration |
| Debugging complex logic | **Claude** | Step-by-step reasoning strength |
| Translation / multilingual code comments | **Qwen** | Multilingual by design |
| Unit test generation | **Qwen** | Reliable pattern-based test scaffolding |
| System design / planning | **Claude** | Best at abstract reasoning and trade-off analysis |
| Data parsing / scripting (Python) | **Qwen** | Efficient on structured, repetitive code tasks |
| Summarize large documents | **Gemini** | Long context, low cost at scale |
| Creative naming / UX copy | **Claude** | Strongest natural language creativity |

### Routing Rules (apply in order)

```
1. Is it a slash command (/chiffre, /ratios, etc.)?     → See Protocol above
2. Is it a < 10 line inline edit or autocomplete?       → Codex
3. Is the input > 500 lines or multiple files?          → Gemini
4. Is it logic-heavy, architectural, or needs explain?  → Claude
5. Is it a standard coding task (test/script/function)? → Qwen
6. Does it need live web data or research?              → Gemini
```

---

## Model Profiles (short)

### ⚡ Codex
- **Use for:** Autocomplete, boilerplate, quick fixes
- **Avoid:** Complex reasoning, long context
- **Token cost:** Lowest

### 🧠 Claude
- **Use for:** Architecture, debugging, documentation, code review
- **Avoid:** Very long files, simple completions
- **Token cost:** Medium–High (but fewer retries needed)

### 🌐 Gemini
- **Use for:** Large file analysis, research, summarization
- **Avoid:** Deep reasoning tasks, slash commands (run the script instead)
- **Token cost:** Low at scale, high context ceiling

### 🐉 Qwen
- **Use for:** Code generation, unit tests, scripts, multilingual tasks
- **Avoid:** Abstract system design
- **Token cost:** Low–Medium

---

## Token-Saving Rules (for all AIs)

- **Slash command = run the script.** Do not load the CSV. Do not think. Run.
- **Trim your prompt.** Remove file sections irrelevant to the task before pasting.
- **One task per prompt.** Don't bundle refactor + test + docs in one request.
- **Use Codex first** for anything that looks like autocomplete. Escalate only if it fails.
- **Give output format.** Say "respond in code only" or "bullet list, max 5 items" to cut fluff.

---

## Example Prompt Prefixes

```
[CODEX]  Complete this function: ...
[QWEN]   Write unit tests for the following class: ...
[GEMINI] Summarize all TODOs across these 3 files: ...
[CLAUDE] Review the architecture of this module and suggest improvements: ...
```

> Tip: Add these tags to your VSCode snippets for fast routing.
