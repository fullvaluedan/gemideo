"""
AI Short-Video Production Pipeline Engine
Synthesizing Riley Brown (Builder/VibeCode) x Kallaway (Marketing/Metaphors) x Sabrina Ramonov (System Blueprints)
Dual Modes: Mode A (Standalone / Faceless) & Mode B (With-Me-On-Camera)
Zero Dollar Stack: Gemini / Antigravity / Browser / Local Open Tools
"""

import json
import os
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

def load_json(filename: str) -> Dict[str, Any]:
    path = os.path.join(TEMPLATES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class ShortVideoPipeline:
    def __init__(self):
        self.hooks = load_json("hook_formulas.json")["hook_archetypes"]
        self.mode_specs = load_json("mode_specs.json")
        self.rubric = load_json("scoring_rubric.json")

    def get_hook_matrix(self, topic: str, key_tension: str) -> List[Dict[str, str]]:
        """Generates candidate hooks across the 7 synthesized formulas."""
        generated_hooks = []
        for h in self.hooks:
            generated_hooks.append({
                "hook_id": h["id"],
                "name": h["name"],
                "formula": h["formula"],
                "visual_cue": h["visual_cue"],
                "retention_mechanism": h["retention_mechanism"]
            })
        return generated_hooks

    def build_draft_prompt(self, topic: str, context_details: str, selected_hook: Dict[str, str], mode: str) -> str:
        """Constructs the prompt for drafting an episode in Mode A or Mode B."""
        spec = self.mode_specs["mode_a_standalone" if mode == "A" else "mode_b_on_camera"]
        
        prompt = f"""
        === SHORT VIDEO SCRIPT GENERATION TASK ===
        Topic: {topic}
        Context & Technical Nuances: {context_details}
        Selected Hook Archetype: {selected_hook['name']}
        Hook Formula: {selected_hook['formula']}
        Selected Production Mode: {spec['title']}

        === CONSTRAINTS & PACING ===
        - Target Word Count: {spec['pacing_rules']['word_count_limit']}
        - Total Duration: {spec['pacing_rules']['target_duration_seconds']}
        - Pattern Interrupts: Visual/Auditory shift every {spec['pacing_rules']['pattern_interrupt_interval_seconds']}
        
        === CREATOR DNA INTEGRATION ===
        1. Riley Brown: Live proof-of-work, UI terminal interactions, no corporate fluff.
        2. Kallaway: Visceral visual metaphors, context lean + unexpected pivot, high-status vocal delivery.
        3. Sabrina Ramonov: Clear architectural breakdown, high bookmark/save utility, actionable blueprint.

        === REQUIRED OUTPUT SCHEMA (JSON) ===
        {{
            "episode_title": string,
            "target_duration_seconds": int,
            "total_word_count": int,
            "hook_analysis": {{
                "spoken_words": string,
                "visual_pattern_interrupt": string,
                "audio_impact": string
            }},
            "shot_by_shot_timeline": [
                {{
                    "timestamp": "00:00 - 00:03",
                    "spoken_script": string,
                    "shot_type": string,
                    "visual_action_description": string,
                    "track_1_broll_prompt": string (Antigravity/Gemini zero-cost image prompt),
                    "track_2_ui_screencast_action": string (Browser/IDE exact steps),
                    "track_3_audio_and_sfx": string (Sub-bass, whoosh, click, music energy),
                    "on_screen_kinetic_text": string (Keywords highlighted)
                }}
            ],
            "bookmark_takeaway": string,
            "zero_dollar_execution_plan": string
        }}
        """
        return prompt

    def build_pro_judge_prompt(self, episode_package: Dict[str, Any]) -> str:
        """Constructs the rigorous evaluation prompt for Gemini Pro Quality Gate."""
        rubric_text = json.dumps(self.rubric["dimensions"], indent=2)
        package_text = json.dumps(episode_package, indent=2)

        prompt = f"""
        === INDEPENDENT QUALITY GATE: VIRAL AI SHORT EVALUATION ===
        You are an elite, hyper-critical short-form video creative director and algorithm expert (benchmarking MrBeast, Kallaway, Riley Brown, and Sabrina Ramonov).
        You are evaluating a draft short-form video package on the topic of '{episode_package.get("episode_title", "AI Short")}'.

        You must grade this submission with extreme rigor against the following 8 dimensions:
        {rubric_text}

        Target passing score for production is >= 9.0 / 10.0.
        DO NOT be lenient. Rate realistically. If a hook takes 4 seconds to land, deduct heavily. If B-roll prompts are vague, deduct points. If words exceed 160 words, deduct points.

        === SUBMISSION TO EVALUATE ===
        {package_text}

        === REQUIRED JSON EVALUATION RESPONSE ===
        {{
            "overall_score": float (0.0 to 10.0),
            "dimension_scores": {{
                "dim_1_hook_velocity": {{ "score": float, "critique": string }},
                "dim_2_retention_velocity": {{ "score": float, "critique": string }},
                "dim_3_show_dont_tell": {{ "score": float, "critique": string }},
                "dim_4_visual_metaphors": {{ "score": float, "critique": string }},
                "dim_5_mode_versatility": {{ "score": float, "critique": string }},
                "dim_6_audio_cadence": {{ "score": float, "critique": string }},
                "dim_7_bookmark_utility": {{ "score": float, "critique": string }},
                "dim_8_zero_dollar_compliance": {{ "score": float, "critique": string }}
            }},
            "critical_fail_points": [string],
            "mandatory_revisions_for_9_plus": [string],
            "verdict": "PASS" or "REVISE"
        }}
        """
        return prompt

if __name__ == "__main__":
    pipeline = ShortVideoPipeline()
    print("AI Short-Video Pipeline initialized successfully.")
    print(f"Loaded {len(pipeline.hooks)} hook archetypes.")
    print(f"Loaded {len(pipeline.rubric['dimensions'])} evaluation dimensions.")
