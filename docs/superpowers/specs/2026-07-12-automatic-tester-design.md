# Design — `automatic_tester`: the self-improvement / retraining engine

**Date:** 2026-07-12
**Status:** Approved

## Problem

`model-improvement-service/main.py` imports `automatic_tester.AutomaticTester`, a
module that does not exist in the repo. So `/improve/automatic` and
`/improve/test-model` return HTTP 501 and the flagship "automated self-improvement"
loop is a stub. This design implements the missing engine.

## Decisions (approved)

- **Reference + judge model:** Groq (free), configurable. The "commercial" side of
  the comparison and the judge both use a strong Groq model. (Anthropic/Claude can
  be enabled later via env; not used by default to avoid burning credits.)
- **Training step:** the pipeline generates the LoRA training dataset to disk for a
  Colab/RunPod handoff. It does NOT run Unsloth/CUDA training locally (no GPU on the
  target machine). `create_improved` produces the dataset + a proposed model name.

## Interface (matches existing callers — do not change the callers)

- `AutomaticTester(claude_api_key: str | None, ollama_url: str)` — constructor
  (signature kept compatible with `main.py:59`). Reads Groq config from env:
  `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `REFERENCE_MODEL` (default
  `llama-3.3-70b-versatile`), `JUDGE_MODEL` (default = reference).
- `full_improvement_pipeline(model_name: str, num_tests: int, create_improved: bool) -> dict`
  — the only method `main.py` calls (`main.py:413`). Synchronous (called
  un-awaited from the async background task). Returns:
  ```
  {
    "model_name", "num_tests", "create_improved",
    "statistics": {"total", "wins", "losses", "ties", "win_rate"},  # win_rate = local wins %
    "comparisons": [{"prompt", "winner", "reason"} ...],            # capped/truncated for storage
    "dataset_path": "<jsonl of losing cases, reference answer as target>" | None,
    "improved_model_name": "<proposed name>" | None,               # set only when create_improved
    "training_handoff": "<human note pointing at the Colab/RunPod path>" | None,
  }
  ```

## Flow (all CPU, runs locally)

1. Load `num_tests` prompts from a bundled curated set (coding + reasoning), cycling
   if `num_tests` exceeds the set size.
2. For each prompt:
   - `local` = generate from the model under test via `ollama_url` (`/api/generate`, `model_name`).
   - `reference` = generate from the Groq `REFERENCE_MODEL` (OpenAI-compatible `/chat/completions`).
   - `winner` = judge via Groq `JUDGE_MODEL`: blind A/B, returns `local` | `reference` | `tie`.
3. `win_rate` = wins / total * 100 (local wins).
4. Losing/tie cases → JSONL rows `{"instruction": prompt, "input": "", "output": reference}`
   (the format the existing LoRA scripts consume) written to
   `datasets/lora_profiles/auto_<model>_<n>.jsonl`; a summary JSON to `comparison_results/`.
5. If `create_improved`: keep the dataset, set `improved_model_name = f"{base}-reflexion"`,
   set `training_handoff` to a note pointing at the dataset + the repo's Colab/RunPod
   training scripts. No local training.

## Isolation / units

- `automatic_tester.py` is self-contained: constructor + private `_gen_local`,
  `_gen_reference`, `_judge`, `_write_dataset`, and the public
  `full_improvement_pipeline`. It depends only on `requests`, stdlib, and env — no
  import from `main.py` (avoids cycles).
- Reuses the OpenAI-compatible request shape already proven in `inference.py`.

## Error handling

- Any per-prompt generation/judge failure is caught, logged, and counted as a skip
  (does not abort the run). If Groq is unreachable, the pipeline returns with
  `statistics.total` = successful comparisons and a `warnings` list.
- Missing `OPENAI_API_KEY` → the reference/judge steps raise a clear RuntimeError at
  pipeline start (fail loud), since the whole feature needs it.

## Testing

- Unit tests (`tests/test_automatic_tester.py`): the win-rate math, dataset JSONL
  shape, and judge-response parsing, with the HTTP calls monkeypatched (no network).
- Live: run `/improve/automatic` against a real Ollama model (gemma3:4b) vs Groq,
  confirm it returns a real `win_rate` and writes a dataset.

## Out of scope

Actual LoRA/Unsloth training (GPU / Colab), vLLM local serving. Handoff only.
