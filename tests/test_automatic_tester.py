"""Unit tests for the automatic_tester self-improvement engine.

HTTP calls are monkeypatched, so no network / Ollama / Groq is needed. These
verify the win-rate math, the losing-case dataset shape, and judge parsing.
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "model-improvement-service" / "automatic_tester.py"


def _load():
    spec = importlib.util.spec_from_file_location("automatic_tester_under_test", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


at = _load()


def _make_tester(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    t = at.AutomaticTester(claude_api_key=None, ollama_url="http://ollama:11434")
    t.datasets_dir = tmp_path / "datasets"
    t.results_dir = tmp_path / "results"
    return t


def test_win_rate_all_local_wins(tmp_path, monkeypatch):
    t = _make_tester(tmp_path, monkeypatch)
    monkeypatch.setattr(t, "_gen_local", lambda m, p, **k: "local answer")
    monkeypatch.setattr(t, "_gen_reference", lambda p, **k: "reference answer")
    monkeypatch.setattr(t, "_judge", lambda p, a, b: "A")  # A == local
    res = t.full_improvement_pipeline("gemma3:4b", num_tests=4, create_improved=False)
    assert res["statistics"]["total"] == 4
    assert res["statistics"]["wins"] == 4
    assert res["statistics"]["win_rate"] == 100.0
    assert res["dataset_path"] is None  # nothing lost -> no dataset


def test_win_rate_all_local_loses_builds_dataset(tmp_path, monkeypatch):
    t = _make_tester(tmp_path, monkeypatch)
    monkeypatch.setattr(t, "_gen_local", lambda m, p, **k: "weak")
    monkeypatch.setattr(t, "_gen_reference", lambda p, **k: "strong reference")
    monkeypatch.setattr(t, "_judge", lambda p, a, b: "B")  # B == reference wins
    res = t.full_improvement_pipeline("gemma3:4b", num_tests=3, create_improved=True)
    assert res["statistics"]["wins"] == 0
    assert res["statistics"]["losses"] == 3
    assert res["statistics"]["win_rate"] == 0.0
    # dataset written with reference answer as the target
    p = Path(res["dataset_path"])
    assert p.exists()
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    assert len(rows) == 3
    assert rows[0]["output"] == "strong reference"
    assert set(rows[0].keys()) == {"instruction", "input", "output"}
    # create_improved -> proposed model + handoff note (no local training)
    assert res["improved_model_name"] == "gemma3-reflexion"
    assert "Colab" in res["training_handoff"] or "RunPod" in res["training_handoff"]


def test_skips_failed_prompts(tmp_path, monkeypatch):
    t = _make_tester(tmp_path, monkeypatch)
    calls = {"n": 0}

    def flaky_local(m, p, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("ollama down")
        return "ok"

    monkeypatch.setattr(t, "_gen_local", flaky_local)
    monkeypatch.setattr(t, "_gen_reference", lambda p, **k: "ref")
    monkeypatch.setattr(t, "_judge", lambda p, a, b: "A")
    res = t.full_improvement_pipeline("gemma3:4b", num_tests=3, create_improved=False)
    assert res["statistics"]["total"] == 2  # one skipped
    assert len(res["warnings"]) == 1


@pytest.mark.parametrize("raw,expected", [
    ("A", "A"), ("B", "B"), ("TIE", "TIE"),
    ("The better answer is A.", "A"),
    ("b", "B"), ("They are equal, TIE", "TIE"),
    ("neither is good", "TIE"),  # unknown -> TIE
])
def test_judge_parsing(tmp_path, monkeypatch, raw, expected):
    t = _make_tester(tmp_path, monkeypatch)
    monkeypatch.setattr(t, "_openai_chat", lambda model, messages, **k: raw)
    assert t._judge("q", "a1", "a2") == expected


def test_missing_openai_key_fails_loud(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example/v1")
    t = at.AutomaticTester(claude_api_key=None, ollama_url="http://ollama:11434")
    with pytest.raises(RuntimeError):
        t.full_improvement_pipeline("gemma3:4b", num_tests=1, create_improved=False)
