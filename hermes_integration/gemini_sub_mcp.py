"""
Gemini Subscription MCP Server
Exposes Google Gemini 3.1 Pro & Flash, Multimodal Vision, and 2M-Token Document Reading
as Model Context Protocol (MCP) tools for Claude Desktop, Claude Code, Hermes, and other MCP clients.
Zero Extra API Cost - Powered by your active Google Antigravity / Gemini Subscription.
"""

import sys
import os
import json
import asyncio
import urllib.request
import subprocess
from typing import Optional

from mcp.server.mcpserver import MCPServer

AGY_PATH = r"C:\Users\danom\AppData\Local\agy\bin\agy.exe"
BRIDGE_URL = "http://127.0.0.1:8000/v1/chat/completions"

mcp = MCPServer("gemini-subscription")

async def call_bridge(model: str, content: str) -> str:
    """Calls the local bridge, with automatic fallback to direct agy.exe execution."""
    # Attempt 1: Call local bridge HTTP endpoint
    try:
        req = urllib.request.Request(
            BRIDGE_URL,
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "stream": False
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        # Timeout 90 seconds for deep thinking/reasoning
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception:
        # Fallback to direct agy.exe execution via stdin NDJSON
        pass

    payload = json.dumps({"event": "user", "message": {"content": content}}) + "\n"
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

    full_response = ""
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
                full_response = evt.get("result", {}).get("response", "")
                break
        except Exception:
            pass

    try:
        proc.kill()
    except Exception:
        pass

    return full_response.strip()

@mcp.tool(
    name="ask_gemini_pro",
    description="Consult Google Gemini 3.1 Pro (via your active Antigravity subscription) for deep reasoning, mathematical proofs, alternative approaches, multi-step code planning, or a second opinion. $0 cost."
)
async def ask_gemini_pro(prompt: str) -> str:
    """Consult Gemini 3.1 Pro for deep reasoning and second opinions."""
    return await call_bridge("gemini-3.1-pro-high", prompt)

@mcp.tool(
    name="ask_gemini_flash",
    description="Fast, low-latency task delegation to Google Gemini 3.8 Flash (via your active Antigravity subscription). Best for quick summarization, data extraction, and high-speed batch tasks. $0 cost."
)
async def ask_gemini_flash(prompt: str) -> str:
    """Fast task delegation to Gemini 3.8 Flash."""
    return await call_bridge("gemini-3.8-flash-high", prompt)

@mcp.tool(
    name="gemini_vision",
    description="Inspect and analyze an image file (PNG, JPG, WebP, screenshots, diagrams, UI mockups) using Google Gemini's multimodal vision capabilities. Provide the absolute local file path."
)
async def gemini_vision(image_path: str, question: str = "Analyze this image in detail and describe everything visible.") -> str:
    """Inspect and analyze an image file using Gemini Vision."""
    norm_path = os.path.abspath(image_path).replace("\\", "/")
    if not os.path.exists(norm_path):
        return f"Error: Image file not found at '{norm_path}'"

    instruction = (
        f"Please inspect the image file at `{norm_path}` using view_file.\n"
        f"User question / instruction: {question}"
    )
    return await call_bridge("gemini-3.8-flash-high", instruction)

@mcp.tool(
    name="gemini_audio",
    description="Listen to and analyze an audio file (MP3, WAV, M4A, AAC, FLAC, voice recordings, podcasts, speech, sound effects) using Google Gemini's native audio understanding. Transcribe spoken words, analyze vocal tone/pacing, identify background sounds, or critique audio quality. Provide the absolute local file path."
)
async def gemini_audio(audio_path: str, question: str = "Transcribe and analyze this audio in detail, noting speech, tone, and sound events.") -> str:
    """Listen to and analyze an audio file using Gemini Multimodal Audio."""
    norm_path = os.path.abspath(audio_path).replace("\\", "/")
    if not os.path.exists(norm_path):
        return f"Error: Audio file not found at '{norm_path}'"

    instruction = (
        f"Please inspect and listen to the audio file at `{norm_path}` using view_file.\n"
        f"User question / instruction: {question}"
    )
    return await call_bridge("gemini-3.1-pro-high", instruction)

@mcp.tool(
    name="gemini_video",
    description="Watch and analyze a video file (MP4, MOV, MKV, WebM, AVI, short-form shorts/reels, screencasts, animation clips) using Google Gemini's native video understanding. Analyze visual scene transitions, cut pacing, B-roll timing, on-screen text, presenter body language, and temporal story flow. Provide the absolute local file path."
)
async def gemini_video(video_path: str, question: str = "Watch and analyze this video in detail, describing the visual flow, pacing, and key scenes.") -> str:
    """Watch and analyze a video file using Gemini Multimodal Video."""
    norm_path = os.path.abspath(video_path).replace("\\", "/")
    if not os.path.exists(norm_path):
        return f"Error: Video file not found at '{norm_path}'"

    instruction = (
        f"Please inspect and watch the video file at `{norm_path}` using view_file.\n"
        f"User question / instruction: {question}"
    )
    return await call_bridge("gemini-3.1-pro-high", instruction)

@mcp.tool(
    name="gemini_read_document",
    description="Offload reading and analyzing massive documents, PDFs, logs, or large code files to Google Gemini's 2,000,000 token context window. Provide the absolute local file path."
)
async def gemini_read_document(file_path: str, question: str = "Summarize the key information and extract the most relevant details.") -> str:
    """Read and analyze massive documents using Gemini's 2M token context window."""
    norm_path = os.path.abspath(file_path).replace("\\", "/")
    if not os.path.exists(norm_path):
        return f"Error: Document file not found at '{norm_path}'"

    instruction = (
        f"Please inspect the document file at `{norm_path}` using view_file.\n"
        f"User question / instruction: {question}"
    )
    return await call_bridge("gemini-3.1-pro-high", instruction)

@mcp.tool(
    name="gemini_multimodal_inspect",
    description="Universal multimodal inspector for ANY media file: image, audio, video, PDF, or code. Automatically routes to Gemini Pro's native multimodal engine. Provide the absolute local file path."
)
async def gemini_multimodal_inspect(file_path: str, question: str = "Analyze this file in detail and answer any questions.") -> str:
    """Inspect any media file (image, audio, video, document) using Gemini Multimodal Pro."""
    norm_path = os.path.abspath(file_path).replace("\\", "/")
    if not os.path.exists(norm_path):
        return f"Error: File not found at '{norm_path}'"

    instruction = (
        f"Please inspect the media file at `{norm_path}` using view_file.\n"
        f"User question / instruction: {question}"
    )
    return await call_bridge("gemini-3.1-pro-high", instruction)

if __name__ == "__main__":
    asyncio.run(mcp.run_stdio_async())
