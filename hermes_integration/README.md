# Hermes Agent Integration with Antigravity & Gemini Subscription

This bridge enables **Hermes Agent** (Desktop App & CLI) to tap directly into your active **Google Antigravity / Gemini Subscription** with **zero additional API costs**.

---

## 🌟 Capabilities Unlocked

| Provider / Model | Backend Routing | Cost | Reasoning / Thinking |
| :--- | :--- | :--- | :--- |
| `gemini-3.1-pro-high` | Google Antigravity Session | **$0.00** (Included) | ✅ Full Reasoning |
| `gemini-3.8-flash-high` | Google Antigravity Session | **$0.00** (Included) | ✅ Low Latency |
| `claude-sonnet-4-6` | Antigravity Multi-Model Session | **$0.00** (Included) | ✅ Frontier Coding |
| `claude-opus-4-6-thinking` | Antigravity Multi-Model Session | **$0.00** (Included) | ✅ Deep Thinking |
| `gpt-oss-120b-medium` | Antigravity Local/OSS Cluster | **$0.00** (Included) | ✅ Open Source |
| `xai-oauth` (Grok 4.6 / Grok 4.20) | Native xAI OAuth in Hermes | **$0.00** (OAuth Sub) | ✅ Real-time X Telemetry |

---

## 🚀 How It Works

1. **Standard OpenAI Compatible Bridge**:
   - Runs locally at `http://127.0.0.1:8000/v1`
   - Exposes `/v1/chat/completions` and `/v1/models`
2. **Stdin NDJSON Streaming (`stream-json`)**:
   - Solves Windows `WinError 206` (command-line length limits) by streaming large prompts and context windows through standard input directly into `agy.exe`.
   - Real-time token streaming via Server-Sent Events (SSE).
   - Accurately captures token usage metadata (`input_tokens`, `output_tokens`, `thinking_tokens`).
3. **Hermes Configuration**:
   - `C:\Users\danom\AppData\Local\hermes\config.yaml` is pre-configured with `gemini_sub` as the active provider:
   ```yaml
   model:
     default: gemini-3.1-pro-high
     provider: gemini_sub
   providers:
     gemini_sub:
       name: "Gemini Subscription (Antigravity)"
       base_url: "http://127.0.0.1:8000/v1"
       api_key: "antigravity-local"
       models:
         gemini-3.1-pro-high: {}
         gemini-3.8-flash-high: {}
         claude-sonnet-4-6: {}
         claude-opus-4-6-thinking: {}
         gpt-oss-120b-medium: {}
   ```

---

## 🛠️ Usage

### From Hermes Desktop App
Simply open Hermes Desktop. It will automatically utilize `Gemini 3.1 Pro (High)` as default. You can also select other models from the model picker in Settings.

### From Hermes CLI
```bash
# Default (Gemini 3.1 Pro)
hermes -z "Analyze this code"

# Explicit Gemini Pro
hermes --provider gemini_sub -m "gemini-3.1-pro-high" -z "Deep reasoning task"

# High-Speed Gemini Flash
hermes --provider gemini_sub -m "gemini-3.8-flash-high" -z "Quick summary"

# Claude Sonnet via Antigravity
hermes --provider gemini_sub -m "claude-sonnet-4-6" -z "Code refactoring"

# Grok via xAI OAuth
hermes --provider xai-oauth -m "grok-4.6" -z "Real-time news search"
```

---

## 🔄 Running the Bridge

- **Silent Background Run**: Double-click `start_gemini_hermes_bridge.vbs`
- **Console Run**: Double-click `start_gemini_hermes_bridge.bat`
- **Health Check**: `curl http://127.0.0.1:8000/health`
