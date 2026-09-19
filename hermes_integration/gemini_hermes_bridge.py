"""
Gemini Hermes Bridge
Bridges your Google Gemini / Antigravity Subscription into Hermes Agent Desktop App
Provides standard OpenAI-compatible endpoints (/v1/chat/completions, /v1/models)
Zero extra cost - runs through your active Antigravity session via stdin NDJSON stream.
"""

import sys
import os
import time
import uuid
import json
import re
import asyncio
from typing import List, Dict, Any, Tuple, Optional

from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
import uvicorn

AGY_PATH = r"C:\Users\danom\AppData\Local\agy\bin\agy.exe"

AVAILABLE_MODELS = [
    "gemini-3.8-flash-high",
    "gemini-3.8-flash-medium",
    "gemini-3.8-flash-low",
    "gemini-3.1-pro-high",
    "gemini-3.1-pro-low",
    "gemini-3.7-flash-high",
    "claude-sonnet-4-6",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium"
]

MODEL_ALIASES = {
    "gemini-3.8-flash": "gemini-3.8-flash-high",
    "gemini-3.8": "gemini-3.8-flash-high",
    "gemini-3.1-pro": "gemini-3.1-pro-high",
    "gemini-3.1": "gemini-3.1-pro-high",
    "gemini-pro": "gemini-3.1-pro-high",
    "gemini-flash": "gemini-3.8-flash-high",
    "gemini-3.7-flash": "gemini-3.7-flash-high",
    "claude-sonnet": "claude-sonnet-4-6",
    "claude-opus": "claude-opus-4-6-thinking",
    "gpt-oss": "gpt-oss-120b-medium",
}

def resolve_model(requested_model: str) -> str:
    """Resolves requested model string to an active Antigravity model."""
    if not requested_model:
        return "gemini-3.8-flash-high"
    req = requested_model.strip().lower()
    if req in AVAILABLE_MODELS:
        return req
    for alias, target in MODEL_ALIASES.items():
        if alias in req:
            return target
    if "pro" in req:
        return "gemini-3.1-pro-high"
    return "gemini-3.8-flash-high"

def extract_message_text(content: Any) -> str:
    """Handles both string content and OpenAI multi-part content arrays."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    parts.append("[Attached Image]")
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content or "")

def format_messages_to_prompt(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """Formats OpenAI messages and optional tool definitions into a single clean prompt."""
    prompt_sections = []

    if tools:
        tool_desc = ["You have access to the following tools:"]
        for t in tools:
            fn = t.get("function", {})
            name = fn.get("name", "unknown")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})
            tool_desc.append(f"- {name}: {desc}\n  Parameters: {json.dumps(params)}")
        tool_desc.append("\nTo call a tool, format your response using this tag:")
        tool_desc.append('<tool_call>\n{"name": "tool_name", "arguments": { ... }}\n</tool_call>')
        prompt_sections.append("[AVAILABLE TOOLS]\n" + "\n".join(tool_desc) + "\n")

    for msg in messages:
        role = msg.get("role", "user").upper()
        content = extract_message_text(msg.get("content", ""))
        
        # Check for assistant tool calls in history
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            tc_str = []
            for tc in tool_calls:
                fn = tc.get("function", {})
                tc_str.append(f"<tool_call>\n{json.dumps({'name': fn.get('name'), 'arguments': fn.get('arguments')})}\n</tool_call>")
            content = (content + "\n" if content else "") + "\n".join(tc_str)

        # Check for tool results
        if role == "TOOL":
            tool_id = msg.get("tool_call_id", "")
            name = msg.get("name", "")
            prompt_sections.append(f"[TOOL RESULT ({name} id={tool_id})]\n{content}\n")
        else:
            prompt_sections.append(f"[{role}]\n{content}\n")

    return "\n".join(prompt_sections)

def parse_tool_calls(text: str) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
    """Detects and parses XML tool_call blocks in model output."""
    pattern = r'<tool_call>\s*({.*?})\s*</tool_call>'
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return text, None

    tool_calls = []
    for match in matches:
        try:
            parsed = json.loads(match)
            name = parsed.get("name")
            args = parsed.get("arguments", {})
            args_str = json.dumps(args) if isinstance(args, dict) else str(args)
            tool_calls.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": args_str
                }
            })
        except Exception:
            continue

    # Remove tool call tags from visible text
    clean_text = re.sub(pattern, '', text, flags=re.DOTALL).strip()
    return clean_text or None, tool_calls if tool_calls else None

async def handle_models(request):
    """Returns available models in OpenAI-compatible schema."""
    data = []
    for m in AVAILABLE_MODELS:
        data.append({
            "id": m,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "google-antigravity"
        })
    # Add friendly aliases
    for alias in MODEL_ALIASES.keys():
        data.append({
            "id": alias,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "google-antigravity-alias"
        })
    return JSONResponse({"object": "list", "data": data})

async def run_agy_full_turn(prompt: str, target_model: str) -> Tuple[str, Dict[str, int]]:
    """Runs agy.exe via stdin NDJSON and collects final response instantly on result event."""
    payload = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"

    cmd = [
        AGY_PATH,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--model", target_model,
        "--dangerously-skip-permissions",
        "--disable-slash-commands"
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    proc.stdin.write(payload.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    full_response = ""
    usage = {
        "prompt_tokens": len(prompt) // 4,
        "completion_tokens": 0,
        "total_tokens": len(prompt) // 4
    }

    while True:
        line_bytes = await proc.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
            if evt.get("event") == "result":
                res = evt.get("result", {})
                full_response = res.get("response", "")
                u = res.get("usage", {})
                if u:
                    usage = {
                        "prompt_tokens": u.get("input_tokens", len(prompt) // 4),
                        "completion_tokens": u.get("output_tokens", len(full_response) // 4),
                        "total_tokens": u.get("total_tokens", (len(prompt) + len(full_response)) // 4)
                    }
                break
        except Exception:
            pass

    try:
        proc.kill()
    except Exception:
        pass

    return full_response.strip(), usage

async def handle_chat_completions(request):
    """OpenAI-compatible /v1/chat/completions endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    raw_model = body.get("model", "gemini-3.8-flash-high")
    model = resolve_model(raw_model)
    messages = body.get("messages", [])
    tools = body.get("tools", None)
    stream = body.get("stream", False)

    prompt = format_messages_to_prompt(messages, tools)
    cmpl_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_time = int(time.time())

    if stream:
        async def event_generator():
            payload = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
            cmd = [
                AGY_PATH,
                "--input-format", "stream-json",
                "--output-format", "stream-json",
                "--model", model,
                "--dangerously-skip-permissions",
                "--disable-slash-commands"
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            proc.stdin.write(payload.encode("utf-8"))
            await proc.stdin.drain()
            proc.stdin.close()

            accumulated_text = ""
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if evt.get("event") == "step_update":
                        delta = evt.get("step_update", {}).get("text_delta", "")
                        if delta:
                            accumulated_text += delta
                            chunk_data = {
                                "id": cmpl_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": delta},
                                    "finish_reason": None
                                }]
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                    elif evt.get("event") == "result":
                        break
                except Exception:
                    continue

            try:
                proc.kill()
            except Exception:
                pass

            final_data = {
                "id": cmpl_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    else:
        output, usage = await run_agy_full_turn(prompt, model)
        clean_content, tool_calls = parse_tool_calls(output)

        message_obj = {"role": "assistant"}
        if clean_content:
            message_obj["content"] = clean_content
        else:
            message_obj["content"] = None

        finish_reason = "stop"
        if tool_calls:
            message_obj["tool_calls"] = tool_calls
            finish_reason = "tool_calls"

        response_payload = {
            "id": cmpl_id,
            "object": "chat.completion",
            "created": created_time,
            "model": model,
            "choices": [{
                "index": 0,
                "message": message_obj,
                "finish_reason": finish_reason
            }],
            "usage": usage
        }
        return JSONResponse(response_payload)

async def handle_health(request):
    return JSONResponse({
        "status": "online",
        "service": "Gemini Hermes Bridge",
        "active_models": AVAILABLE_MODELS,
        "aliases": MODEL_ALIASES
    })

routes = [
    Route("/", handle_health, methods=["GET"]),
    Route("/health", handle_health, methods=["GET"]),
    Route("/v1/models", handle_models, methods=["GET"]),
    Route("/models", handle_models, methods=["GET"]),
    Route("/v1/chat/completions", handle_chat_completions, methods=["POST"]),
    Route("/chat/completions", handle_chat_completions, methods=["POST"]),
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    port = 8000
    print(f"=== Starting Gemini Hermes Bridge on http://127.0.0.1:{port} ===")
    print("Zero Extra Cost: Utilizing active Antigravity/Gemini Subscription")
    print("Models Available:")
    for m in AVAILABLE_MODELS:
        print(f" - {m}")
    print(f"\nReady to accept Hermes requests at http://127.0.0.1:{port}/v1\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
