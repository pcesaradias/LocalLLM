"""Backend-agnostic inference layer for the localllm service.

Selects between Ollama's native API and any OpenAI-compatible endpoint based on
the INFERENCE_BACKEND env var, which is read at call time (not at import) so
tests and deployments can override it without re-importing.

All functions reuse the caller's httpx.AsyncClient (the shared `_http` in
main.py) instead of opening a second client, so connection pooling and the
event-loop-friendly timeouts configured there are preserved.
"""

import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)


def backend() -> str:
    """Return the selected inference backend name: "ollama" (default) | "openai".

    Read at call time so INFERENCE_BACKEND can be overridden per test/deploy.
    """
    return os.getenv("INFERENCE_BACKEND", "ollama").strip().lower()


def _ollama_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _openai_url() -> str:
    # e.g. https://api.groq.com/openai/v1
    return os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")


def _openai_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


async def generate(http, model: str, prompt: str, temperature: float = 0.7,
                   max_tokens: Optional[int] = None, timeout: float = 600.0) -> str:
    """Generate a single (non-streamed) completion and return the text.

    Raises RuntimeError on a non-2xx response with a message naming the backend,
    status code and URL so failures are actionable.
    """
    if backend() == "openai":
        url = f"{_openai_url()}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = await http.post(url, json=payload, headers=_openai_headers(), timeout=timeout)
        if resp.status_code // 100 != 2:
            raise RuntimeError(
                f"OpenAI backend generate failed ({resp.status_code}) at {url}: {resp.text}"
            )
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ollama (default)
    url = f"{_ollama_url()}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    resp = await http.post(url, json=payload, timeout=timeout)
    if resp.status_code // 100 != 2:
        raise RuntimeError(
            f"Ollama backend generate failed ({resp.status_code}) at {url}: {resp.text}"
        )
    data = resp.json()
    return data["response"]


async def generate_vision(http, model: str, prompt: str, image_data: str,
                          temperature: float = 0.7, max_tokens: Optional[int] = None,
                          timeout: float = 600.0, mime: str = "image/jpeg") -> str:
    """Generate a completion from a text prompt + a base64 image, return the text.

    `image_data` is raw base64 (no data: prefix). Raises RuntimeError on non-2xx.
    """
    if backend() == "openai":
        url = f"{_openai_url()}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                ],
            }],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = await http.post(url, json=payload, headers=_openai_headers(), timeout=timeout)
        if resp.status_code // 100 != 2:
            raise RuntimeError(
                f"OpenAI backend generate_vision failed ({resp.status_code}) at {url}: {resp.text}"
            )
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ollama (default) — native /api/generate with images[]
    url = f"{_ollama_url()}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_data],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    resp = await http.post(url, json=payload, timeout=timeout)
    if resp.status_code // 100 != 2:
        raise RuntimeError(
            f"Ollama backend generate_vision failed ({resp.status_code}) at {url}: {resp.text}"
        )
    data = resp.json()
    return data["response"]


async def stream_tokens(http, model: str, prompt: str, temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        timeout: float = 600.0) -> AsyncGenerator[str, None]:
    """Yield text token chunks as they are produced by the backend.

    Raises RuntimeError on a non-2xx response before any tokens are yielded.
    """
    if backend() == "openai":
        url = f"{_openai_url()}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with http.stream("POST", url, json=payload,
                               headers=_openai_headers(), timeout=timeout) as resp:
            if resp.status_code // 100 != 2:
                await resp.aread()
                raise RuntimeError(
                    f"OpenAI backend stream failed ({resp.status_code}) at {url}: {resp.text}"
                )
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                content = (choices[0].get("delta") or {}).get("content")
                if content:
                    yield content
        return

    # ollama (default)
    url = f"{_ollama_url()}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    async with http.stream("POST", url, json=payload, timeout=timeout) as resp:
        if resp.status_code // 100 != 2:
            await resp.aread()
            raise RuntimeError(
                f"Ollama backend stream failed ({resp.status_code}) at {url}: {resp.text}"
            )
        async for line in resp.aiter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "response" in obj:
                yield obj["response"]
            if obj.get("done", False):
                break


async def list_models(http) -> List[Dict[str, Any]]:
    """Return available models normalized to [{name,size,modified,status}].

    Raises RuntimeError on a non-2xx response.
    """
    if backend() == "openai":
        url = f"{_openai_url()}/models"
        resp = await http.get(url, headers=_openai_headers())
        if resp.status_code // 100 != 2:
            raise RuntimeError(
                f"OpenAI backend list_models failed ({resp.status_code}) at {url}: {resp.text}"
            )
        data = resp.json()
        return [
            {"name": m.get("id"), "size": "n/a", "modified": "n/a", "status": "available"}
            for m in data.get("data", [])
        ]

    # ollama (default)
    url = f"{_ollama_url()}/api/tags"
    resp = await http.get(url)
    if resp.status_code // 100 != 2:
        raise RuntimeError(
            f"Ollama backend list_models failed ({resp.status_code}) at {url}: {resp.text}"
        )
    data = resp.json()
    models: List[Dict[str, Any]] = []
    for m in data.get("models", []):
        size = m.get("size", "unknown")
        models.append({
            "name": m.get("name"),
            "size": str(size) if isinstance(size, int) else (size if isinstance(size, str) else "unknown"),
            "modified": str(m.get("modified_at", "unknown")),
            "status": "available",
        })
    return models
