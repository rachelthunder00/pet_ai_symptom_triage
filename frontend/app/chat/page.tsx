"use client";

import { Send, Upload, Home, User, MessageCircle, Users, Settings, X, ArrowLeft, Sparkles, BookOpen } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { sendChatMessage, imageToBase64 } from "@/lib/api";

interface Message {
  id: string;
  type: "user" | "ai";
  content: string;
  toolsUsed?: string[];
  timestamp: Date;
}

export default function ChatPage() {
  const [activeTab, setActiveTab] = useState("chat");
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "ai",
      content: "Hello! 👋 I'm your Pet Health AI Assistant. I can answer questions about pet health, nutrition, behavior, and more.\n\nI have access to a knowledge base of 18,000+ pet health records and can search the web for the latest information.\n\n**Ask me anything!** For example:\n• What are signs of diabetes in dogs?\n• Is chocolate toxic to cats?\n• How often should I groom my golden retriever?",
      toolsUsed: [],
      timestamp: new Date(Date.now() - 5 * 60000),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const tabs = [
    { id: "home", icon: Home, label: "Home", href: "/" },
    { id: "profile", icon: User, label: "Profile", href: "/profile" },
    { id: "chat", icon: MessageCircle, label: "Chat", href: "/chat" },
    { id: "forum", icon: Users, label: "Forum", href: "/community-forum" },
    { id: "settings", icon: Settings, label: "Settings", href: "/" },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await sendChatMessage({
        message: inputValue,
        session_id: sessionId,
      });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: response.response || "I apologize, I couldn't process that request.",
        toolsUsed: response.tools_used || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: "I'm sorry, I couldn't connect to the AI service. Please make sure the backend is running.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
    scrollToBottom();
  };

  const getToolBadge = (tool: string) => {
    switch (tool) {
      case "vector_search":
        return { label: "📚 Knowledge Base", color: "bg-purple-100 text-purple-700" };
      case "web_search_tool":
        return { label: "🌐 Web Search", color: "bg-blue-100 text-blue-700" };
      case "check_red_flags":
        return { label: "🚨 Safety Check", color: "bg-red-100 text-red-700" };
      case "find_nearby_vets":
        return { label: "📍 Vet Finder", color: "bg-green-100 text-green-700" };
      default:
        return { label: tool, color: "bg-gray-100 text-gray-700" };
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-50 pb-24 flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-4 pt-6 pb-4 shadow-lg">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push("/")}
              className="p-2 hover:bg-purple-700 rounded-full transition-colors"
            >
              <ArrowLeft size={24} />
            </button>
            <h1 className="text-2xl font-bold flex items-center gap-2" style={{ fontFamily: "var(--font-poppins)" }}>
              <Sparkles size={28} /> Pet Health Chat
            </h1>
          </div>
          <p className="text-purple-100 text-sm ml-12">Ask any pet health question - powered by RAG & AI</p>
        </div>
      </header>

      {/* Info Banner */}
      <div className="px-4 py-3 max-w-2xl mx-auto w-full">
        <div className="bg-white/80 backdrop-blur rounded-xl p-3 border border-purple-200 flex items-center gap-3">
          <BookOpen className="text-purple-500 flex-shrink-0" size={20} />
          <p className="text-xs text-gray-600">
            <strong>Knowledge-powered:</strong> I search 18,000+ pet health records and the web to answer your questions.
          </p>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 max-w-2xl mx-auto w-full space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-md ${
                message.type === "user"
                  ? "bg-purple-500 text-white rounded-br-none"
                  : "bg-white text-gray-800 rounded-bl-none border border-gray-200"
              }`}
            >
              <div
                className="text-sm font-medium leading-relaxed whitespace-pre-wrap"
                style={{ fontFamily: "var(--font-poppins)" }}
              >
                {message.content}
              </div>

              {/* Tools Used Badges */}
              {message.type === "ai" && message.toolsUsed && message.toolsUsed.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {message.toolsUsed.map((tool, idx) => {
                    const badge = getToolBadge(tool);
                    return (
                      <span
                        key={idx}
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.color}`}
                      >
                        {badge.label}
                      </span>
                    );
                  })}
                </div>
              )}

              <span className={`text-xs mt-2 block ${message.type === "user" ? "text-purple-100" : "text-gray-500"}`}>
                {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 px-4 py-3 rounded-2xl rounded-bl-none border border-gray-200 shadow-md">
              <div className="flex gap-2 items-center">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                <span className="text-sm text-gray-500 ml-2">Searching knowledge base...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4 shadow-xl max-w-2xl mx-auto w-full">
        <div className="flex gap-3 items-end">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSendMessage()}
            placeholder="Ask any pet health question..."
            disabled={isLoading}
            className="flex-1 bg-gray-100 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 placeholder-gray-500 disabled:opacity-50"
            style={{ fontFamily: "var(--font-poppins)" }}
          />

          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="flex-shrink-0 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white p-2 rounded-full transition-all active:scale-95"
          >
            <Send size={20} />
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-3" style={{ fontFamily: "var(--font-poppins)" }}>
          💡 Try: "What vaccines does my puppy need?" or "Why is my cat losing fur?"
        </p>
      </div>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-2xl">
        <div className="mx-auto max-w-2xl px-4 flex justify-around items-center">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  router.push(tab.href);
                }}
                className="flex-1 py-4 px-2 flex flex-col items-center gap-1 transition-all duration-200 group relative"
              >
                <Icon
                  size={28}
                  className={`transition-all duration-200 ${
                    isActive ? "text-purple-600 scale-125" : "text-gray-600 group-hover:text-purple-500"
                  }`}
                  strokeWidth={isActive ? 2.5 : 2}
                />
                <span
                  className={`text-xs font-bold transition-all ${
                    isActive ? "text-purple-600 opacity-100" : "text-gray-600 opacity-0 group-hover:opacity-75"
                  }`}
                >
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>
    </main>
  );
}
