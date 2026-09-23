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

async def handle_ask_pro(request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    prompt = body.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "Missing 'prompt'"}, status_code=400)
    output, usage = await run_agy_full_turn(prompt, "gemini-3.1-pro-high")
    return JSONResponse({"response": output, "model": "gemini-3.1-pro-high", "usage": usage})

async def handle_ask_flash(request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    prompt = body.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "Missing 'prompt'"}, status_code=400)
    output, usage = await run_agy_full_turn(prompt, "gemini-3.8-flash-high")
    return JSONResponse({"response": output, "model": "gemini-3.8-flash-high", "usage": usage})

async def handle_vision(request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    image_path = body.get("image_path", "").replace("\\", "/")
    question = body.get("question", "Analyze this image in detail and describe everything visible.")
    if not image_path:
        return JSONResponse({"error": "Missing 'image_path'"}, status_code=400)
    instruction = f"Please inspect the image file at `{image_path}` using view_file.\nUser question / instruction: {question}"
    output, usage = await run_agy_full_turn(instruction, "gemini-3.8-flash-high")
    return JSONResponse({"analysis": output, "image_path": image_path, "usage": usage})

async def handle_read_document(request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
    file_path = body.get("file_path", "").replace("\\", "/")
    question = body.get("question", "Summarize the key information and extract the most relevant details.")
    if not file_path:
        return JSONResponse({"error": "Missing 'file_path'"}, status_code=400)
    instruction = f"Please inspect the document file at `{file_path}` using view_file.\nUser question / instruction: {question}"
    output, usage = await run_agy_full_turn(instruction, "gemini-3.1-pro-high")
    return JSONResponse({"summary": output, "file_path": file_path, "usage": usage})

async def generate_imagen_file(prompt: str, aspect_ratio: str = "1:1", image_name: str = "image") -> Tuple[Optional[str], str]:
    """Generates an image via agy.exe native Google Imagen tool and returns (file_path, raw_output)."""
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', image_name).strip('_')[:20] or "image"
    valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]
    ratio = aspect_ratio if aspect_ratio in valid_ratios else "1:1"

    instruction = (
        f"Please use the generate_image tool to generate an image with:\n"
        f"Prompt: '{prompt}'\n"
        f"ImageName: '{clean_name}'\n"
        f"AspectRatio: '{ratio}'\n"
        f"Once generated, report the exact file path where it was saved."
    )

    raw_output, _ = await run_agy_full_turn(instruction, "gemini-3.8-flash-high")

    # 1. Regex find absolute path in output
    match = re.search(r'([A-Za-z]:\\[^`\r\n]+\.jpg)', raw_output)
    if match and os.path.exists(match.group(1)):
        return match.group(1), raw_output

    # 2. Fallback: inspect brain directories for recently created .jpg
    try:
        for base in [r"C:\Users\danom\.gemini\antigravity-cli\brain", r"C:\Users\danom\.gemini\antigravity\brain"]:
            if not os.path.exists(base):
                continue
            latest_file = None
            latest_time = 0
            for root, dirs, files in os.walk(base):
                for f in files:
                    if f.endswith(".jpg"):
                        fp = os.path.join(root, f)
                        try:
                            t = os.path.getmtime(fp)
                            if t > latest_time:
                                latest_time = t
                                latest_file = fp
                        except Exception:
                            pass
            if latest_file and (time.time() - latest_time) < 120:
                return latest_file, raw_output
    except Exception:
        pass

    return None, raw_output

async def handle_image_generations(request):
    """OpenAI-compatible /v1/images/generations endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": {"message": "Invalid JSON body", "type": "invalid_request_error"}}, status_code=400)

    prompt = body.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": {"message": "Missing required field 'prompt'", "type": "invalid_request_error"}}, status_code=400)

    size = str(body.get("size", "1024x1024")).lower()
    response_format = body.get("response_format", "url")

    # Map size to aspect ratio
    if "1792" in size or "1920" in size or "16:9" in size:
        aspect_ratio = "16:9"
    elif "1080" in size or "9:16" in size:
        aspect_ratio = "9:16"
    elif "4:3" in size:
        aspect_ratio = "4:3"
    elif "3:4" in size:
        aspect_ratio = "3:4"
    elif "3:2" in size:
        aspect_ratio = "3:2"
    elif "2:3" in size:
        aspect_ratio = "2:3"
    else:
        aspect_ratio = "1:1"

    file_path, raw_out = await generate_imagen_file(prompt, aspect_ratio=aspect_ratio, image_name="img")

    if not file_path or not os.path.exists(file_path):
        return JSONResponse({
            "error": {
                "message": f"Image generation failed: {raw_out}",
                "type": "api_error"
            }
        }, status_code=500)

    created_time = int(time.time())
    norm_url = "file:///" + file_path.replace("\\", "/")
    img_data = {
        "url": norm_url,
        "revised_prompt": prompt,
        "file_path": file_path.replace("\\", "/")
    }

    if response_format == "b64_json":
        import base64
        with open(file_path, "rb") as f:
            img_data["b64_json"] = base64.b64encode(f.read()).decode("utf-8")

    return JSONResponse({
        "created": created_time,
        "data": [img_data]
    })

async def handle_generate_image(request):
    """Direct JSON image generation endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    prompt = body.get("prompt", "")
    aspect_ratio = body.get("aspect_ratio", "1:1")
    image_name = body.get("image_name", "generated_image")
    if not prompt:
        return JSONResponse({"error": "Missing 'prompt'"}, status_code=400)

    file_path, raw_out = await generate_imagen_file(prompt, aspect_ratio=aspect_ratio, image_name=image_name)
    if not file_path:
        return JSONResponse({"error": "Image generation failed", "details": raw_out}, status_code=500)

    norm_path = file_path.replace("\\", "/")
    return JSONResponse({
        "status": "success",
        "file_path": norm_path,
        "url": f"file:///{norm_path}",
        "raw_response": raw_out
    })

async def handle_openapi(request):
    schema = {
        "openapi": "3.0.1",
        "info": {
            "title": "Gemini Subscription Bridge for ChatGPT & External Agents",
            "description": "Exposes Google Gemini 3.1 Pro, Flash, Vision, and 2M Document Reading to ChatGPT and external tools with zero extra API costs.",
            "version": "1.0.0"
        },
        "servers": [{"url": "http://127.0.0.1:8000"}],
        "paths": {
            "/v1/ask_pro": {
                "post": {
                    "summary": "Ask Gemini 3.1 Pro for deep reasoning, proofs, or complex advice",
                    "operationId": "askGeminiPro",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"prompt": {"type": "string", "description": "The prompt or question to solve"}},
                                    "required": ["prompt"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Gemini Pro response", "content": {"application/json": {"schema": {"type": "object", "properties": {"response": {"type": "string"}}}}}}
                    }
                }
            },
            "/v1/ask_flash": {
                "post": {
                    "summary": "Ask Gemini 3.8 Flash for fast, low-latency summaries and extraction",
                    "operationId": "askGeminiFlash",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"prompt": {"type": "string"}},
                                    "required": ["prompt"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Gemini Flash response", "content": {"application/json": {"schema": {"type": "object", "properties": {"response": {"type": "string"}}}}}}
                    }
                }
            },
            "/v1/vision": {
                "post": {
                    "summary": "Inspect and analyze an image or screenshot using Gemini Multimodal Vision",
                    "operationId": "geminiVision",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "image_path": {"type": "string", "description": "Local absolute file path to the image"},
                                        "question": {"type": "string", "description": "Specific question or analysis request"}
                                    },
                                    "required": ["image_path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Gemini Vision analysis", "content": {"application/json": {"schema": {"type": "object", "properties": {"analysis": {"type": "string"}}}}}}
                    }
                }
            },
            "/v1/read_document": {
                "post": {
                    "summary": "Read and analyze massive documents/codebases using Gemini 2M context window",
                    "operationId": "geminiReadDocument",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string", "description": "Local absolute file path to the document/file"},
                                        "question": {"type": "string", "description": "Specific question or summary goal"}
                                    },
                                    "required": ["file_path"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Gemini Document Summary", "content": {"application/json": {"schema": {"type": "object", "properties": {"summary": {"type": "string"}}}}}}
                    }
                }
            },
            "/v1/images/generations": {
                "post": {
                    "summary": "Generate high-resolution photorealistic images using Google Imagen via active subscription",
                    "operationId": "generateImageOpenAI",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {"type": "string", "description": "Visual prompt describing the image to generate"},
                                        "size": {"type": "string", "description": "Image dimensions: 1024x1024 (1:1), 1792x1024 (16:9), 1024x1792 (9:16)"},
                                        "response_format": {"type": "string", "description": "url or b64_json"}
                                    },
                                    "required": ["prompt"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "OpenAI-compatible image data", "content": {"application/json": {"schema": {"type": "object", "properties": {"data": {"type": "array"}}}}}}
                    }
                }
            }
        }
    }
    return JSONResponse(schema)

async def handle_health(request):
    return JSONResponse({
        "status": "online",
        "service": "Gemini Hermes Bridge",
        "active_models": AVAILABLE_MODELS,
        "aliases": MODEL_ALIASES,
        "endpoints": [
            "/v1/chat/completions",
            "/v1/models",
            "/v1/ask_pro",
            "/v1/ask_flash",
            "/v1/vision",
            "/v1/read_document",
            "/v1/images/generations",
            "/v1/generate_image",
            "/openapi.json"
        ]
    })

routes = [
    Route("/", handle_health, methods=["GET"]),
    Route("/health", handle_health, methods=["GET"]),
    Route("/openapi.json", handle_openapi, methods=["GET"]),
    Route("/v1/models", handle_models, methods=["GET"]),
    Route("/models", handle_models, methods=["GET"]),
    Route("/v1/chat/completions", handle_chat_completions, methods=["POST"]),
    Route("/chat/completions", handle_chat_completions, methods=["POST"]),
    Route("/v1/ask_pro", handle_ask_pro, methods=["POST"]),
    Route("/v1/ask_flash", handle_ask_flash, methods=["POST"]),
    Route("/v1/vision", handle_vision, methods=["POST"]),
    Route("/v1/read_document", handle_read_document, methods=["POST"]),
    Route("/v1/images/generations", handle_image_generations, methods=["POST"]),
    Route("/images/generations", handle_image_generations, methods=["POST"]),
    Route("/v1/generate_image", handle_generate_image, methods=["POST"]),
]

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True
    )
]

app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    port = 8000
    print(f"=== Starting Gemini Hermes Bridge on http://127.0.0.1:{port} ===")
    print("Zero Extra Cost: Utilizing active Antigravity/Gemini Subscription")
    print("Models Available:")
    for m in AVAILABLE_MODELS:
        print(f" - {m}")
    print(f"\nReady to accept Hermes, Claude, and external requests at http://127.0.0.1:{port}/v1\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
