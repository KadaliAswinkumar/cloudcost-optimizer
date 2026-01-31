import { useState, useEffect, useRef } from 'react'
import { 
  Sparkles, 
  Send,
  Mic,
  MicOff,
  Loader2,
  Bot,
  User,
  Lightbulb,
  Copy,
  Check
} from 'lucide-react'
import { api } from '../api/client'

export default function CloudCostAI() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [copied, setCopied] = useState(false)
  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Fetch suggestions on mount
  useEffect(() => {
    const fetchSuggestions = async () => {
      try {
        const response = await api.getChatSuggestions('general')
        setSuggestions(response.data.suggestions || [])
      } catch (err) {
        console.error('Failed to fetch suggestions:', err)
        setSuggestions([
          "What's the best instance for my workload?",
          "How can I reduce my cloud costs?",
          "Compare AWS, GCP, and Azure pricing"
        ])
      }
    }
    fetchSuggestions()

    // Add welcome message
    setMessages([{
      role: 'assistant',
      content: `👋 Hi! I'm **CloudCost AI™**, your personal cloud cost optimization expert.

I can help you:
- 💰 Find the most cost-effective cloud instances
- ⚡ Optimize your workload performance
- 📊 Compare AWS, GCP, and Azure pricing
- 💡 Suggest money-saving strategies

**Just describe your workload in plain English!** 

For example: "I need instances for a daily data pipeline processing 3GB"

What can I help you with today?`
    }])
  }, [])

  // Voice recognition setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setInputMessage(transcript)
        setIsListening(false)
      }

      recognitionRef.current.onerror = () => {
        setIsListening(false)
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
  }, [])

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Voice input not supported in your browser. Please use Chrome.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || inputMessage.trim()
    
    if (!textToSend) return

    // Add user message
    const userMessage = { role: 'user', content: textToSend }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      // Prepare conversation history (exclude welcome message)
      const conversationHistory = messages
        .filter(m => m.role !== 'system')
        .map(m => ({ role: m.role, content: m.content }))

      // Send to API
      const response = await api.chatWithAI({
        message: textToSend,
        conversation_history: conversationHistory
      })

      // Add AI response
      if (response.data.success) {
        const aiMessage = {
          role: 'assistant',
          content: response.data.message
        }
        setMessages(prev => [...prev, aiMessage])
      } else {
        throw new Error(response.data.error || 'Failed to get response')
      }
    } catch (err) {
      console.error('Chat error:', err)
      const errorMessage = {
        role: 'assistant',
        content: `😕 Sorry, I encountered an error: ${err.response?.data?.detail || err.message}

Please try again or rephrase your question.`
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const useSuggestion = (suggestion) => {
    setInputMessage(suggestion)
    // Auto-send after a brief delay
    setTimeout(() => sendMessage(suggestion), 300)
  }

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 mb-3">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Conversational AI</span>
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            CloudCost AI™ Chat
          </span>
        </h1>
        <p className="text-slate-300">
          Ask me anything about cloud instances and costs in plain English! 🎤
        </p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 glass-card flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div className={`
                flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                ${message.role === 'user' 
                  ? 'bg-gradient-to-br from-blue-500 to-purple-500' 
                  : 'bg-gradient-to-br from-purple-500 to-pink-500'
                }
              `}>
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={`
                flex-1 max-w-3xl
                ${message.role === 'user' ? 'text-right' : 'text-left'}
              `}>
                <div className={`
                  inline-block px-5 py-3 rounded-2xl text-sm leading-relaxed
                  ${message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-blue-500/30 text-white'
                    : 'bg-slate-800/50 border border-slate-700/50 text-slate-200'
                  }
                `}>
                  {/* Render markdown-like formatting */}
                  <div 
                    className="prose prose-invert prose-sm max-w-none"
                    dangerouslySetInnerHTML={{
                      __html: message.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 rounded bg-slate-900 text-blue-400 font-mono text-xs">$1</code>')
                        .replace(/\n\n/g, '<br/><br/>')
                        .replace(/\n-/g, '<br/>•')
                    }}
                  />
                </div>

                {/* Copy button for AI messages */}
                {message.role === 'assistant' && (
                  <button
                    onClick={() => copyMessage(message.content)}
                    className="mt-2 text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        Copy
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-slate-800/50 border border-slate-700/50">
                <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
                <span className="text-sm text-slate-400">AI is thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions (show only if no user messages yet) */}
        {messages.filter(m => m.role === 'user').length === 0 && suggestions.length > 0 && (
          <div className="px-6 pb-4 border-t border-slate-800/50">
            <div className="flex items-center gap-2 text-xs text-slate-400 mb-3 mt-4">
              <Lightbulb className="w-4 h-4" />
              <span>Try asking:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => useSuggestion(suggestion)}
                  className="px-3 py-2 text-xs rounded-lg bg-slate-800/50 border border-slate-700 text-slate-300 hover:border-purple-500/50 hover:text-white transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-6 border-t border-slate-800/50">
          <div className="flex gap-3">
            {/* Voice Input Button */}
            <button
              onClick={toggleVoiceInput}
              disabled={loading}
              className={`
                flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-all
                ${isListening
                  ? 'bg-red-500/20 border-2 border-red-500 text-red-400 animate-pulse'
                  : 'bg-slate-800 border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600'
                }
              `}
              title="Voice input (click to speak)"
            >
              {isListening ? (
                <MicOff className="w-5 h-5" />
              ) : (
                <Mic className="w-5 h-5" />
              )}
            </button>

            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isListening ? "🎤 Listening..." : "Ask me anything about cloud costs... (or click 🎤 to speak)"}
                disabled={loading || isListening}
                className="w-full h-12 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 resize-none"
                rows="1"
              />
            </div>

            {/* Send Button */}
            <button
              onClick={() => sendMessage()}
              disabled={loading || !inputMessage.trim() || isListening}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all shadow-lg shadow-purple-500/25"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              ) : (
                <Send className="w-5 h-5 text-white" />
              )}
            </button>
          </div>

          {/* Tips */}
          <div className="mt-3 text-xs text-slate-500 text-center">
            💡 Pro tip: Be specific about your workload for better recommendations
          </div>
        </div>
      </div>
    </div>
  )
}
