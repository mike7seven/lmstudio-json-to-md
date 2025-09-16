# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2025 
import json, sys, copy
from datetime import datetime

KEEP_ROOT = {"name","createdAt","tokenCount","messages","lastUsedModel"}
STRIP_VERSION_KEYS = {
    "genInfo","stats","senderInfo","preprocessed","edited","reasoning_content",
    "defaultShouldIncludeInContext","shouldIncludeInContext"
}
STRIP_MSG_KEYS = {"currentlySelected"}  # keep if you want
STRIP_ROOT = {
    "preset","systemPrompt","plugins","pluginConfigs","disabledPluginTools",
    "perChatPredictionConfig","clientInput","clientInputFiles","userFilesSizeBytes",
    "notes","looseFiles","pinned"
}

def text_blocks_from_version(ver):
    texts = []
    t = ver.get("type")
    if t == "singleStep":
        for b in ver.get("content", []):
            if b.get("type") == "text":
                texts.append(b.get("text",""))
    elif t == "multiStep":
        for step in ver.get("steps", []):
            for b in step.get("content", []):
                if b.get("type") == "text":
                    texts.append(b.get("text",""))
    return "\n".join([t for t in texts if t])

def sanitize(conv):
    out = {k: copy.deepcopy(v) for k,v in conv.items() if k in KEEP_ROOT}
    # simplify lastUsedModel
    lum = out.get("lastUsedModel")
    if isinstance(lum, dict):
        out["lastUsedModel"] = {
            k: lum[k] for k in ("indexedModelIdentifier","identifier") if k in lum
        }

    clean_msgs = []
    for msg in conv.get("messages", []):
        vers = msg.get("versions", [])
        sel = msg.get("currentlySelected", 0)
        if isinstance(sel, int) and 0 <= sel < len(vers):
            v = copy.deepcopy(vers[sel])
        elif vers:
            v = copy.deepcopy(vers[0])
        else:
            continue

        # strip noisy fields on version
        for k in list(v.keys()):
            if k in STRIP_VERSION_KEYS:
                v.pop(k, None)

        role = v.get("role","unknown")
        content_text = text_blocks_from_version(v)
        clean_msgs.append({"role": role, "text": content_text})

    out["messages"] = clean_msgs

    # strip known-noisy top-level keys (if any slipped through)
    for k in STRIP_ROOT:
        out.pop(k, None)

    return out

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace(".json",".sanitized.json")
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    sanitized = sanitize(data)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, ensure_ascii=False, indent=2)
    print(f"wrote {dst}")