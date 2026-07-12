"""Automatic self-improvement engine for the model-improvement-service.

Runs a curated set of test prompts through the model under test (local, via
Ollama) and a strong reference model (Groq / any OpenAI-compatible endpoint),
has a judge model pick the better answer, computes a win rate, and writes the
losing cases as a LoRA fine-tuning dataset for a Colab/RunPod training handoff.

It does NOT run training locally (that needs a CUDA GPU). `create_improved`
produces the dataset + a proposed model name and a handoff note.

Config (env): OPENAI_BASE_URL, OPENAI_API_KEY (reference + judge, required),
REFERENCE_MODEL (default llama-3.3-70b-versatile), JUDGE_MODEL (default =
reference), OLLAMA_URL (model under test).
"""
import json
import logging
import os
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Curated coding + reasoning prompts. num_tests cycles through this list.
TEST_PROMPTS = [
    "Write a Python function that returns the nth Fibonacci number iteratively.",
    "Explain the difference between a process and a thread in three sentences.",
    "Write a SQL query to find the second highest salary in an employees table.",
    "What is a race condition and how do you prevent one? Answer concisely.",
    "Write a Python function to check whether a string is a palindrome.",
    "Explain what a REST API is to a junior developer in a short paragraph.",
    "Given a list of integers, write Python to return only the even ones.",
    "Describe the time complexity of binary search and why.",
    "Write a function to reverse a linked list in Python.",
    "What does the 'async'/'await' keyword pair do in Python? Be brief.",
    "Write a regex that matches a valid IPv4 address.",
    "Explain database indexing and one trade-off it introduces.",
    "Write Python to count word frequencies in a string, returning a dict.",
    "What is the difference between TCP and UDP? Two sentences.",
    "Write a function that merges two sorted lists into one sorted list.",
]


class AutomaticTester:
    def __init__(self, claude_api_key=None, ollama_url="http://localhost:11434"):
        # claude_api_key kept for constructor compatibility with main.py; the
        # reference + judge use the configured OpenAI-compatible endpoint.
        self.claude_api_key = claude_api_key
        self.ollama_url = (ollama_url or "http://localhost:11434").rstrip("/")
        self.openai_base = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.reference_model = os.getenv("REFERENCE_MODEL", "llama-3.3-70b-versatile")
        self.judge_model = os.getenv("JUDGE_MODEL", self.reference_model)
        self.datasets_dir = Path(os.getenv("DATASETS_DIR", "/app/datasets/lora_profiles"))
        self.results_dir = Path(os.getenv("RESULTS_DIR", "/app/comparison_results"))

    # --- generation ---------------------------------------------------------
    def _gen_local(self, model, prompt, timeout=120):
        r = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

    def _openai_chat(self, model, messages, temperature=0.2, timeout=120):
        if not self.openai_base or not self.openai_key:
            raise RuntimeError(
                "OPENAI_BASE_URL/OPENAI_API_KEY are required for the reference and judge models"
            )
        r = requests.post(
            f"{self.openai_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.openai_key}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages": messages,
                  "temperature": temperature, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return (r.json()["choices"][0]["message"]["content"] or "").strip()

    def _gen_reference(self, prompt, timeout=120):
        return self._openai_chat(
            self.reference_model, [{"role": "user", "content": prompt}], timeout=timeout
        )

    def _judge(self, prompt, ans_a, ans_b):
        """Blind A/B judgement. Returns 'A' | 'B' | 'TIE'."""
        judge_prompt = (
            "You are judging two AI answers to the same question. "
            "Reply with ONLY one token: A if the first answer is better, "
            "B if the second is better, TIE if they are equal.\n\n"
            f"QUESTION:\n{prompt}\n\nANSWER A:\n{ans_a}\n\nANSWER B:\n{ans_b}\n\nVerdict:"
        )
        raw = self._openai_chat(
            self.judge_model, [{"role": "user", "content": judge_prompt}], temperature=0.0
        )
        u = raw.strip().upper()
        if "TIE" in u:
            return "TIE"
        has_a = re.search(r"\bA\b", u) is not None
        has_b = re.search(r"\bB\b", u) is not None
        if has_a and not has_b:
            return "A"
        if has_b and not has_a:
            return "B"
        if has_a and has_b:
            return "A" if u.index("A") < u.index("B") else "B"
        return "TIE"

    # --- pipeline -----------------------------------------------------------
    def full_improvement_pipeline(self, model_name, num_tests=10, create_improved=False):
        if not self.openai_base or not self.openai_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required to run the improvement pipeline (reference + judge)"
            )

        n = max(1, int(num_tests))
        prompts = [TEST_PROMPTS[i % len(TEST_PROMPTS)] for i in range(n)]

        comparisons = []
        losing = []
        warnings = []
        wins = losses = ties = 0

        for prompt in prompts:
            try:
                local = self._gen_local(model_name, prompt)
                reference = self._gen_reference(prompt)
                # Position note: local is always ANSWER A. LLM judges have some
                # position bias; the win_rate is a directional signal, not a
                # precise benchmark.
                verdict = self._judge(prompt, local, reference)
                if verdict == "A":
                    wins += 1
                    winner = "local"
                elif verdict == "B":
                    losses += 1
                    winner = "reference"
                    losing.append({"instruction": prompt, "input": "", "output": reference})
                else:
                    ties += 1
                    winner = "tie"
                    losing.append({"instruction": prompt, "input": "", "output": reference})
                comparisons.append({"prompt": prompt[:120], "winner": winner})
            except Exception as e:
                warnings.append(f"skipped a prompt: {e}")
                logger.warning(f"comparison skipped: {e}")

        total = wins + losses + ties
        win_rate = round((wins / total * 100.0), 1) if total else 0.0

        dataset_path = self._write_dataset(model_name, losing) if losing else None

        improved_model_name = None
        training_handoff = None
        if create_improved:
            base = model_name.split(":")[0]
            improved_model_name = f"{base}-reflexion"
            training_handoff = (
                f"Training dataset ready at {dataset_path}. This host has no CUDA GPU: "
                f"run scripts/automation/UNSLOTH_TRAINING.py on Colab/Kaggle/RunPod with "
                f"that dataset, then import the result to Ollama as '{improved_model_name}'."
            )

        result = {
            "model_name": model_name,
            "num_tests": num_tests,
            "create_improved": create_improved,
            "statistics": {
                "total": total, "wins": wins, "losses": losses,
                "ties": ties, "win_rate": win_rate,
            },
            "comparisons": comparisons[:50],
            "dataset_path": str(dataset_path) if dataset_path else None,
            "improved_model_name": improved_model_name,
            "training_handoff": training_handoff,
            "warnings": warnings,
        }

        try:
            self.results_dir.mkdir(parents=True, exist_ok=True)
            summary = self.results_dir / f"auto_{model_name.replace(':', '_')}_{total}.json"
            summary.write_text(json.dumps(result, indent=2))
        except Exception as e:
            logger.warning(f"could not write summary file: {e}")

        return result

    def _write_dataset(self, model_name, rows):
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        path = self.datasets_dir / f"auto_{model_name.replace(':', '_')}_{len(rows)}.jsonl"
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        return path
