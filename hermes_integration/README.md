# Multi-Agent Subscription Bridge: Gemini AI for Claude, Hermes, ChatGPT & Muse

Connect your active **Google Antigravity / Gemini Subscription** to all your daily AI workflows with **zero extra API costs**:

- 🤖 **Claude (Desktop & CLI)**: Multimodal Vision, 2M-token document analysis, and second-opinion reasoning via native **Model Context Protocol (MCP)**.
- ⚡ **Hermes Agent (Desktop & CLI)**: Native default provider + Auxiliary Vision engine + MCP tools.
- 💬 **ChatGPT (Desktop & Web)**: Custom GPT Actions using OpenAPI 3.0.
- 🎨 **Muse (muse.ai / Meta AI)**: Seamless browser overlay with `Alt + G` second opinions and vision outsourcing.

---

## 🚀 Unified Capability Matrix

| Platform | Integration Method | Capabilities Unlocked | Cost |
| :--- | :--- | :--- | :--- |
| **Claude Desktop** | MCP (`gemini_sub_mcp.py`) | `gemini_vision`, `gemini_audio`, `gemini_video`, `gemini_generate_image`, `gemini_read_document`, `ask_gemini_pro`, `ask_gemini_flash` | **$0.00** |
| **Claude Code (CLI)** | User-level MCP Server | Full terminal tool suite & Imagen generation across all projects | **$0.00** |
| **Hermes Agent** | Native Bridge + Aux Vision | Default brain (`gemini-3.1-pro-high`) + auxiliary vision + `/v1/images/generations` | **$0.00** |
| **ChatGPT** | Custom GPT Actions (OpenAPI) | Outsource proofs, complex reasoning, 2M document reading, image gen | **$0.00** |
| **Muse (muse.ai)** | Userscript (`Alt+G`) + CORS | Quick second opinion & vision card directly on muse.ai | **$0.00** |

---

## 🛠️ Setup Instructions

### 1. Claude Desktop & Claude Code
Both **Claude Desktop** and **Claude Code CLI** are already pre-configured on this system:
- **Claude Desktop config updated:** `C:\Users\danom\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`
- **Claude Code CLI registered:** `claude mcp add --scope user gemini_sub python "C:\Users\danom\scripts\gemini_sub_mcp.py"`
- **How to use in Claude**:
  - Ask Claude: *"Use gemini_vision to inspect screenshot.png and describe the UI layout."*
  - Ask Claude: *"Use gemini_generate_image to create a photorealistic cyberpunk neon skyline in 16:9 aspect ratio."*
  - Ask Claude: *"Use gemini_read_document on huge_codebase.py and extract all API endpoints."*
  - Ask Claude: *"Ask Gemini Pro to double-check this mathematical proof."*

### 2. Hermes Desktop & CLI
Hermes is already configured:
- `C:\Users\danom\AppData\Local\hermes\config.yaml` has `default: gemini-3.1-pro-high` and `auxiliary.vision` routed to the bridge.
- You can run `hermes` directly or switch models in the desktop app.
- **Image Generation in Hermes / OpenAI clients**: Call `POST http://127.0.0.1:8000/v1/images/generations` with standard OpenAI payload (`{"prompt": "...", "size": "1024x1024"}`) to generate images via Google Imagen with $0 extra cost.

### 3. ChatGPT (Desktop & Web)
To connect your Gemini subscription to ChatGPT:
1. Double-click `start_chatgpt_tunnel.bat` (uses free `localtunnel` on port 8000).
2. Copy the generated `https://xxxx.loca.lt` URL.
3. In ChatGPT -> **Explore GPTs** -> **Create a GPT**:
   - Go to **Configure** -> **Create new action**.
   - Paste the contents of `chatgpt_custom_gpt_action.json`.
   - Replace the `servers.url` with your tunnel URL.
4. Save the GPT! Now ChatGPT can delegate heavy lifting and vision to your Gemini subscription!

### 4. Muse (muse.ai / Meta AI)
Since muse.ai is web-based:
1. Install **Tampermonkey** or **Violentmonkey** extension in your browser.
2. Install [`muse_gemini_companion.user.js`](muse_gemini_companion.user.js).
3. Open `https://muse.ai`:
   - A floating **✦** icon appears in the bottom right.
   - Or highlight text on Muse and press **`Alt + G`**.
   - Gemini 3.1 Pro processes the query and allows one-click copying straight into Muse!

---

## 🔄 Core Service & Management

The local bridge service runs at `http://127.0.0.1:8000`:
- **Silent Background Run:** Double-click `start_gemini_hermes_bridge.vbs`
- **Console Run:** Double-click `start_gemini_hermes_bridge.bat`
- **MCP Server:** `python C:\Users\danom\scripts\gemini_sub_mcp.py`
- **Health Check:** `curl http://127.0.0.1:8000/health`
