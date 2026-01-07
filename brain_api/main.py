"""
FastAPI wrapper for the Python Brain (Multi-Agent System)
This exposes the LanGraph agents as HTTP API endpoints
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the graph
from src.graph import app as graph_app
from langchain_core.messages import HumanMessage

# Initialize FastAPI
api = FastAPI(
    title="GeoTutor Brain API",
    description="Multi-Agent Geotechnical Engineering AI System",
    version="1.0.0"
)

# CORS middleware for TypeScript backend to call
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # TypeScript backend + React frontend
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

# Main question-answering endpoint
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
            "Critical review"
        ]
    }

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
