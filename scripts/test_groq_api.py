#!/usr/bin/env python3
"""
Quick test script for Groq Conversational AI
Run this to test locally before deploying
"""

import asyncio
import os
import sys

# Set the API key from environment variable
# Get your FREE key at: https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    print("❌ Error: GROQ_API_KEY environment variable not set!")
    print("\n📝 To use this test:")
    print("   export GROQ_API_KEY='your_groq_api_key_here'")
    print("   python scripts/test_groq_api.py")
    print("\n🔑 Get your FREE key at: https://console.groq.com/keys")
    sys.exit(1)

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Mock database for testing
class MockDB:
    async def execute(self, query):
        class MockResult:
            def scalars(self):
                return self
            def all(self):
                return []
        return MockResult()

async def test_groq_api():
    """Test Groq API connection and response"""
    print("🧪 Testing Groq Conversational AI...")
    print("-" * 60)
    
    try:
        # Import after setting env var
        from src.services.conversational_ai import ConversationalAI
        
        # Create AI instance with mock DB
        ai = ConversationalAI(MockDB())
        
        if not ai.client:
            print("❌ GROQ_API_KEY not properly set!")
            sys.exit(1)
        
        print("✅ Groq client initialized successfully!")
        print("\n📤 Sending test message...")
        
        # Test message
        test_message = "I need instances for a daily data pipeline processing 3GB"
        print(f"Message: \"{test_message}\"")
        print("\n⏳ Waiting for AI response...\n")
        
        # Get response
        response = await ai.chat(
            message=test_message,
            conversation_history=None,
            stream=False
        )
        
        if response.get("success"):
            print("✅ SUCCESS! AI responded:")
            print("-" * 60)
            print(response["message"])
            print("-" * 60)
            print(f"\n📊 Usage:")
            print(f"   Prompt tokens: {response['usage']['prompt_tokens']}")
            print(f"   Completion tokens: {response['usage']['completion_tokens']}")
            print(f"   Total tokens: {response['usage']['total_tokens']}")
            print(f"   Model: {response['model']}")
            print("\n🎉 GROQ API IS WORKING PERFECTLY!")
            return True
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Install dependencies first:")
        print("   pip install groq httpx")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           CloudCost AI™ - Groq API Test                     ║
║                                                              ║
║  Testing: Conversational AI with Llama 3.1 70B              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    success = asyncio.run(test_groq_api())
    
    if success:
        print("\n" + "=" * 60)
        print("🚀 READY TO DEPLOY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Add GROQ_API_KEY to Render environment variables")
        print("2. Wait for auto-deployment (~5 minutes)")
        print("3. Test at: https://cloudcost-optimizer-5c3p.onrender.com/api/v1/ai/chat")
        print("4. Use the UI: https://kadaliaswinkumar.github.io/cloudcost-optimizer/ai")
    else:
        print("\n❌ Fix the issues above before deploying")
        sys.exit(1)
