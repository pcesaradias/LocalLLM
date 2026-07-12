from fastapi import FastAPI, HTTPException, Depends
from starlette.concurrency import run_in_threadpool
from internal_auth import require_internal_key, internal_headers
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import inference
import json
import redis
import os
from langchain.llms import Ollama
try:
    from langchain_openai import ChatOpenAI
except ImportError as e:
    raise ImportError(
        "langchain-openai is required for INFERENCE_BACKEND=openai. "
        "Install it: pip install langchain-openai==0.1.7"
    ) from e
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LangChain Agent Service", version="1.0.0")

# Initialize Redis for caching
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Initialize Ollama LLM
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
model_manager_url = os.getenv("MODEL_MANAGER_URL", "http://localhost:8005")
model_name = os.getenv("MODEL_NAME", "qwen3-coder:latest")

# Inference backend selection. Defaults to "ollama" so existing deployments are
# unaffected; set INFERENCE_BACKEND=openai to point the agent LLM at any
# OpenAI-compatible endpoint (vLLM/Groq/OpenRouter) via OPENAI_BASE_URL.
inference_backend = os.getenv("INFERENCE_BACKEND", "ollama")

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    reasoning: Optional[str] = None
    tools_used: List[str] = []

class ReflectionRequest(BaseModel):
    question: str
    initial_response: str
    context: Optional[Dict[str, Any]] = None

class ReflectionResponse(BaseModel):
    improved_response: str
    reflection_notes: str
    confidence_score: float

# Custom tools for the agent
class CodeAnalysisTool(BaseTool):
    name = "code_analyzer"
    description = "Analyzes code for bugs, performance issues, and best practices"

    def _run(self, code: str) -> str:
        prompt = f"""
        Analyze the following code and provide feedback:
        
        Code:
        {code}
        
        Please analyze for:
        1. Potential bugs or errors
        2. Performance issues
        3. Code style and best practices
        4. Security concerns
        5. Suggestions for improvement
        
        Provide detailed feedback in a structured format.
        """
        
        try:
            result = inference.generate_sync(model_name, prompt, temperature=0.3, timeout=120)
            return result
        except Exception as e:
            return f"Error analyzing code: {str(e)}"

    async def _arun(self, code: str) -> str:
        return self._run(code)

class ResearchTool(BaseTool):
    name = "researcher"
    description = "Researches topics and provides detailed information"

    def _run(self, topic: str) -> str:
        prompt = f"""
        Research and provide comprehensive information about: {topic}
        
        Include:
        1. Key concepts and definitions
        2. Important facts and details
        3. Related topics and connections
        4. Practical applications
        5. Common misconceptions
        
        Provide well-structured, detailed information.
        """
        
        try:
            result = inference.generate_sync(model_name, prompt, temperature=0.5, timeout=120)
            return result
        except Exception as e:
            return f"Error researching: {str(e)}"

    async def _arun(self, topic: str) -> str:
        return self._run(topic)

# Initialize tools
tools = [
    CodeAnalysisTool(),
    ResearchTool(),
]

# Per-conversation memory cache. Isolates each conversation's buffer so users'
# histories never bleed into one another. FIFO-evicted once it exceeds the cap.
_MAX_CONVERSATIONS = 1000
_conversation_memories: dict[str, ConversationBufferMemory] = {}

def _new_memory() -> ConversationBufferMemory:
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def get_conversation_memory(conversation_id: str) -> ConversationBufferMemory:
    """Return the memory for a conversation, creating it if absent.

    Evicts the oldest conversation (FIFO) once the cache exceeds _MAX_CONVERSATIONS.
    """
    memory = _conversation_memories.get(conversation_id)
    if memory is None:
        if len(_conversation_memories) >= _MAX_CONVERSATIONS:
            oldest_id = next(iter(_conversation_memories))
            del _conversation_memories[oldest_id]
        memory = _new_memory()
        _conversation_memories[conversation_id] = memory
    return memory

def get_best_model_for_task(task_type: str) -> str:
    """Get the best model for a specific task type using the model manager"""
    try:
        response = requests.get(
            f"{model_manager_url}/recommend-model",
            params={"task_type": task_type},
            headers=internal_headers(),
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("recommended_model", model_name)
        else:
            logger.warning(f"Failed to get model recommendation, using default: {model_name}")
            return model_name
    except Exception as e:
        logger.warning(f"Error getting model recommendation: {str(e)}, using default: {model_name}")
        return model_name

# Initialize the LLM. Ollama remains the default; INFERENCE_BACKEND=openai swaps
# in ChatOpenAI, which accepts any OpenAI-compatible base_url.
def _build_llm():
    if inference_backend.lower() == "openai":
        return ChatOpenAI(
            model=model_name,
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
        )
    return Ollama(
        base_url=ollama_base_url,
        model=model_name,
        temperature=0.7,
    )

llm = _build_llm()

# Build a conversational agent bound to the given per-conversation memory
def create_agent(memory: ConversationBufferMemory):
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, _auth: bool = Depends(require_internal_key)):
    """Enhanced chat endpoint with reasoning and tool usage"""
    try:
        # Check cache first
        cache_key = f"chat:{request.conversation_id}:{hash(request.message)}"
        cached_response = redis_client.get(cache_key)
        
        if cached_response:
            logger.info("Returning cached response")
            return ChatResponse(**json.loads(cached_response))
        
        # Resolve per-conversation memory so buffers never bleed across users;
        # fall back to ephemeral memory when no conversation_id is provided.
        if request.conversation_id:
            memory = get_conversation_memory(request.conversation_id)
        else:
            memory = _new_memory()
        agent = create_agent(memory)

        # Use the agent for enhanced reasoning
        response = await run_in_threadpool(agent.run, input=request.message)
        
        # Extract tools used from the agent's execution
        tools_used = []
        if hasattr(agent, 'agent_executor'):
            # This would need to be adapted based on actual agent execution tracking
            tools_used = ["reasoning_agent"]
        
        result = ChatResponse(
            response=response,
            conversation_id=request.conversation_id or "default",
            reasoning="Enhanced reasoning through LangChain agent",
            tools_used=tools_used
        )
        
        # Cache the response
        redis_client.setex(cache_key, 3600, json.dumps(result.dict()))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reflect", response_model=ReflectionResponse)
async def reflect_endpoint(request: ReflectionRequest, _auth: bool = Depends(require_internal_key)):
    """Reflection endpoint for self-improvement and verification"""
    try:
        reflection_prompt = f"""
        You are a reflection agent. Analyze the following:
        
        Question: {request.question}
        Initial Response: {request.initial_response}
        Context: {request.context or 'No additional context provided'}
        
        Please:
        1. Critique the initial response for accuracy, completeness, and clarity
        2. Identify any potential improvements or corrections
        3. Provide an improved version of the response
        4. Rate your confidence in the improved response (0.0 to 1.0)
        
        Format your response as:
        CRITIQUE: [your critique]
        IMPROVED_RESPONSE: [improved response]
        CONFIDENCE: [confidence score]
        """
        
        reflection_text = await run_in_threadpool(
            inference.generate_sync, model_name, reflection_prompt, 0.3, None, 120
        )

        # Parse the reflection response
        lines = reflection_text.split('\n')
        critique = ""
        improved_response = ""
        confidence = 0.7  # default

        for line in lines:
            if line.startswith("CRITIQUE:"):
                critique = line.replace("CRITIQUE:", "").strip()
            elif line.startswith("IMPROVED_RESPONSE:"):
                improved_response = line.replace("IMPROVED_RESPONSE:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.7

        return ReflectionResponse(
            improved_response=improved_response or reflection_text,
            reflection_notes=critique,
            confidence_score=confidence
        )

    except Exception as e:
        logger.error(f"Error in reflection endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "langchain-agent"}

@app.get("/models")
async def list_models(_auth: bool = Depends(require_internal_key)):
    """List available models"""
    try:
        response = await run_in_threadpool(requests.get, f"{ollama_base_url}/api/tags", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch models")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
