"""
API routes for CloudCost AI™
AI-powered instance recommendations + Conversational AI
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.ai_recommender import CloudCostAI
from src.services.conversational_ai import ConversationalAI

router = APIRouter(prefix="/ai", tags=["CloudCost AI"])


class AIRecommendationRequest(BaseModel):
    """Request model for AI recommendations"""
    
    min_vcpus: int = Field(..., ge=1, le=256, description="Minimum vCPUs required")
    min_memory_gb: float = Field(..., ge=0.5, le=4096, description="Minimum memory in GB")
    workload_type: Literal["web_app", "database", "compute_intensive", "memory_intensive", "ml_training", "general"] = Field(
        default="general",
        description="Type of workload"
    )
    traffic_pattern: Literal["steady", "variable", "spiky"] = Field(
        default="steady",
        description="Traffic pattern"
    )
    providers: Optional[List[str]] = Field(
        default=None,
        description="Cloud providers to consider (aws, gcp, azure)"
    )
    max_monthly_budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum monthly budget in USD"
    )
    spot_eligible: bool = Field(
        default=True,
        description="Whether spot/preemptible instances are acceptable"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of recommendations"
    )


@router.post("/recommend")
async def get_ai_recommendations(
    request: AIRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered instance recommendations
    
    **CloudCost AI™** analyzes your requirements and recommends the best instances
    across AWS, GCP, and Azure.
    
    - **Intelligent scoring**: ML-like algorithm ranks instances by suitability
    - **Multi-cloud comparison**: Compare all options in one place
    - **Cost optimization**: Find the best price/performance ratio
    - **Workload-aware**: Recommendations tailored to your workload type
    - **Traffic-aware**: Considers your traffic patterns
    - **Spot analysis**: Shows savings with spot/preemptible instances
    
    Returns:
        - Top N recommendations ranked by score
        - Detailed pricing (on-demand and spot)
        - Savings analysis
        - Key insights and tips
    """
    try:
        ai = CloudCostAI(db)
        
        result = await ai.get_recommendations(
            min_vcpus=request.min_vcpus,
            min_memory_gb=request.min_memory_gb,
            workload_type=request.workload_type,
            traffic_pattern=request.traffic_pattern,
            providers=request.providers,
            max_monthly_budget=request.max_monthly_budget,
            spot_eligible=request.spot_eligible,
            limit=request.limit
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "ai_powered": True,
            "version": "1.0"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/workload-types")
async def get_workload_types():
    """
    Get available workload types and their descriptions
    """
    return {
        "success": True,
        "workload_types": [
            {
                "id": "web_app",
                "name": "Web Application",
                "description": "Web apps, APIs, microservices",
                "icon": "🌐",
                "cpu_weight": "Medium",
                "memory_weight": "Low-Medium",
                "spot_eligible": True
            },
            {
                "id": "database",
                "name": "Database",
                "description": "Databases, data stores, caches",
                "icon": "🗄️",
                "cpu_weight": "Low-Medium",
                "memory_weight": "High",
                "spot_eligible": False
            },
            {
                "id": "compute_intensive",
                "name": "Compute Intensive",
                "description": "Batch processing, CI/CD, video encoding",
                "icon": "⚙️",
                "cpu_weight": "Very High",
                "memory_weight": "Low",
                "spot_eligible": True
            },
            {
                "id": "memory_intensive",
                "name": "Memory Intensive",
                "description": "Big data, analytics, in-memory processing",
                "icon": "💾",
                "cpu_weight": "Low",
                "memory_weight": "Very High",
                "spot_eligible": True
            },
            {
                "id": "ml_training",
                "name": "ML Training",
                "description": "Machine learning, AI workloads",
                "icon": "🤖",
                "cpu_weight": "High",
                "memory_weight": "Medium",
                "spot_eligible": True
            },
            {
                "id": "general",
                "name": "General Purpose",
                "description": "General workloads, mixed use",
                "icon": "⚡",
                "cpu_weight": "Medium",
                "memory_weight": "Medium",
                "spot_eligible": True
            }
        ]
    }


# ============================================================================
# CONVERSATIONAL AI ENDPOINTS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous messages in format [{role: 'user'|'assistant', content: 'message'}]"
    )


@router.post("/chat")
async def chat_with_ai(
    request: ChatMessage,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with CloudCost AI™ - Conversational interface
    
    **NEW!** ChatGPT-like conversational interface for cloud cost optimization.
    
    Ask questions in natural language like:
    - "I need instances for a daily data pipeline processing 3GB"
    - "Best setup for a web app with 1000 users?"
    - "What's the difference between AWS m5 and GCP n2?"
    
    The AI will:
    - Understand your requirements
    - Ask clarifying questions
    - Recommend specific instances with pricing
    - Provide optimization tips
    - Access real pricing data from our database
    
    Returns:
        - AI response message
        - Usage statistics (tokens)
        - Model information
    """
    try:
        ai = ConversationalAI(db)
        
        result = await ai.chat(
            message=request.message,
            conversation_history=request.conversation_history,
            stream=False
        )
        
        # Return 200 with success/error in body so the UI can show GROQ/API messages
        # without mapping HTTP 500 to a generic "detail" string (e.g. "Not Found" from Groq).
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/suggestions")
async def get_chat_suggestions(workload_type: str = "general"):
    """
    Get quick suggestion prompts for the chat interface
    
    These are example prompts users can click to start a conversation.
    
    Args:
        workload_type: Type of workload (data_pipeline, web_app, database, ml_training, general)
    
    Returns:
        List of suggestion prompts
    """
    try:
        # Create AI instance without DB (not needed for suggestions)
        ai = ConversationalAI(db=None)
        suggestions = await ai.get_quick_suggestions(workload_type)
        
        return {
            "success": True,
            "workload_type": workload_type,
            "suggestions": suggestions
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": [
                "What's the best instance for my workload?",
                "How can I reduce my cloud costs?",
                "Compare AWS, GCP, and Azure pricing"
            ]
        }

