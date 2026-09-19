"""
Gemideo: AI Short-Video Production Pipeline Engine
Synthesizing Riley Brown (Builder/VibeCode) x Kallaway (Marketing/Metaphors) x Sabrina Ramonov (System Blueprints)
Dual Modes: Mode A (Standalone / Faceless) & Mode B (With-Me-On-Camera)
Zero Dollar Stack: Gemini / Antigravity / Browser / Local Open Tools
"""

import json
import os
import argparse
import sys
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def load_json(filename: str) -> Dict[str, Any]:
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class GemideoPipeline:
    def __init__(self):
        self.hooks = load_json("hook_formulas.json")["hook_archetypes"]
        self.mode_specs = load_json("mode_specs.json")
        self.rubric = load_json("scoring_rubric.json")

    def list_hooks(self):
        """Displays available hook archetypes with visual cues and formulas."""
        print("\n=== AVAILABLE VIRAL HOOK FORMULAS ===")
        for i, h in enumerate(self.hooks, 1):
            print(f"[{i}] {h['name']} ({h['id']})")
            print(f"    Formula: {h['formula']}")
            print(f"    Visual Cue: {h['visual_cue']}")
            print(f"    Retention: {h['retention_mechanism']}\n")

    def export_srt(self, episode_json_path: str, output_srt_path: str):
        """Converts an episode shot timeline into standard SRT subtitle format."""
        with open(episode_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        timeline = data.get("shot_by_shot_timeline", [])
        srt_lines = []
        for i, shot in enumerate(timeline, 1):
            # Parse timestamp e.g. "00:00 - 00:02.1"
            parts = shot["timestamp"].split(" - ")
            start_str = parts[0].strip()
            end_str = parts[1].strip()

            def to_srt_time(t_str: str) -> str:
                # converts "00:02.1" or "00:02" to "00:00:02,100"
                tokens = t_str.split(":")
                mins = int(tokens[0])
                secs_part = tokens[1]
                if "." in secs_part:
                    secs = int(secs_part.split(".")[0])
                    millis = int(float("0." + secs_part.split(".")[1]) * 1000)
                else:
                    secs = int(secs_part)
                    millis = 0
                hrs = mins // 60
                mins = mins % 60
                return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

            start_srt = to_srt_time(start_str)
            end_srt = to_srt_time(end_str)

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_srt} --> {end_srt}")
            srt_lines.append(f"{shot['spoken_script']}\n")

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        print(f"Exported SRT subtitle file to: {output_srt_path}")

    def build_generation_prompt(self, topic: str, mode: str = "A", hook_id: str = "trinity_hybrid_nuke") -> str:
        """Generates the prompt package to be fed into Gemini Flash for drafting."""
        selected_hook = next((h for h in self.hooks if h["id"] == hook_id), self.hooks[0])
        mode_key = "mode_a_standalone" if mode.upper() == "A" else "mode_b_on_camera"
        spec = self.mode_specs[mode_key]

        return f"""
        === GEMIDEO VIRAL SHORT GENERATION PROMPT ===
        Topic: {topic}
        Hook Archetype: {selected_hook['name']}
        Selected Mode: {spec['title']}
        Target Duration: {spec['pacing_rules']['target_duration_seconds']}
        Word Limit: {spec['pacing_rules']['word_count_limit']}
        Maximum Shot Duration: <= 3.0 seconds per visual stimulus cut.
        
        Synthesize:
        1. Riley Brown: VibeCode, screen recordings, rapid 2.5s pacing, authentic developer grit.
        2. Kallaway: Subverted assumptions, visual metaphors translating abstract tech into physical models.
        3. Sabrina Ramonov: High-save bookmark blueprint, copy-pasteable prompt, $0 free software stack.
        """

def main():
    parser = argparse.ArgumentParser(description="Gemideo: AI Short-Video Production Pipeline")
    parser.add_argument("--list-hooks", action="store_true", help="List all 7 viral hook formulas")
    parser.add_argument("--export-srt", action="store_true", help="Export SRT subtitle file for Grok Bot episode")
    parser.add_argument("--topic", type=str, help="Topic for new episode generation")
    parser.add_argument("--mode", type=str, choices=["A", "B"], default="A", help="Production mode: A (Standalone) or B (On-Camera)")
    args = parser.parse_args()

    pipeline = GemideoPipeline()

    if args.list_hooks:
        pipeline.list_hooks()
    elif args.export_srt:
        episode_path = os.path.join(OUTPUT_DIR, "grok_bot_episode", "draft_v3.json")
        srt_path = os.path.join(OUTPUT_DIR, "grok_bot_episode", "grok_bot_episode.srt")
        pipeline.export_srt(episode_path, srt_path)
    elif args.topic:
        prompt = pipeline.build_generation_prompt(args.topic, mode=args.mode)
        print(f"\nGenerated Generation Prompt for '{args.topic}':\n")
        print(prompt)
    else:
        print("Gemideo Pipeline initialized.")
        print(f"Loaded {len(pipeline.hooks)} hook archetypes.")
        print(f"Loaded {len(pipeline.rubric['dimensions'])} evaluation dimensions.")
        print("Use --list-hooks, --export-srt, or --topic '<name>' to run CLI commands.")

if __name__ == "__main__":
    main()
