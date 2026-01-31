"""
Conversational AI Service for CloudCost Optimizer
Powered by Groq (FREE & SUPER FAST - 500 tokens/sec)
"""

import os
import json
import logging
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime

from groq import AsyncGroq
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cloud_provider import CloudInstance
from src.models.pricing import CloudPricing

logger = logging.getLogger(__name__)


class ConversationalAI:
    """
    Conversational AI for cloud cost optimization
    Uses Groq API with Llama 3.1 70B for intelligent recommendations
    """
    
    # System prompt that gives AI knowledge about cloud instances
    SYSTEM_PROMPT = """You are CloudCost AI™, an expert cloud cost optimization assistant.

Your role:
- Help users find the best cloud instances (AWS, GCP, Azure) for their workloads
- Provide cost-effective recommendations
- Explain technical concepts in simple terms
- Be conversational, friendly, and helpful

Your knowledge:
- AWS EC2 instances (t3, m5, c5, r5, etc.)
- GCP Compute Engine (n2, e2, c2, etc.)  
- Azure VMs (D-series, E-series, F-series, etc.)
- Instance types: General purpose, compute optimized, memory optimized, GPU instances
- Pricing models: On-demand, Spot/Preemptible, Reserved/Committed
- Workload patterns: Batch processing, real-time, scheduled, continuous

Guidelines:
1. ALWAYS ask clarifying questions if the user's requirements are unclear
2. Recommend specific instance types with reasoning
3. Mention pricing (approximate hourly/monthly costs)
4. Suggest spot instances for fault-tolerant workloads (70-90% savings)
5. Consider workload patterns (daily, weekly, continuous)
6. Mention managed services when appropriate (RDS, Cloud SQL, etc.)
7. Keep responses concise but informative
8. Use emojis sparingly for emphasis (💰 for cost, ⚡ for performance, 💡 for tips)

Example response format:
"For your [workload description], I recommend:

**Best Options:**
- AWS: [instance-type] ([specs]) - $X/hour
- GCP: [instance-type] ([specs]) - $Y/hour  
- Azure: [instance-type] ([specs]) - $Z/hour

**Why?** [Brief reasoning]

💡 **Pro tip:** [Additional optimization advice]

**Questions:**
- [Clarifying question if needed]"

Remember: You're helping users SAVE MONEY while maintaining performance. Be their trusted advisor!
"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = os.getenv("GROQ_API_KEY", "")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Conversational AI will not work.")
            self.client = None
        else:
            self.client = AsyncGroq(api_key=self.api_key)
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False
    ) -> Dict:
        """
        Send a message to the AI and get a response
        
        Args:
            message: User's message
            conversation_history: Previous messages in the conversation
            stream: Whether to stream the response
            
        Returns:
            Dict with AI response or stream
        """
        if not self.client:
            return {
                "error": "AI service not configured. Please set GROQ_API_KEY environment variable.",
                "message": "Get your free API key from: https://console.groq.com/keys"
            }
        
        try:
            # Build conversation history
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            
            # Add previous messages
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Check if user is asking for specific recommendations
            # If so, fetch real data from database
            context = await self._get_context_from_db(message)
            if context:
                # Add context to the last user message
                messages[-1]["content"] = f"{message}\n\n[Context from database: {context}]"
            
            logger.info(f"Sending message to Groq AI: {message[:100]}...")
            
            if stream:
                # Streaming response (for real-time typing effect)
                return await self._stream_response(messages)
            else:
                # Regular response
                response = await self.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",  # 70B model - very smart!
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=0.9,
                )
                
                ai_message = response.choices[0].message.content
                
                return {
                    "success": True,
                    "message": ai_message,
                    "model": "llama-3.1-70b-versatile",
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in conversational AI: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an error. Please try again."
            }
    
    async def _stream_response(self, messages: List[Dict]) -> AsyncGenerator:
        """Stream the AI response word by word"""
        try:
            stream = await self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"\n\nError: {str(e)}"
    
    async def _get_context_from_db(self, message: str) -> Optional[str]:
        """
        Extract context from database based on user's message
        This helps AI give accurate recommendations with real pricing data
        """
        message_lower = message.lower()
        context_parts = []
        
        try:
            # Check if user is asking about specific instance types
            instance_keywords = ["m5", "t3", "c5", "r5", "n2", "e2", "d-series", "f-series"]
            mentioned_instances = [kw for kw in instance_keywords if kw in message_lower]
            
            if mentioned_instances:
                # Fetch pricing for mentioned instances
                for instance_prefix in mentioned_instances[:3]:  # Limit to 3
                    query = select(CloudInstance, CloudPricing).join(
                        CloudPricing,
                        and_(
                            CloudPricing.provider == CloudInstance.provider,
                            CloudPricing.instance_type == CloudInstance.instance_type,
                            CloudPricing.pricing_type == "on_demand"
                        )
                    ).where(
                        CloudInstance.instance_type.ilike(f"{instance_prefix}%")
                    ).limit(5)
                    
                    result = await self.db.execute(query)
                    rows = result.all()
                    
                    if rows:
                        for instance, pricing in rows[:2]:  # Top 2
                            context_parts.append(
                                f"{instance.provider.upper()} {instance.instance_type}: "
                                f"{instance.vcpus}vCPU, {instance.memory_gb}GB RAM, "
                                f"${float(pricing.hourly_price):.4f}/hour"
                            )
            
            # Check if user mentions workload patterns
            if any(word in message_lower for word in ["batch", "pipeline", "daily", "scheduled"]):
                context_parts.append(
                    "Note: For batch/scheduled workloads, Spot instances can save 70-90% "
                    "(e.g., AWS Spot, GCP Preemptible, Azure Spot)"
                )
            
            # Check if user mentions database
            if any(word in message_lower for word in ["database", "db", "mysql", "postgres", "sql"]):
                context_parts.append(
                    "Note: Memory-optimized instances recommended for databases. "
                    "Consider managed services (RDS, Cloud SQL, Azure Database) for production."
                )
            
            # Check if asking for comparison
            if any(word in message_lower for word in ["compare", "vs", "versus", "difference"]):
                # Fetch sample instances for comparison
                query = select(CloudInstance, CloudPricing).join(
                    CloudPricing,
                    and_(
                        CloudPricing.provider == CloudInstance.provider,
                        CloudPricing.instance_type == CloudInstance.instance_type,
                        CloudPricing.pricing_type == "on_demand"
                    )
                ).where(
                    and_(
                        CloudInstance.vcpus >= 4,
                        CloudInstance.vcpus <= 8,
                        CloudInstance.memory_gb >= 16,
                        CloudInstance.memory_gb <= 32
                    )
                ).limit(9)  # 3 per cloud
                
                result = await self.db.execute(query)
                rows = result.all()
                
                if rows:
                    by_provider = {}
                    for instance, pricing in rows:
                        if instance.provider not in by_provider:
                            by_provider[instance.provider] = []
                        by_provider[instance.provider].append((instance, pricing))
                    
                    for provider, instances in list(by_provider.items())[:3]:
                        if instances:
                            inst, price = instances[0]
                            context_parts.append(
                                f"{provider.upper()} example: {inst.instance_type} "
                                f"({inst.vcpus}vCPU, {inst.memory_gb}GB) = "
                                f"${float(price.hourly_price):.4f}/hr"
                            )
            
            if context_parts:
                return " | ".join(context_parts[:5])  # Max 5 context items
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting context from DB: {e}")
            return None
    
    async def get_quick_suggestions(self, workload_type: str) -> List[str]:
        """
        Get quick suggestion prompts for users to click
        """
        suggestions = {
            "data_pipeline": [
                "I need instances for a daily data pipeline processing 3GB",
                "Best setup for batch processing that runs every 6 hours",
                "Cost-effective option for ETL jobs running once a day"
            ],
            "web_app": [
                "Best instances for a web app with 1000 concurrent users",
                "What's the cheapest option for a small API server?",
                "I need to run a Node.js app with moderate traffic"
            ],
            "database": [
                "Best instance for PostgreSQL with 100GB data",
                "What's good for a MySQL database with 50 concurrent connections?",
                "Memory-optimized instances for Redis cache"
            ],
            "ml_training": [
                "Instances for training a machine learning model",
                "Best GPU instances for deep learning",
                "Cost-effective option for model training"
            ],
            "general": [
                "What's the difference between AWS, GCP, and Azure pricing?",
                "How much can I save with spot instances?",
                "Best instances for a startup on a budget"
            ]
        }
        
        return suggestions.get(workload_type, suggestions["general"])
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (1 token ≈ 4 chars)"""
        return len(text) // 4
