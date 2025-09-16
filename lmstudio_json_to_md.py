import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

def format_datetime(timestamp_ms):
    """Convert LM Studio ms timestamp to readable string."""
    if timestamp_ms:
        return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"

def format_date(timestamp_ms):
    """Convert LM Studio ms timestamp to YYYY-MM-DD in America/Denver."""
    if timestamp_ms:
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=ZoneInfo("America/Denver")).date().isoformat()
    return "N/A"

def sanitize_filename(title):
    """Make safe filenames."""
    return "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in title).strip().replace(" ", "_")

def _split_think_tags(text):
    """Extract reasoning inside <think>...</think> tags and visible text."""
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if match:
        reasoning = match.group(1).strip()
        visible = (text[:match.start()] + text[match.end():]).strip()
        return reasoning, visible
    else:
        return None, text

def _extract_texts_from_version(version):
    """Extract visible texts and thoughts from a version dict."""
    visible_texts = []
    thoughts = []

    version_type = version.get("type")
    if version_type == "singleStep":
        blocks = version.get("content", [])
        for block in blocks:
            if block.get("type") == "text":
                reasoning, visible = _split_think_tags(block.get("text", ""))
                if reasoning:
                    thoughts.append(reasoning)
                if visible:
                    visible_texts.append(visible)
    elif version_type == "multiStep":
        steps = version.get("steps", [])
        for step in steps:
            for block in step.get("content", []):
                if block.get("type") == "text":
                    reasoning, visible = _split_think_tags(block.get("text", ""))
                    if reasoning:
                        thoughts.append(reasoning)
                    if visible:
                        visible_texts.append(visible)
    # Also check for reasoning_content at top level of version
    reasoning_content = version.get("reasoning_content")
    if reasoning_content:
        thoughts.append(reasoning_content.strip())

    return visible_texts, thoughts

def extract_model_id(conversation):
    """Best-effort extraction of model id from conversation JSON."""
    # Prefer root-level lastUsedModel if present
    last_used = conversation.get("lastUsedModel", {}) or {}
    model = last_used.get("indexedModelIdentifier") or last_used.get("identifier")
    if model:
        return model
    # Fallback: scan messages/versions/steps for genInfo.indexedModelIdentifier
    for msg in conversation.get("messages", []):
        for ver in msg.get("versions", []):
            # Directly on version, if present
            gen = ver.get("genInfo", {})
            if isinstance(gen, dict) and gen.get("indexedModelIdentifier"):
                return gen["indexedModelIdentifier"]
            # Inside multiStep steps
            if ver.get("type") == "multiStep":
                for step in ver.get("steps", []):
                    gen = step.get("genInfo", {})
                    if isinstance(gen, dict) and gen.get("indexedModelIdentifier"):
                        return gen["indexedModelIdentifier"]
    return None

def conversation_to_markdown(conversation, conversation_id=None):
    """Convert a single LM Studio conversation dict to Markdown text."""
    title = conversation.get("name", "Untitled")
    created = format_datetime(conversation.get("createdAt"))
    tokens = conversation.get("tokenCount", "N/A")

    model_id = extract_model_id(conversation)
    published = datetime.now(ZoneInfo("America/Denver")).date().isoformat()

    # YAML frontmatter
    md = ["---"]
    md.append(f'title: "{title}"')
    if model_id:
        md.append(f"Model: {model_id}")
    md.append('author: "LM Studio Chat to Markdown Converter"')
    md.append(f"published: {published}")
    md.append(f'created: "{created}"')
    if conversation_id is not None:
        md.append(f"id: {conversation_id}")
    # tokens as number when possible
    tokens_val = conversation.get("tokenCount", "N/A")
    if isinstance(tokens_val, int):
        md.append(f"tokens: {tokens_val}")
    elif isinstance(tokens_val, str) and tokens_val.isdigit():
        md.append(f"tokens: {int(tokens_val)}")
    else:
        md.append(f"tokens: {tokens}")
    # description and tags
    if model_id:
        md.append(f'description: "Talk with {model_id}"')
    else:
        md.append('description: "LM Studio conversation"')
    md.append("tags:")
    md.append('  - "LM-Studio"')
    md.extend(["---", ""])

    # Messages
    for message in conversation.get("messages", []):
        versions = message.get("versions", [])
        if versions:
            sel = message.get("currentlySelected")
            if isinstance(sel, int) and 0 <= sel < len(versions):
                version = versions[sel]
            else:
                version = versions[0]
            role = version.get("role", "unknown").capitalize()
            visible_texts, thoughts = _extract_texts_from_version(version)
            if visible_texts:
                md.append(f"**{role}:**")
                md.append("\n".join(visible_texts))
                if thoughts:
                    md.append("")
                    md.append("<details><summary>thinking</summary>")
                    md.append("")
                    md.append("```")
                    md.append("\n".join(thoughts))
                    md.append("```")
                    md.append("</details>")
                md.append("")  # blank line for spacing

    return "\n".join(md)

if __name__ == "__main__":
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir("."):
        if filename.endswith(".conversation.json"):
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            prefix = filename.rsplit(".conversation.json", 1)[0]
            conversation_id = int(prefix) if prefix.isdigit() else None
            print(f"Processing: {filename}  (id={conversation_id})")
            if conversation_id is None:
                print("⚠️  No numeric ID parsed; `id` will be omitted from frontmatter.")

            if isinstance(data, dict) and "messages" in data:
                conversations = [data]
            elif isinstance(data, list):
                conversations = data
            else:
                raise ValueError(f"Unexpected LM Studio JSON format in file {filename}")

            for conversation in conversations:
                title = conversation.get("name", "Untitled")
                safe_title = sanitize_filename(title)
                if conversation_id is not None:
                    md_filename = f"{safe_title}_{conversation_id}.md"
                else:
                    md_filename = f"{safe_title}.md"
                filepath = os.path.join(output_dir, md_filename)
                print(f"→ Writing: {filepath}")

                md_text = conversation_to_markdown(conversation, conversation_id=conversation_id)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(md_text)
                print(f"✅ Wrote {filepath}")