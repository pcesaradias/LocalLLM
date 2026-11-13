# Graph Report - .  (2026-07-14)

## Corpus Check
- 94 files · ~55,917 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1088 nodes · 1482 edges · 90 communities (82 shown, 8 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 61 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- LangChain Agent Dependencies
- Vector DB Service (ChromaDB)
- Multimodal Agent (Vision)
- Resilience & Circuit Breaker
- Docs & Cloud Training Guides
- LangChain Agent Core
- Common Error Handling
- Common Cache Utils
- LocalLLM Cache Utils
- Meta Cache Utils
- Model Version Detector
- Model Improvement Service
- React UI
- Model Manager Service
- LocalLLM Auth & Admin
- Meta Model Routing
- Meta-Orchestrator Core
- LangChain Inference Backend
- Orchestration Workflows
- Model Version Monitor Scripts
- LocalLLM Inference Backend
- LocalLLM RAG & Sessions
- Multimodal Inference Backend
- Common API-Key Auth
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 83

## God Nodes (most connected - your core abstractions)
1. `internal_headers()` - 20 edges
2. `PromptCacheManager` - 18 edges
3. `ModelVersionDetector` - 17 edges
4. `APIKeyValidator` - 14 edges
5. `ClinePromptParser` - 14 edges
6. `create_error_response()` - 14 edges
7. `PromptCacheManager` - 14 edges
8. `create_error_response()` - 14 edges
9. `CircuitBreaker` - 13 edges
10. `AutomaticTester` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Pluggable OpenAI-Compatible Inference Backend` --semantically_similar_to--> `Groq Reference/Judge Model`  [INFERRED] [semantically similar]
  RECOMMENDATIONS.md → docs/superpowers/specs/2026-07-12-automatic-tester-design.md
- `Windows Ollama Setup & Testing Guide` --semantically_similar_to--> `vLLM Inference Server`  [INFERRED] [semantically similar]
  docs/WINDOWS_OLLAMA_SETUP_GUIDE.md → RECOMMENDATIONS.md
- `LearningSystem` --uses--> `APIKeyValidator`  [INFERRED]
  meta-orchestrator/main.py → common/auth.py
- `MetaRequest` --uses--> `APIKeyValidator`  [INFERRED]
  meta-orchestrator/main.py → common/auth.py
- `MetaResponse` --uses--> `APIKeyValidator`  [INFERRED]
  meta-orchestrator/main.py → common/auth.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Self-Improvement / Retraining Pipeline** — readme_self_improvement_loop, readme_reflexion_learning, docs_superpowers_specs_2026_07_12_automatic_tester_design_automatictester, readme_lora_fine_tuning, cloud_training_cloud_training_guide_google_colab [INFERRED 0.80]
- **Cloud LoRA Training Documentation Set** — cloud_training_readme_package, cloud_training_quick_start_guide, cloud_training_cloud_training_guide_guide, cloud_training_setup_summary_summary, cloud_training_cloud_training_guide_google_colab [EXTRACTED 0.85]
- **Production Hardening (compose + auth + CI + Redis)** — docker_compose_simplified_stack, recommendations_internal_service_auth, docker_compose_simplified_redis, _github_workflows_ci_pipeline [INFERRED 0.75]

## Communities (90 total, 8 thin omitted)

### Community 0 - "LangChain Agent Dependencies"
Cohesion: 0.05
Nodes (44): fastapi, langchain-agent/requirements.txt, httpx, langchain, langchain-community, langchain-core, langchain-openai, openai (+36 more)

### Community 1 - "Vector DB Service (ChromaDB)"
Cohesion: 0.08
Nodes (33): add_document(), add_documents_batch(), CollectionInfo, delete_collection(), Document, DocumentBatch, get_collection_stats(), health() (+25 more)

### Community 2 - "Multimodal Agent (Vision)"
Cohesion: 0.07
Nodes (33): analyze_document_endpoint(), analyze_image_endpoint(), CodeFromImageRequest, CodeFromImageResponse, CodeGenerationTool, DocumentAnalysisRequest, DocumentAnalysisResponse, DocumentParserTool (+25 more)

### Community 3 - "Resilience & Circuit Breaker"
Cohesion: 0.08
Nodes (32): authentication_error(), CircuitBreaker, create_error_response(), ErrorCategory, ErrorResponse, internal_error(), invalid_request_error(), model_error() (+24 more)

### Community 4 - "Docs & Cloud Training Guides"
Cohesion: 0.15
Nodes (29): CI Pipeline, Google Colab (T4 GPU), Cloud GPU Training Guide, Cloud Training Quick Start, Cloud GPU Training Package README, Cloud Training Setup Summary, Deploy LocalLLM on Google Cloud, Redis Cache (+21 more)

### Community 5 - "LangChain Agent Core"
Cohesion: 0.11
Nodes (23): BaseTool, ConversationBufferMemory, chat_endpoint(), ChatRequest, ChatResponse, CodeAnalysisTool, create_agent(), get_best_model_for_task() (+15 more)

### Community 6 - "Common Error Handling"
Cohesion: 0.11
Nodes (27): authentication_error(), create_error_response(), ErrorCategory, ErrorResponse, internal_error(), invalid_request_error(), model_error(), not_found_error() (+19 more)

### Community 7 - "Common Cache Utils"
Cohesion: 0.10
Nodes (16): create_cache_manager(), PromptCacheManager, Any, Redis, Prompt Caching Utilities for LocalLLM Services  Provides: - Intelligent cache ke, Get cached response if available          Args:             prompt: The prompt t, Cache a response          Args:             prompt: The prompt text, Intelligent prompt caching with semantic similarity matching      Features: (+8 more)

### Community 8 - "LocalLLM Cache Utils"
Cohesion: 0.10
Nodes (16): create_cache_manager(), PromptCacheManager, Any, Redis, Prompt Caching Utilities for LocalLLM Services  Provides: - Intelligent cache ke, Get cached response if available          Args:             prompt: The prompt t, Cache a response          Args:             prompt: The prompt text, Intelligent prompt caching with semantic similarity matching      Features: (+8 more)

### Community 9 - "Meta Cache Utils"
Cohesion: 0.10
Nodes (16): create_cache_manager(), PromptCacheManager, Any, Redis, Prompt Caching Utilities for LocalLLM Services  Provides: - Intelligent cache ke, Get cached response if available          Args:             prompt: The prompt t, Cache a response          Args:             prompt: The prompt text, Intelligent prompt caching with semantic similarity matching      Features: (+8 more)

### Community 10 - "Model Version Detector"
Cohesion: 0.11
Nodes (14): main(), ModelVersionDetector, Model Version Detector  Monitors for new model versions from: 1. Ollama library, Detect new models that weren't known before, Check Ollama library for models not yet downloaded         Returns list of avail, Get detailed information about a model, Pull a new model from Ollama library         This is a long-running operation, Detects new model versions from various sources (+6 more)

### Community 11 - "Model Improvement Service"
Cohesion: 0.09
Nodes (23): detect_new_models(), get_available_downloads(), get_improvement_status(), get_model_recommendations(), get_model_status(), health_check(), ImprovementStatus, list_improvement_tasks() (+15 more)

### Community 12 - "React UI"
Cohesion: 0.09
Nodes (22): axios, react, react-dom, recharts, dependencies, axios, react, react-dom (+14 more)

### Community 13 - "Model Manager Service"
Cohesion: 0.10
Nodes (22): analyze_model_performance(), auto_upgrade_models(), calculate_model_score(), check_model_updates(), generate_reflection_analysis(), get_model(), get_models(), health_check() (+14 more)

### Community 14 - "LocalLLM Auth & Admin"
Cohesion: 0.10
Nodes (17): HTTPAuthorizationCredentials, delete_model(), generate_api_key(), get_learning_insights(), get_stats(), list_models(), ModelInfo, pull_model() (+9 more)

### Community 15 - "Meta Model Routing"
Cohesion: 0.10
Nodes (14): create_model_router(), ModelRouter, Any, Intelligent Model Routing  Advanced model selection for optimal coding quality u, Get model for specific LoRA profile.          Args:             profile: LoRA pr, Analyze task complexity from prompt and context.          Args:             prom, Task complexity levels, Get routing statistics. (+6 more)

### Community 16 - "Meta-Orchestrator Core"
Cohesion: 0.15
Nodes (19): detect_coding_profile(), _determine_workflow_type(), _fallback_to_localllm(), health_check(), intelligent_chat(), list_services(), MetaRequest, MetaResponse (+11 more)

### Community 17 - "LangChain Inference Backend"
Cohesion: 0.24
Nodes (17): backend(), generate(), generate_sync(), generate_vision(), list_models(), _ollama_url(), _openai_headers(), _openai_url() (+9 more)

### Community 18 - "Orchestration Workflows"
Cohesion: 0.18
Nodes (11): Any, TypedDict, Analyze image and extract UI components, Generate code from visual analysis, Test and validate generated code, Refine code based on test results, Simple code validation (placeholder for actual testing), Vision-to-Code workflow for converting UI designs to production code (+3 more)

### Community 19 - "Model Version Monitor Scripts"
Cohesion: 0.17
Nodes (16): check_huggingface_version(), check_ollama_version(), detect_new_version(), load_known_versions(), main(), Model Version Monitor Automatically detects new Qwen model releases and triggers, Create trigger file to start fine-tuning, Send notification about new version (placeholder) (+8 more)

### Community 20 - "LocalLLM Inference Backend"
Cohesion: 0.26
Nodes (15): backend(), generate(), generate_vision(), list_models(), _ollama_url(), _openai_headers(), _openai_url(), Any (+7 more)

### Community 21 - "LocalLLM RAG & Sessions"
Cohesion: 0.16
Nodes (14): analyze_conversation_history(), analyze_session(), augment_prompt_with_context(), ChatResponse, Any, Retrieve relevant context from vector database, Augment user prompt with retrieved context, Enhanced chat with reflection and reasoning (+6 more)

### Community 22 - "Multimodal Inference Backend"
Cohesion: 0.26
Nodes (15): backend(), generate(), generate_vision(), list_models(), _ollama_url(), _openai_headers(), _openai_url(), Any (+7 more)

### Community 23 - "Common API-Key Auth"
Cohesion: 0.17
Nodes (10): APIKeyValidator, create_validator_dependency(), Redis, Shared authentication module for all Local LLM services Provides unified API key, Check and enforce rate limits          Args:             key_hash: SHA256 hash o, Migrate a legacy API key from environment variable to Redis          Args:, Validates API keys against Redis storage with permission and rate limit checks, Create a FastAPI dependency function for API key validation      Args:         r (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (10): ClinePromptParser, parse_cline_message(), Cline Prompt Parser - Extract user queries from Cline's verbose internal prompts, Determine if we should apply our enhancements (reflection, caching, etc.), Convenience function to parse a Cline message      Args:         message: Raw me, Parser for Cline's structured prompts, Detect if a message is from Cline (contains internal tags)          Args:, Extract the actual user query from Cline's verbose prompt          Cline format (+2 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (10): APIKeyValidator, create_validator_dependency(), Redis, Shared authentication module for all Local LLM services Provides unified API key, Check and enforce rate limits          Args:             key_hash: SHA256 hash o, Migrate a legacy API key from environment variable to Redis          Args:, Validates API keys against Redis storage with permission and rate limit checks, Create a FastAPI dependency function for API key validation      Args:         r (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (15): anthropic, fastapi, model-improvement-service/requirements.txt, httpx, pydantic, redis, requests, uvicorn (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (14): execute_workflow(), get_workflow_result(), list_workflows(), BaseModel, Enum, str, Execute a multi-agent workflow, Get workflow result by ID (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.19
Nodes (14): check_for_new_models(), create_modelfile(), deploy_model(), get_model_hash(), load_deployed_models(), main(), Automatic LoRA Model Deployment Watches for new models and deploys them automati, Check for new or updated models (+6 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (15): chromadb, fastapi, vector-db-service/requirements.txt, numpy, pydantic, python-multipart, requests, sentence-transformers (+7 more)

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (8): BackgroundProcessCleaner, main(), Automatic cleanup for background bash processes, Initialize cleaner          Args:             redis_url: Redis connection URL, Get all bash process keys from Redis, Clean up old background processes, Clean up processes based on age (if metadata available), Run as daemon, cleaning up periodically          Args:             interval_seco

### Community 31 - "Community 31"
Cohesion: 0.20
Nodes (13): generate_weekly_report(), load_history(), main(), Weekly Complete Improvement System  Runs automatically every week (Monday 2 AM):, Generate weekly improvement report, Send email report (optional), Run weekly improvement, Load historical improvement data (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.18
Nodes (13): clean_html(), collect_from_stackoverflow(), fetch_stackoverflow_questions(), get_question_answers(), process_question_answer_pair(), Stack Overflow Dataset Collection Script Collects Q&A pairs from Stack Overflow, Process Q&A pair into instruction-response format, Collect Q&A pairs from Stack Overflow (+5 more)

### Community 33 - "Community 33"
Cohesion: 0.22
Nodes (8): ClinePromptParser, parse_cline_message(), Cline Prompt Parser - Extract user queries from Cline's verbose internal prompts, Determine if we should apply our enhancements (reflection, caching, etc.), Convenience function to parse a Cline message      Args:         message: Raw me, Parser for Cline's structured prompts, Detect if a message is from Cline (contains internal tags)          Args:, Extract the actual user query from Cline's verbose prompt          Cline format

### Community 34 - "Community 34"
Cohesion: 0.18
Nodes (9): get_performance_metrics(), LearningSystem, Intelligent learning system for model selection and optimization, Record performance data for learning, Calculate intelligent score for service selection, Select the best service for a given task, Route endpoint - returns routing decision without executing (requires authentica, Get performance metrics for all services (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.15
Nodes (12): author, dependencies, playwright, description, keywords, license, main, name (+4 more)

### Community 36 - "Community 36"
Cohesion: 0.15
Nodes (12): aiohttp, fastapi, httpx, numpy, prometheus-client, pydantic, python-dotenv, python-multipart (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (13): accelerate, beautifulsoup4, bitsandbytes, datasets, scripts/lora_profiles/lora_requirements.txt, numpy, pandas, peft (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (12): collect_dataset(), create_ollama_modelfile(), main(), merge_datasets(), Master Training Script - Train All LoRA Profiles Automates dataset collection an, Merge GitHub and Stack Overflow datasets, Train LoRA adapter for a profile, Create Ollama Modelfile for profile (+4 more)

### Community 39 - "Community 39"
Cohesion: 0.23
Nodes (11): categorize_example(), create_training_report(), main(), merge_weekly_data(), Monthly Unsloth Automation Script Merges all weekly reflexion data and triggers, Categorize training example into a profile based on content, Create a report of what will be trained, Instructions for syncing to Google Drive (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.21
Nodes (11): clean_code(), collect_from_github(), extract_function_or_class(), generate_instruction(), GitHub Dataset Collection Script Collects code examples from top GitHub reposito, Generate instruction prompt from filename and code, Collect code examples from GitHub for the specified profile, Save examples to JSONL file (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.27
Nodes (11): health_check(), BaseModel, Web Search Service - Real-time web search for your Local LLM Uses DuckDuckGo (fr, Search web and have LLM summarize the results     Returns answer with sources, Health check endpoint, Search the web using DuckDuckGo     Returns top results with title, URL, and sni, search_and_summarize(), SearchRequest (+3 more)

### Community 42 - "Community 42"
Cohesion: 0.29
Nodes (3): AutomaticTester, Automatic self-improvement engine for the model-improvement-service.  Runs a cur, Blind A/B judgement. Returns 'A' | 'B' | 'TIE'.

### Community 44 - "Community 44"
Cohesion: 0.27
Nodes (6): ModelManagerIntegration, Any, Integration with model manager for intelligent model selection, Get recommended model from model manager, Fallback model selection when model manager is unavailable, Analyze model performance using reflection

### Community 45 - "Community 45"
Cohesion: 0.22
Nodes (7): Enum, str, Intelligent task classification system, Classify task type based on message content and context, Get required capabilities for a task type, TaskClassifier, TaskType

### Community 46 - "Community 46"
Cohesion: 0.27
Nodes (9): create_lora_config(), fine_tune_lora(), format_training_data(), load_model_and_tokenizer(), LoRA Fine-Tuning Script for Coding Profiles Trains profile-specific LoRA adapter, Format dataset example with profile-specific system prompt, Main fine-tuning function, Load base model with optional 4-bit quantization (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.25
Nodes (9): BackgroundTasks, Test a model and generate improvement training data      Runs full comparison te, Run automatic improvement on all new models detected      This is the main endpo, Report improvement results to meta-orchestrator      This updates the learning s, Background task to run improvement pipeline      This is the main automatic impr, report_improvement_to_orchestrator(), run_automatic_improvement(), run_improvement_pipeline() (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.28
Nodes (5): CircuitBreaker, HTTPException, Circuit breaker pattern implementation      States:     - CLOSED: Normal operati, Execute function with circuit breaker protection, Handle successful call

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (6): _make_tester(), Unit tests for the automatic_tester self-improvement engine.  HTTP calls are mon, test_judge_parsing(), test_skips_failed_prompts(), test_win_rate_all_local_loses_builds_dataset(), test_win_rate_all_local_wins()

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (8): internal_headers(), Authorization header for outbound calls to internal services., Scheduled task to automatically check for and apply upgrades, Initialize model configurations in Redis and start scheduled tasks, scheduled_auto_upgrade(), startup_event(), health_check(), Health check endpoint

### Community 51 - "Community 51"
Cohesion: 0.32
Nodes (7): chat_endpoint(), chat_stream_endpoint(), ChatRequest, Stream chat responses using Server-Sent Events, Store a conversation turn in Redis for history tracking and analysis, Stream chat responses using Server-Sent Events (SSE), store_conversation_turn()

### Community 52 - "Community 52"
Cohesion: 0.36
Nodes (5): BaseModel, Analyze and reflect on a model's response to provide improvements., reflect_on_response(), ReflectionRequest, ReflectionResponse

### Community 53 - "Community 53"
Cohesion: 0.38
Nodes (6): format_prompts(), main(), Train all profiles sequentially, Format dataset for Qwen chat template, Train a single LoRA profile, train_profile()

### Community 54 - "Community 54"
Cohesion: 0.47
Nodes (5): check_environment(), main(), Check GPU and CUDA availability, Train a single LoRA profile, train_profile()

### Community 55 - "Community 55"
Cohesion: 0.33
Nodes (6): POST /chat API endpoint (localhost:8080), FastAPI + React tech stack, index.html landing page, GitHub repository link button, self-improving AI system demo, stats dashboard cards (win rate, cost, speed)

### Community 56 - "Community 56"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (3): EnhancedLLMService, Load available models from Ollama, Check for model updates and download new versions

### Community 58 - "Community 58"
Cohesion: 0.33
Nodes (6): periodic_model_loading(), Schedule background model update checks, Start all background tasks, Periodically reload available models, schedule_model_updates(), start_background_tasks()

### Community 59 - "Community 59"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 60 - "Community 60"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 62 - "Community 62"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 64 - "Community 64"
Cohesion: 0.53
Nodes (4): App(), CHART_COLORS, defaultApiBase(), resolveInitialTheme()

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (5): internal_headers(), Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., Authorization header for outbound calls to internal services., require_internal_key()

### Community 67 - "Community 67"
Cohesion: 0.50
Nodes (5): BaseModel, Analyze and improve model responses using reflection, reflect_endpoint(), ReflectRequest, ReflectResponse

### Community 68 - "Community 68"
Cohesion: 0.40
Nodes (3): DocumentAutomationWorkflow, Document automation workflow for technical documentation, Execute document automation workflow

### Community 69 - "Community 69"
Cohesion: 0.40
Nodes (3): QualityControlWorkflow, Quality control workflow for visual inspection, Execute quality control workflow

### Community 70 - "Community 70"
Cohesion: 0.40
Nodes (5): ui/index.html React app entry, Local LLM Manager UI purpose, /src/main.jsx module entry, #root mount element, Vite bundler

### Community 71 - "Community 71"
Cohesion: 0.50
Nodes (3): Shared internal service-to-service authentication.  Backend services that are on, FastAPI dependency: require a valid internal bearer token when configured., require_internal_key()

### Community 72 - "Community 72"
Cohesion: 0.50
Nodes (4): monitoring_loop(), Start background monitoring loop, Continuous monitoring loop      Checks for new models every 6 hours and automati, startup_event()

### Community 74 - "Community 74"
Cohesion: 0.67
Nodes (3): fastapi, tests/requirements-test.txt, pytest

## Knowledge Gaps
- **131 isolated node(s):** `name`, `version`, `description`, `main`, `test` (+126 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `internal_headers()` connect `Community 50` to `LangChain Agent Core`, `Community 71`, `Model Improvement Service`, `Community 44`, `Model Manager Service`, `LocalLLM Auth & Admin`, `Community 47`, `Meta-Orchestrator Core`, `Orchestration Workflows`, `LocalLLM RAG & Sessions`, `Community 27`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `CircuitBreaker` connect `Community 48` to `Community 34`, `Common Error Handling`, `Community 44`, `Community 45`, `Meta-Orchestrator Core`, `Community 24`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `ModelVersionDetector` connect `Model Version Detector` to `Model Improvement Service`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `PromptCacheManager` (e.g. with `ChatRequest` and `ChatResponse`) actually correct?**
  _`PromptCacheManager` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ModelVersionDetector` (e.g. with `ImprovementStatus` and `ModelPullRequest`) actually correct?**
  _`ModelVersionDetector` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `APIKeyValidator` (e.g. with `LearningSystem` and `MetaRequest`) actually correct?**
  _`APIKeyValidator` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ClinePromptParser` (e.g. with `LearningSystem` and `MetaRequest`) actually correct?**
  _`ClinePromptParser` has 7 INFERRED edges - model-reasoned connections that need verification._