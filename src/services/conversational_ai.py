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

from src.models.cloud_provider import CloudInstance, CloudPricing

logger = logging.getLogger(__name__)


class ConversationalAI:
    """
    Conversational AI for cloud cost optimization
    Uses Groq API with Llama 3.1 70B for intelligent recommendations
    """
    
    # Expert system prompt with deep cloud knowledge
    SYSTEM_PROMPT = """You are CloudCost AI™, a senior cloud infrastructure architect with 10+ years of experience optimizing costs across AWS, GCP, and Azure.

🎯 YOUR EXPERTISE:
You deeply understand the relationship between workload characteristics and instance selection. You NEVER recommend:
- Compute-optimized (C-series) for memory-intensive workloads
- Memory-optimized (R-series) for CPU-bound tasks
- General-purpose for specialized workloads
- Burstable (T-series) for sustained high-load applications

📊 INSTANCE FAMILY MATCHING (CRITICAL):

**Compute-Optimized** (High vCPU, Low Memory ratio <2:1):
- AWS: c5, c6i, c6g, c7g, c8g
- GCP: c2, c2d, c3, h3
- Azure: F-series, Fsv2
- USE FOR: Video encoding, batch processing, web servers, CI/CD, high-performance computing
- DON'T USE FOR: Databases, caching, in-memory analytics

**Memory-Optimized** (Low vCPU, High Memory ratio >8:1):
- AWS: r5, r6i, r6g, r7g, x2, z1d
- GCP: m1, m2, m3, n2-highmem
- Azure: E-series, M-series, Mv2
- USE FOR: Databases (PostgreSQL, MySQL, Redis), in-memory analytics, SAP HANA, real-time big data
- DON'T USE FOR: Video encoding, batch processing, stateless web apps

**General-Purpose** (Balanced 4:1 to 8:1 ratio):
- AWS: m5, m6i, m6g, m7g, t3, t4g
- GCP: n1, n2, n2d, e2
- Azure: D-series, B-series
- USE FOR: Web apps with moderate traffic, small databases, dev/test, microservices
- DON'T USE FOR: Specialized high-CPU or high-memory workloads

**Storage-Optimized** (High IOPS, NVMe):
- AWS: i3, i4i, d3, d3en
- GCP: n2-standard with local SSD
- Azure: L-series
- USE FOR: NoSQL databases, data warehousing, Elasticsearch, Cassandra
- DON'T USE FOR: Workloads that don't need local storage

**GPU-Accelerated**:
- AWS: p3, p4, g4, g5
- GCP: a2, a3
- Azure: NC, ND, NV series
- USE FOR: ML training, inference, rendering, simulation
- DON'T USE FOR: General compute (massive waste of money!)

🧠 ANALYSIS PROCESS:
1. **Identify workload type** from user description
2. **Determine resource bottleneck**: CPU-bound, Memory-bound, I/O-bound, or Balanced
3. **Match to correct instance family** (NEVER recommend wrong family!)
4. **Consider usage pattern**: Continuous vs Intermittent vs Batch
5. **Recommend pricing model**: On-demand, Spot/Preemptible, or Reserved
6. **Provide 2-3 options** across different clouds with exact pricing
7. **Explain WHY** each recommendation fits

💰 PRICING STRATEGY:
- **Continuous workloads (24/7)**: Reserved/Committed Use Discounts (40-60% savings)
- **Batch/Scheduled (fault-tolerant)**: Spot/Preemptible (70-90% savings)
- **Variable/Unpredictable**: On-demand with auto-scaling
- **Dev/Test**: Spot instances + stop when not in use

🚫 RED FLAGS (Ask clarifying questions):
- User says "database" but doesn't specify type/size
- User says "web app" without mentioning traffic/concurrent users
- User mentions "ML" without specifying training vs inference
- Unclear if workload is fault-tolerant (for Spot recommendation)

✅ RESPONSE FORMAT:

"Based on your **[workload type]** requirements, here's my expert analysis:

**🎯 Workload Classification:**
- Type: [CPU-bound/Memory-bound/Balanced]
- Pattern: [Continuous/Batch/Variable]
- Fault-tolerance: [Yes/No]

**💎 Recommended Instances:**

1. **[Provider]** - `[instance-type]` ([vCPUs]vCPU, [memory]GB RAM)
   - Cost: $[X]/hour ($[Y]/month on-demand)
   - Why: [Specific reason matching workload]
   - Save with Spot: $[Z]/month (if applicable)

2. **[Provider]** - `[instance-type]` ([specs])
   - Cost: $[X]/hour
   - Why: [Reason]

**🎓 Expert Reasoning:**
[Explain WHY these specific families/types match the workload characteristics]

**💡 Cost Optimization Tips:**
- [Specific tip 1]
- [Specific tip 2]

**❓ Questions to refine:**
- [Clarifying question if needed]"

🔍 ALWAYS USE REAL DATA:
When I provide you with [Context from database: ...], use those EXACT prices and specs in your response. Don't make up numbers!

Remember: A bad recommendation costs users money. Be precise, be accurate, be expert-level!"""

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
                    model="llama-3.3-70b-versatile",  # Updated to latest model
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=0.9,
                )
                
                ai_message = response.choices[0].message.content
                
                return {
                    "success": True,
                    "message": ai_message,
                    "model": "llama-3.3-70b-versatile",
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
                model="llama-3.3-70b-versatile",
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
        Extract SMART context from database based on user's message
        This helps AI give EXPERT recommendations with real pricing data
        """
        message_lower = message.lower()
        context_parts = []
        
        try:
            # Detect workload type from message
            workload_signals = {
                "database": {"family_hint": "memory", "keywords": ["mysql", "postgres", "redis", "mongodb", "db", "database"]},
                "compute": {"family_hint": "compute", "keywords": ["encoding", "batch", "processing", "ci/cd", "compile", "render"]},
                "memory": {"family_hint": "memory", "keywords": ["cache", "in-memory", "analytics", "big data", "spark"]},
                "web": {"family_hint": "general", "keywords": ["web", "api", "microservice", "frontend", "backend", "server"]},
                "ml": {"family_hint": "gpu", "keywords": ["ml", "machine learning", "ai", "training", "inference", "model"]},
            }
            
            detected_workload = None
            for workload, config in workload_signals.items():
                if any(kw in message_lower for kw in config["keywords"]):
                    detected_workload = config["family_hint"]
                    context_parts.append(f"🎯 Detected workload: {workload.upper()}")
                    break
            
            # Extract resource requirements
            vcpu_pattern = r'(\d+)\s*(?:vcpu|cpu|core)'
            memory_pattern = r'(\d+)\s*(?:gb|gib|g)\s*(?:ram|memory)'
            
            import re
            vcpu_match = re.search(vcpu_pattern, message_lower)
            memory_match = re.search(memory_pattern, message_lower)
            
            min_vcpus = int(vcpu_match.group(1)) if vcpu_match else 2
            min_memory = float(memory_match.group(1)) if memory_match else 8
            
            # Calculate memory-to-vCPU ratio to determine instance family
            ratio = min_memory / min_vcpus if min_vcpus > 0 else 4
            
            if ratio < 2:
                family_type = "compute_optimized"
                family_note = "High CPU, Low Memory (ratio < 2:1)"
            elif ratio > 8:
                family_type = "memory_optimized"
                family_note = "Low CPU, High Memory (ratio > 8:1)"
            else:
                family_type = "general_purpose"
                family_note = "Balanced (ratio 4:1 to 8:1)"
            
            context_parts.append(f"📊 Resource ratio: {ratio:.1f}:1 → {family_note}")
            
            # Fetch appropriate instances based on detected family
            query = select(CloudInstance, CloudPricing).join(
                CloudPricing,
                and_(
                    CloudPricing.provider == CloudInstance.provider,
                    CloudPricing.instance_type == CloudInstance.instance_type,
                    CloudPricing.pricing_type == "on_demand"
                )
            ).where(
                and_(
                    CloudInstance.vcpus >= min_vcpus * 0.8,  # Allow some flexibility
                    CloudInstance.vcpus <= min_vcpus * 1.5,
                    CloudInstance.memory_gb >= min_memory * 0.8,
                    CloudInstance.memory_gb <= min_memory * 1.5,
                )
            ).limit(9)  # 3 per provider
            
            result = await self.db.execute(query)
            rows = result.all()
            
            if rows:
                # Group by provider
                by_provider = {"aws": [], "gcp": [], "azure": []}
                for instance, pricing in rows:
                    if instance.provider in by_provider:
                        by_provider[instance.provider].append((instance, pricing))
                
                # Get best match from each provider
                for provider in ["aws", "gcp", "azure"]:
                    if by_provider[provider]:
                        # Sort by price
                        sorted_instances = sorted(by_provider[provider], key=lambda x: float(x[1].hourly_price))
                        inst, price = sorted_instances[0]  # Cheapest
                        
                        monthly = float(price.hourly_price) * 730
                        ratio_str = f"{inst.memory_gb / inst.vcpus:.1f}:1"
                        
                        family_indicator = ""
                        if inst.memory_gb / inst.vcpus < 2:
                            family_indicator = "⚡COMPUTE-OPT"
                        elif inst.memory_gb / inst.vcpus > 8:
                            family_indicator = "💾MEMORY-OPT"
                        else:
                            family_indicator = "⚖️BALANCED"
                        
                        context_parts.append(
                            f"{provider.upper()}: {inst.instance_type} "
                            f"({inst.vcpus}vCPU, {inst.memory_gb}GB, ratio {ratio_str}) "
                            f"= ${float(price.hourly_price):.4f}/hr (${monthly:.0f}/mo) "
                            f"[{family_indicator}]"
                        )
            
            # Check for spot/batch keywords
            if any(word in message_lower for word in ["batch", "scheduled", "daily", "nightly", "fault-tolerant", "interruptible"]):
                context_parts.append("💡 SPOT ELIGIBLE: Workload seems fault-tolerant → Consider Spot/Preemptible for 70-90% savings")
            
            # Check for database-specific advice
            if any(word in message_lower for word in ["database", "db", "mysql", "postgres"]):
                context_parts.append("🗄️ DATABASE DETECTED: Use MEMORY-OPTIMIZED (R-series/highmem/E-series), NOT compute-optimized!")
            
            # Check for ML workload
            if any(word in message_lower for word in ["ml", "machine learning", "training", "ai", "neural"]):
                context_parts.append("🤖 ML WORKLOAD: Consider GPU instances (P/A/NC series) for training, CPU for inference")
            
            # Return context if we found anything useful
            if len(context_parts) >= 2:  # At least 2 pieces of info
                return " | ".join(context_parts[:8])  # Max 8 items
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting expert context from DB: {e}")
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
