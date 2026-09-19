# AI Short-Video Production Pipeline
### Synthesizing Riley Brown (VibeCode) × Kallaway (Marketing Metaphors) × Sabrina Ramonov (System Blueprints)

A production-grade, zero-cost pipeline designed to generate hyper-retention short-form video scripts and multi-track asset packages for technical and AI topics.

---

## 1. Architectural Highlights

* **Dual-Mode Generation:**
  * **Mode A: Fully Standalone (Faceless):** Built for high-volume automated publishing. Driven by kinetic typography, live UI captures, and story-driven visual metaphors.
  * **Mode B: With-Me-On-Camera (Presenter):** Built for personal brand and authority. Uses tight chest-level framing, punch-in zooms, 3-second face limits, and hand-gesture-synced picture-in-picture cutaways.
* **$0 Budget Enforcement:** Uses existing subscriptions (Gemini, Antigravity built-in image generator, local browser DevTools/screen capture, and free CapCut editing). No paid video rendering APIs or external subscriptions required.
* **Pro-Tier Quality Gate Loop:** Automated quality control where Gemini Flash drafts and Gemini Pro independently judges against an 8-dimension viral retention rubric. Automatically iterates until the package achieves $\ge 9.0/10.0$.

---

## 2. Directory Structure

```
scratch/ai_short_video_pipeline/
├── pipeline_graph.mermaid          # Mermaid architecture flowchart
├── pipeline_engine.py             # Python orchestrator & schema builder
├── CREATOR_ANALYSIS.md            # Deep-dive study into Brown, Kallaway, and Ramonov
├── templates/
│   ├── hook_formulas.json         # 7 viral hook formulas with visual cues
│   ├── mode_specs.json            # Strict pacing & compositing rules for Mode A & B
│   └── scoring_rubric.json        # 8-dimension quantitative evaluation rubric
└── output/
    └── grok_bot_episode/          # Production-ready test episode
        ├── draft_v1.json          # Initial draft
        ├── critique_v1.json       # Round 1 audit (Score: 7.23 -> REVISE)
        ├── draft_v2.json          # Refined draft with 19 micro-shots
        ├── critique_v2.json       # Round 2 audit (Score: 9.75 -> PASS)
        ├── FINAL_PRODUCTION_PACKAGE.md # Shot-by-shot timeline & dual scripts
        └── visual_assets/         # Generated 9:16 visual metaphor images
```

---

## 3. The 3 Synthesized Creator Disciplines

1. **Riley Brown ("The Builder"):**
   * *Show-Don't-Tell:* Live screen recordings, UI terminal interactions, rough edges that prove authenticity.
   * *High-Velocity Cadence:* Audio and visual stimuli shift every 2.0 to 2.8 seconds.
2. **Kallaway ("The Strategist"):**
   * *Hook Engineering:* Context lean + abrupt cognitive paradox ("Traditional AI waits for you to type, then dies").
   * *Comprehension Maxing:* Translates abstract technical architectures into undeniable visual metaphors.
3. **Sabrina Ramonov ("The Systems Architect"):**
   * *Bookmark Traps:* Every short ends with an exact, copy-pasteable prompt and concrete free software stack that compels viewers to hit "Save" or "Bookmark".
   * *Modularity:* Full faceless vs presenter parity.

---

## 4. How to Run a New Episode

1. Run `pipeline_engine.py` with your new topic (e.g. `python pipeline_engine.py`).
2. Flash generates candidate hooks from `templates/hook_formulas.json`.
3. Select Mode A or Mode B (or generate dual-track).
4. Subagent invokes Gemini Pro Quality Gate to audit the timeline.
5. If score $< 9.0$, the engine auto-refines pacing and prompt specificity until $\ge 9.0$ is reached.
6. Generate visual assets via Antigravity image generation and export final production markdown.
