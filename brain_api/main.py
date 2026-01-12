"""
FastAPI wrapper for the Python Brain (Multi-Agent System)
This exposes the LanGraph agents as HTTP API endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import os
import json
import asyncio
from queue import Queue
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ChromaDB loader (downloads database from GitHub Releases if not present)
from .chromadb_loader import ensure_chromadb_available

# Import the graph components
from src.graph import app as graph_app, librarian, critic
from src.agents.consensus import ConsensusManager
from src.tools.visual_generator import VisualGenerator
from langchain_core.messages import HumanMessage, AIMessage

# Initialize visual generator (lazy load to avoid errors if no API key)
visual_generator = None
def get_visual_generator():
    global visual_generator
    if visual_generator is None:
        try:
            visual_generator = VisualGenerator()
        except Exception as e:
            print(f"[WARN] Visual generator not initialized: {e}")
    return visual_generator

# Initialize FastAPI
api = FastAPI(
    title="GeoTutor Brain API",
    description="Multi-Agent Geotechnical Engineering AI System",
    version="1.0.0"
)

# Startup event: ensure ChromaDB is available
@api.on_event("startup")
async def startup_event():
    """Download ChromaDB from GitHub Releases if not present."""
    print("[Startup] Checking ChromaDB availability...")
    success = ensure_chromadb_available()
    if success:
        print("[Startup] ChromaDB ready!")
    else:
        print("[Startup] WARNING: ChromaDB not available - retrieval will fail")

# CORS middleware for TypeScript backend to call
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for SSE compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None  # For learning project context
    visualType: Optional[str] = None  # flowchart, diagram, infographic, illustration
    includeVisual: bool = False

class QuestionResponse(BaseModel):
    answer: str
    critique: str
    mindmapPath: Optional[str] = None
    visualPath: Optional[str] = None
    visualBase64: Optional[str] = None
    context: Optional[str] = None
    plan: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

# Health check endpoint
@api.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "GeoTutor Brain API",
        "version": "1.0.0"
    }

# Main question-answering endpoint (original, non-streaming)
@api.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Process a question through the multi-agent brain system
    
    Flow:
    1. Librarian retrieves context from knowledge base
    2. Router determines if it's an exam or consensus question
    3. Consensus manager runs multi-agent deliberation
    4. Critic reviews the final answer
    5. Returns comprehensive response
    """
    try:
        # Prepare the question with additional context if provided
        question_text = request.question
        if request.context:
            question_text = f"Context: {request.context}\n\nQuestion: {request.question}"
        
        # Run the LanGraph workflow
        inputs = {"messages": [HumanMessage(content=question_text)]}
        result = graph_app.invoke(inputs)
        
        # Extract results
        answer = result.get("result", "No response generated.")
        critique = result.get("critique", "")
        mindmap_path = result.get("mindmap_path", "")
        context = result.get("context", "")
        plan = result.get("plan", "")
        
        return QuestionResponse(
            answer=answer,
            critique=critique,
            mindmapPath=mindmap_path if mindmap_path else None,
            context=context if context else None,
            plan=plan if plan else None,
            success=True,
            error=None
        )
        
    except Exception as e:
        # Return error but don't crash
        return QuestionResponse(
            answer="",
            critique="",
            success=False,
            error=str(e)
        )


# SSE Streaming endpoint
@api.post("/ask-stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Process a question with real-time streaming of agent progress.
    
    Returns Server-Sent Events (SSE) with the following event types:
    - progress: Agent status updates (stage, agent, status, detail)
    - result: Final answer when complete
    - error: Any errors that occur
    """
    
    async def generate_events() -> AsyncGenerator[str, None]:
        # Queue to receive progress events from sync threads
        progress_queue: Queue = Queue()
        result_holder = {"answer": "", "critique": "", "error": None, "visual_path": None, "visual_base64": None}
        
        def progress_callback(stage: str, agent: str, status: str, detail: Optional[str]):
            """Callback that puts progress events into the queue"""
            event_data = {
                "type": "progress",
                "stage": stage,
                "agent": agent,
                "status": status,
                "detail": detail or ""
            }
            progress_queue.put(event_data)
        
        def run_consensus():
            """Run the consensus process in a separate thread"""
            try:
                question_text = request.question
                if request.context:
                    question_text = f"Context: {request.context}\n\nQuestion: {request.question}"
                
                # Stage 0: Librarian retrieves context
                progress_queue.put({
                    "type": "progress",
                    "stage": "retrieving",
                    "agent": "Librarian",
                    "status": "started",
                    "detail": "Searching knowledge base..."
                })
                
                context = librarian.retrieve(question_text)
                
                progress_queue.put({
                    "type": "progress",
                    "stage": "retrieving",
                    "agent": "Librarian",
                    "status": "done",
                    "detail": f"Found {len(context.split())} words of context"
                })
                
                # Create consensus manager with progress callback
                consensus = ConsensusManager(on_progress=progress_callback)
                
                # Run the 3-stage consensus
                responses = consensus.stage1_collect_responses(question_text, context)
                rankings, label_map = consensus.stage2_collect_rankings(responses)
                final_answer = consensus.stage3_synthesize_final(question_text, responses, rankings, label_map)
                
                # Critic review
                progress_queue.put({
                    "type": "progress",
                    "stage": "reviewing",
                    "agent": "Critic",
                    "status": "started",
                    "detail": "Reviewing final answer..."
                })
                
                critique = critic.review(question_text, "Consensus Plan", "N/A", final_answer)
                
                progress_queue.put({
                    "type": "progress",
                    "stage": "reviewing",
                    "agent": "Critic",
                    "status": "done",
                    "detail": "Review complete"
                })
                
                result_holder["answer"] = final_answer
                result_holder["critique"] = critique
                
                # Generate visual if requested
                if request.includeVisual and request.visualType:
                    progress_queue.put({
                        "type": "progress",
                        "stage": "visualizing",
                        "agent": "Visualizer",
                        "status": "started",
                        "detail": f"Generating {request.visualType} visualization..."
                    })
                    
                    try:
                        gen = get_visual_generator()
                        if gen:
                            visual_result = gen.generate(
                                visual_type=request.visualType,
                                llm_response=final_answer,
                                topic_summary=question_text[:100]
                            )
                            
                            if visual_result["success"]:
                                result_holder["visual_path"] = visual_result["image_path"]
                                result_holder["visual_base64"] = visual_result["image_base64"]
                                progress_queue.put({
                                    "type": "progress",
                                    "stage": "visualizing",
                                    "agent": "Visualizer",
                                    "status": "done",
                                    "detail": "Visual generated successfully"
                                })
                            else:
                                progress_queue.put({
                                    "type": "progress",
                                    "stage": "visualizing",
                                    "agent": "Visualizer",
                                    "status": "done",
                                    "detail": f"Visual generation skipped: {visual_result.get('error', 'Unknown error')}"
                                })
                        else:
                            progress_queue.put({
                                "type": "progress",
                                "stage": "visualizing",
                                "agent": "Visualizer",
                                "status": "done",
                                "detail": "Visual generator not available (missing API key)"
                            })
                    except Exception as ve:
                        progress_queue.put({
                            "type": "progress",
                            "stage": "visualizing",
                            "agent": "Visualizer",
                            "status": "error",
                            "detail": f"Visual generation failed: {str(ve)}"
                        })
                    
                    # Mark stage as complete
                    progress_queue.put({
                        "type": "progress",
                        "stage": "visualizing",
                        "agent": "system",
                        "status": "done",
                        "detail": "Visualization phase complete"
                    })
                
            except Exception as e:
                result_holder["error"] = str(e)
                progress_queue.put({
                    "type": "error",
                    "message": str(e)
                })
            finally:
                # Signal completion
                progress_queue.put(None)
        
        # Start the consensus process in a background thread
        thread = Thread(target=run_consensus)
        thread.start()
        
        # Yield SSE events as they arrive
        while True:
            try:
                # Check for events with a timeout to allow async cooperation
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
                while not progress_queue.empty():
                    event = progress_queue.get_nowait()
                    
                    if event is None:
                        # Process complete, send final result
                        if result_holder["error"]:
                            final_event = {
                                "type": "error",
                                "message": result_holder["error"]
                            }
                        else:
                            final_event = {
                                "type": "result",
                                "answer": result_holder["answer"],
                                "critique": result_holder["critique"],
                                "visualPath": result_holder.get("visual_path"),
                                "visualBase64": result_holder.get("visual_base64"),
                                "success": True
                            }
                        yield f"data: {json.dumps(final_event)}\n\n"
                        return
                    
                    # Send progress event
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                error_event = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_event)}\n\n"
                return
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# Exam generation endpoint
@api.post("/generate-exam")
async def generate_exam(topic: str, num_questions: int = 5):
    """
    Generate an exam sheet using the Exam Council
    """
    try:
        query = f"Generate an exam with {num_questions} questions about: {topic}"
        inputs = {"messages": [HumanMessage(content=query)]}
        result = graph_app.invoke(inputs)
        
        exam_text = result.get("result", "")
        
        return {
            "success": True,
            "examContent": exam_text,
            "topic": topic
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# System info endpoint
@api.get("/system/info")
def get_system_info():
    return {
        "agents": [
            "LibrarianAgent - Retrieves context from knowledge base",
            "ConsensusManager - Multi-agent deliberation system",
            "CriticAgent - Reviews and validates answers",
            "ExamCouncil - Generates exam materials",
            "Visualizer - Creates concept maps"
        ],
        "capabilities": [
            "Multi-agent consensus answering",
            "Knowledge base retrieval",
            "Exam generation",
            "Concept map visualization",
            "Critical review",
            "Real-time streaming progress"
        ],
        "endpoints": {
            "/ask": "POST - Standard question answering",
            "/ask-stream": "POST - Streaming question answering with progress updates (SSE)",
            "/generate-exam": "POST - Generate exam questions",
            "/system/info": "GET - System information"
@api.get("/system/models")
def list_models():
    """Diagnostic endpoint to list available models."""
    try:
        from src.tools.visual_generator import get_visual_generator
        gen = get_visual_generator()
        models = gen.client.models.list()
        return {
            "success": True,
            "models": [m.name for m in models]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
    ========================================
    🧠 GeoTutor Brain API Starting...
    ========================================
    
    Server: http://localhost:{port}
    Docs: http://localhost:{port}/docs
    
    Agents initialized:
    - Librarian (RAG)
    - Consensus Manager (Multi-agent)
    - Critic (Validation)
    - Exam Council (Generation)
    - Visualizer (Concept Maps)
    
    NEW: Streaming endpoint at /ask-stream
    
    Ready to serve GeoTutor frontend!
    ========================================
    """)
    
    uvicorn.run(
        "main:api",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
