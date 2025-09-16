# LM Studio Chat to Markdown Converter

A Python script that converts LM Studio conversation JSON files into an HTML file showing a chat like interface. I am not going to lie, this is all AI slop, but it does work!

## Description and Features

This script transforms conversation data stored in JSON format (from LM Studio) into a Markdown formatted document that displays the conversation as a chat conversation interface. The output includes YAML frontmatter for use with Obsidian.md and other markdown rendering systems that can take advantage for frontmatter. This will help if you are an Obsidian Bases user. 


## Usage
python3 lmstudio_json_to_md.py [].conversation.json

## Input Format

The script expects a JSON file with the following structure:
- `name`: Conversation name
- `createdAt`: Timestamp of conversation creation
- `tokenCount`: Total tokens in conversation
- `systemPrompt`: System prompt used
- `messages`: Array of message objects with:
  - `versions`: Message versions with content, timestamps, and metadata
  - `role`: Either "user" or "assistant"
  - `content`: Text content of the message
  - For assistant messages: Additional fields like `steps`, `genInfo`, `tool_calls`

## Output

The script generates a complete HTML file with:
- Conversation header showing name, creation date, and token count
- Color-coded user/assistant messages
- Detailed thinking process sections
- Model generation statistics
- Tool call information
- Timestamps for all messages
- Responsive layout that works on desktop and mobile

## Requirements

- Python 3.x
- JSON module (built-in)
- datetime module (built-in)
- os module (built-in)
- re module (built-in)

# LM Studio Chat → Markdown Converter

A small Python utility that converts **LM Studio** `.conversation.json` files directly into **clean Markdown** with YAML frontmatter. It supports thinking-model logs, multiple message structures, and batch conversion. Optional integrations let you produce HTML (via a companion repo) or other formats (via Pandoc).

---

## What this tool does

- **JSON → Markdown :** Parses LM Studio conversation JSON and writes Markdown with YAML frontmatter.
- **YAML frontmatter:**  
  - `title`, `created` (quoted `YYYY-MM-DD HH:MM:SS`), `published` (date of conversion),  
    `id` (from filename prefix like `1757985544936.conversation.json`),  
    `Model` (e.g. `Qwen/Qwen3-30B-A3B-MLX-bf16`),  
    `tokens`, `description`, `tags` (includes `"LM-Studio"`).
- **Thinking models supported:** Extracts `<think>…</think>` and `reasoning_content`. Reasoning is folded into a collapsible `<details>` block under each assistant message.
- **Message structures:** Handles both `singleStep` and `multiStep` assistant outputs; respects `currentlySelected` version per message.
- **Batch-friendly:** Processes all `*.conversation.json` files in the working directory.  
- **Deterministic filenames:** Outputs `output/<Sanitized_Title>_<id>.md` when the numeric ID is present; otherwise `output/<Sanitized_Title>.md`.
- **Helpful logs:** Prints which files are processed and where the Markdown was written.

---

## Requirements

- Python **3.9+** (uses the standard library only; `zoneinfo` is built-in on 3.9+).  
- (Optional) **Pandoc** for converting Markdown to PDF/HTML/etc.  
  - macOS: `brew install pandoc`

---

## Quick start

1) Place your LM Studio files (e.g. `1757985544936.conversation.json`) in this folder.  
2) Run:
```sh
python3 lmstudio_json_to_md.py
```
3) Find results in the `output/` directory, e.g.:
```
output/Capital_of_France_1757985544936.md
```

---

## Input format (LM Studio)

The script expects a structure like:
- `name` — conversation title  
- `createdAt` — epoch ms  
- `tokenCount` — integer  
- `lastUsedModel.indexedModelIdentifier` (preferred) or nested `genInfo.indexedModelIdentifier`  
- `messages[]` — each message has
  - `versions[]` — take `currentlySelected` when present
    - `type` — `"singleStep"` or `"multiStep"`
    - `content[]` blocks (user/assistant text)
    - for `"multiStep"`: `steps[]` with `content[]` blocks
    - optional `reasoning_content`

> Note: JSON schemas can vary between LM Studio versions; this script includes fallbacks.

---

## Output format (Markdown)

**YAML frontmatter** at the top:
```yaml
---
title: "Capital of France"
Model: Qwen/Qwen3-30B-A3B-MLX-bf16
author: "LM Studio Chat to Markdown Converter"
published: 2025-09-16
created: "2025-09-15 10:41:06"
id: 1757985544936
tokens: 33
description: "Talk with Qwen/Qwen3-30B-A3B-MLX-bf16"
tags:
  - "LM-Studio"
---
```

**Transcript body**:
```
**User:**
What is the capital of France?

**Assistant:**
The capital of France is **Paris**.

<details><summary>thinking</summary>

```
...hidden chain-of-thought or reasoning content...
```
</details>
```

---

## Usage notes

- `created` uses the source timestamp; `published` uses the conversion date (America/Denver).
- Reasoning content is preserved only if present (`<think>` tags or `reasoning_content`).
- If a filename lacks a numeric prefix, `id` is omitted from frontmatter and filename.

---

## Sanitizing conversations (privacy & publishing)

**Why**  
LM Studio exports can include internal metadata (system prompts, configs, load parameters, precise timestamps/IDs, model stats) that you may not want to publish. Use `conversation_sanitizer.py` to keep only the essentials.

**What `conversation_sanitizer.py` keeps**
- `name`, `createdAt`, `tokenCount`
- `lastUsedModel.indexedModelIdentifier` (or `identifier` if present)
- `messages` simplified to an array of `{ "role": "...", "text": "..." }`

**What it removes**
- `genInfo`, `stats`, `senderInfo`
- `predictionConfig`, `loadModelConfig`, `perChatPredictionConfig`
- `plugins`, `pluginConfigs`, `disabledPluginTools`
- `systemPrompt`, `preset`, `preprocessed`, `edited`, `debugInfoBlock`
- `stepIdentifier`, `clientInput`, `clientInputFiles`, `userFilesSizeBytes`
- `notes`, `looseFiles`, `pinned`

**How to use**
```bash
# sanitize a single LM Studio export
python3 conversation_sanitizer.py path/to/1757985544936.conversation.json path/to/1757985544936.sanitized.json

# then convert the sanitized file to Markdown (copy or move it into this folder)
cp path/to/1757985544936.sanitized.json .
python3 lmstudio_json_to_md.py
```

**Sanitized JSON output shape**
```json
{
  "name": "...",
  "createdAt": 1757985544937,
  "tokenCount": 33,
  "lastUsedModel": { "indexedModelIdentifier": "Qwen/Qwen3-30B-A3B-MLX-bf16" },
  "messages": [
    { "role": "user", "text": "What is the capital of France?" },
    { "role": "assistant", "text": "The capital of France is **Paris**." }
  ]
}
```

**Notes**
- `createdAt` remains epoch milliseconds; the Markdown converter formats it to `"YYYY-MM-DD HH:MM:SS"` in frontmatter.
- If you prefer not to publish precise times, coarsen `createdAt` to date-only before converting.
- Add raw exports to `.gitignore` and publish only sanitized JSON and generated Markdown.

---

## Roadmap / TODOs

- **Integrate with `lmstudiochatconverter` repo for HTML output.**  
  Use it as an optional path for people who want a stylized chat UI. Our Markdown path remains the default for portability and analytics.
- **Integrate with Pandoc for other output means.**  
  Provide CLI flags to run Pandoc post-processing (Markdown → PDF/HTML/DOCX). Include recommended Pandoc flags and a Lua filter for stripping divs if using the HTML route.
- **MCP server integration.**  
  Connect to or create an MCP server that accepts an LM Studio conversation and returns the chosen target format (Markdown, HTML, PDF). Support batch jobs and simple policies (e.g., include/exclude reasoning).
- **Multiple-model documentation.**  
  Figure out how to document conversations that involve different models across turns. Possible approaches: per-message model tags, section headers by model, or a frontmatter `models: [ ... ]` list.
- **Branching visualization.**  
  Investigate showing branched flows when a conversation forks. Some formats may not support this; however, HTML via `lmstudiochatconverter` could be extended to render branches as a graph/timeline with anchors.
- **CLI polish.**  
  Flags for: input glob, output dir, include/exclude reasoning, timezone override, strict schema mode, and quiescent (no-log) mode.
- **Tests & fixtures.**  
  Add small JSON fixtures for singleStep/multiStep/branched versions and snapshot tests for emitted Markdown.

- **Interactive Chat Interface**: Clean, responsive design that mimics real chat applications
- **Complete Metadata Display**: Shows timestamps, token count, model information, and system prompts
- **Thinking Process Visualization**: Displays AI reasoning steps with clear separation
- **Generation Statistics**: Shows detailed performance metrics including tokens per second, timing information, and token counts
- **Tool Call Integration**: Visualizes any tool calls made during the conversation
- **Responsive Design**: Works well on different screen sizes
- **Customizable Output**: Generates HTML files ready for web viewing

---

## License

MIT