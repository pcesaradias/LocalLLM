# Production-Readiness Review & Roadmap

This document summarizes a full code + architecture + security review of LocalLLM
against real production use, the improvements already applied on the
`production-hardening` branch, and the remaining work — with rationale and
sources — for the changes that need a running stack to validate safely.

The review was cross-checked by independent security, architecture, and
Python-quality passes plus a survey of current (2025–2026) self-hosted-LLM
practice. Findings that three passes agreed on are treated as high-confidence.

---

## Honest status

The README previously claimed "Phase 19 Complete — Production Ready." That was
not accurate: several services could not start or serve their advertised
endpoints, the API key was retrievable without authentication, and every
service (including Redis) was published to the host. **Treat this as a capable
prototype that is now materially hardened, not a turnkey production system.**

---

## What was fixed on this branch

**Correctness / boot blockers**
- `multimodal-agent`: `/analyze-image` and `/analyze-document` called an
  undefined `self.*` and always 500'd — now call the real module functions;
  added a 10 MB upload cap (and stopped the 413 being swallowed into a 500).
- `model-improvement-service`: crashed at import on a missing `automatic_tester`
  module — import is now resilient and the service starts; fixed a
  `logger.info()` `TypeError` in `__main__`.
- `meta-orchestrator`: `except` blocks referenced possibly-unbound variables,
  raising `NameError` that masked the real error and broke the localllm
  fallback — handlers are now safe.
- `langchain-agent`: one global `ConversationBufferMemory` was shared across all
  users (cross-conversation leakage + races) — now per-`conversation_id` memory
  with FIFO eviction; added timeouts to all outbound calls.
- `reflection-agent`: `/metrics` now returns the correct Prometheus content type.
- `localllm`: RAG flag/params are now part of the response cache key, so a RAG
  request can no longer return a stale non-RAG cached answer.

**Security**
- Removed the unauthenticated `/admin/current-key` and `/admin/generate-key`
  (they disclosed / rotated the live API key with a bare `curl`); replaced with
  an authenticated `/admin/rotate-key`.
- Auth now required on every `/admin/*` endpoint.
- Constant-time API-key comparison (`secrets.compare_digest`); stopped logging
  the plaintext key.
- CORS: dropped the invalid `allow_origins=["*"]` + credentials combo for an
  `ALLOWED_ORIGINS` allowlist.
- **Network isolation**: internal services (multimodal, langchain, model-manager,
  web-search, vector-db, model-improvement) and Redis are no longer published to
  the host — only `localllm:8080`, `orchestration:8003`, `meta:8004`, `ui:3001`.
- Redis now requires a password.

**Deployment**
- Non-root user in 8 of 10 service images; `no-new-privileges` on all; per-service
  memory limits; `depends_on: condition: service_healthy`.
- Installed `curl` in the 4 images whose curl healthcheck was silently broken.
- Removed `uvicorn --reload` from the langchain prod image; UI now serves Vite's
  `dist/` (was serving a nonexistent `build/`); pinned base images.
- Fixed the `COMMERCIAL_AI_API_KEY` vs `ANTHROPIC_API_KEY` env mismatch that
  silently disabled commercial comparison.
- Pinned `langchain` to the 0.1.x line the code targets; removed dead deps.

---

## Remaining work (needs a running stack to validate)

Ordered by leverage. These were intentionally **not** applied blind because they
can break the service mesh or runtime behavior in ways only integration testing
catches.

### 1. Eliminate blocking I/O inside `async def` (HIGH — systemic)
Every service except `reflection-agent` calls the synchronous `requests`
library (and sync `redis-py`, and CPU-bound `embedding_model.encode`) directly
inside `async def` handlers. One slow Ollama call blocks the entire event loop —
including `/health` — for that worker. `model-manager` already does this right
(`httpx.AsyncClient` with `await`). Standardize on `httpx.AsyncClient` with
explicit connect+read timeouts, and wrap unavoidable CPU/sync work in
`await run_in_threadpool(...)`. This restores real concurrency and is the single
highest-impact change. *Rationale: FastAPI/async best practice; validated by all
three review passes.*

### 2. Internal service-to-service authentication (HIGH — security)
Auth was deliberately **not** added to the 8 internal services on this branch:
`orchestration-service` calls `multimodal`/`langchain` with no auth header, and
`meta-orchestrator` only tokenizes its call to `localllm`. Adding auth naively
would break the orchestration flow. The correct fix is a shared internal
credential: provision an `INTERNAL_API_KEY` into the Redis key store at startup,
have every internal service require it, and have every inter-service caller send
`Authorization: Bearer ${INTERNAL_API_KEY}`. Network isolation (done) reduces the
exposure in the meantime, but this closes it. *OWASP LLM Top 10 2025: keep
inference/backends behind authenticated gateways.*

### 3. Migrate inference from Ollama to vLLM or SGLang (HIGH — throughput + LoRA)
Ollama is a single-user/dev tool; it processes requests largely sequentially and
degrades sharply under concurrency (benchmarks show it collapsing at ~10–40
concurrent users where vLLM sustains 180+). vLLM adds PagedAttention + continuous
batching, an OpenAI-compatible API (which the FastAPI services already speak), a
native Prometheus `/metrics` endpoint, and — directly relevant to this repo's
reflexion/LoRA loop — **hot-swappable Unsloth LoRA adapters**
(`--enable-lora`, runtime adapter loading) instead of Ollama's merge-and-reexport
per iteration. Keep Ollama as the dev/default; make the backend URL configurable.
- Ollama vs vLLM benchmark: https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking
- Unsloth vLLM/LoRA serving: https://docs.unsloth.ai/basics/inference-and-deployment/vllm-guide

### 4. Make resilience real (MEDIUM)
`meta-orchestrator` constructs `CircuitBreaker`/`retry_with_backoff` and never
calls them, and the primitives are synchronous (`time.sleep`) so they can't wrap
async calls anyway. Replace with an async-aware breaker actually applied to
downstream calls; narrow retries to idempotent GETs; make cache/Redis failures
degrade with an explicit metric instead of being indistinguishable from a normal
miss. Add FastAPI `lifespan` shutdown to close Redis/Chroma and cancel background
tasks.

### 5. Observability (MEDIUM)
Adopt the OpenTelemetry GenAI semantic conventions (`gen_ai.*` spans/metrics),
export traces to a self-hosted Langfuse, and scrape token/latency/queue metrics
in Prometheus. Only `localllm` and `reflection-agent` currently expose `/metrics`;
the Prometheus targets were corrected on this branch but most services remain
un-instrumented. Switch `logging.basicConfig` to structured logging with
correlation IDs (the code already passes `extra={}` fields that the current sink
drops).
- OTel GenAI conventions: https://opentelemetry.io/blog/2026/genai-observability/
- Langfuse OTel: https://langfuse.com/integrations/native/opentelemetry

### 6. Consider an LLM gateway (LiteLLM) (MEDIUM)
A unified OpenAI-compatible gateway (LiteLLM Proxy, MIT) in front of the
local backend(s) gives virtual API keys, per-caller budgets, fallbacks/load
balancing, and Redis-backed rate limiting/caching — and could replace bespoke
routing logic across the FastAPI services while reusing the existing Redis.
https://github.com/BerriAI/litellm

### 7. Kill code duplication; single-source the shared modules (MEDIUM)
`common/` is dead code — each service vendors its own copy of `auth.py`,
`cache_utils.py`, `error_handling.py`, `cline_utils.py`, and they have already
drifted (`common/cline_utils.py` logs user-prompt content that
`meta-orchestrator`'s copy was patched to redact). Package `common/` as an
installable dependency (or a shared base image) so fixes apply once.

### 8. Prompt-injection hardening for RAG + web-search (MEDIUM — security)
Treat retrieved web/RAG content strictly as data, never instructions
(OWASP LLM01/LLM08). Sanitize/validate documents before indexing; add access
control on the vector store (its `DELETE /collections/{name}` is destructive).
Gate the reflexion training corpus so injected content can't reach fine-tuning
data (LLM04 model poisoning).

### 9. Tests + CI (MEDIUM)
There are zero tests and no CI — which is why regressions shipped labeled
"production ready." Add a minimal CI that runs `docker compose build` plus a
smoke test hitting each `/health`, and unit tests for the auth validator, cache
keying, and task routing.

### 10. Non-root for the last two images (LOW)
`localllm` and `model-improvement` still run as root because they write to host
bind mounts (`./models`, `./data`, `./logs`, `./comparison_results`). Convert
those to named volumes (or align UIDs) and add `USER appuser`.

### RAG at scale (situational)
ChromaDB is fine for the current corpus size. If retrieval grows past a few
million vectors or needs heavy metadata filtering, Qdrant (or pgvector if you
already run Postgres) is the common production choice. Not urgent.

---

*Reviewed 2026-07-12. Sources reflect 2025–2026 self-hosted-LLM practice; the
inference-serving and OWASP-LLM recommendations are high-confidence consensus,
the RAG-database choice is situational.*
