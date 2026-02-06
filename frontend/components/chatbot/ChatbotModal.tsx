"use client";
import { useState, useRef, useEffect } from "react";
import { Paperclip, AlertTriangle, Clock, CheckCircle, Camera, X } from "lucide-react";
import { useCameraCapture } from "./useCameraCapture";

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Get risk level styling
const getRiskStyle = (riskLevel: string) => {
  switch (riskLevel) {
    case 'ER':
      return { label: '🚨 EMERGENCY' };
    case 'TODAY':
      return { label: '⚠️ See Vet Today' };
    case 'SOON':
      return { label: '📅 Schedule Soon' };
    case 'MONITOR':
      return { label: '✅ Monitor at Home' };
    default:
      return { label: riskLevel };
  }
};

interface ChatbotModalProps {
  open: boolean;
  onClose: () => void;
  ownerName?: string;
  petName?: string;
}

type ChatMode = 'select' | 'category' | 'symptom' | 'general';

// Symptom categories with icons
const SYMPTOM_CATEGORIES = [
  { id: 'Toxic Ingestion & Poisoning', label: 'Poisoning / Toxic', icon: '☠️' },
  { id: 'Stomach Upset', label: 'Stomach Issues', icon: '🤢' },
  { id: 'Itching & Skin Issues', label: 'Skin & Itching', icon: '🔴' },
  { id: 'Injury & Bleeding', label: 'Injury / Bleeding', icon: '🩹' },
  { id: 'Concerning Behaviour Changes', label: 'Behavior Changes', icon: '😰' },
  { id: 'Ears, Eyes, and Mouth', label: 'Eyes / Ears / Mouth', icon: '👁️' },
  { id: 'Breathing Issues', label: 'Breathing Problems', icon: '😮‍💨' },
  { id: 'Urinary & Genital', label: 'Urinary Issues', icon: '💧' },
  { id: 'Something Else', label: 'Other Symptoms', icon: '❓' },
];

// Suggested prompts for symptom checker
const SYMPTOM_SUGGESTIONS = [
  "My pet is vomiting",
  "Not eating or drinking",
  "Limping or in pain",
  "Skin rash or itching",
  "Breathing problems",
];

// Suggested prompts for general questions
const GENERAL_SUGGESTIONS = [
  "Best food for my dog?",
  "How often should I groom?",
  "Vaccination schedule",
  "Exercise recommendations",
];

// Get urgency badge style based on risk level
const getUrgencyBadge = (riskLevel: string) => {
  switch (riskLevel) {
    case 'ER':
    case 'TODAY':
      return { label: 'High', className: 'bg-red-100 text-red-700' };
    case 'SOON':
      return { label: 'Medium', className: 'bg-yellow-100 text-yellow-700' };
    case 'MONITOR':
      return { label: 'Low', className: 'bg-green-100 text-green-700' };
    default:
      return null;
  }
};

export default function ChatbotModal({ open, onClose, ownerName, petName }: ChatbotModalProps) {
  type ChatMessage = { type: string; text: string; image?: string; riskLevel?: string };

  const [mode, setMode] = useState<ChatMode>('select');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [cameraOpen, setCameraOpen] = useState(false);

  const { videoRef, startCamera, stopCamera, capturePhoto } = useCameraCapture((dataUrl) => {
    setImages((prev) => [...prev, dataUrl]);
    setCameraOpen(false);
  });

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Reset when modal opens
  useEffect(() => {
    if (open) {
      setMode('select');
      setSelectedCategory('');
      setMessages([]);
      setInput("");
      setImages([]);
    }
  }, [open]);

  // Get pet context from localStorage
  const getPetContext = () => {
    if (typeof window === 'undefined') return {};
    const storedSpecies = localStorage.getItem('petSpecies');
    return {
      name: localStorage.getItem('petName') || undefined,
      species: storedSpecies ? storedSpecies.toLowerCase() : 'dog',
      breed: localStorage.getItem('petBreed') || undefined,
      age_years: localStorage.getItem('petAge') ? parseInt(localStorage.getItem('petAge')!) : undefined,
      weight: localStorage.getItem('petWeight') ? parseFloat(localStorage.getItem('petWeight')!) : undefined,
      weight_unit: localStorage.getItem('petWeightUnit') || 'kg',
    };
  };

  // Get location from localStorage
  const getLocation = () => {
    if (typeof window === 'undefined') return { latitude: undefined, longitude: undefined };
    const storedLoc = localStorage.getItem('userLocation');
    if (storedLoc) {
      try {
        const loc = JSON.parse(storedLoc);
        return { latitude: loc.lat, longitude: loc.lng };
      } catch { }
    }
    return { latitude: undefined, longitude: undefined };
  };

  const selectMode = (selectedMode: 'symptom' | 'general') => {
    if (selectedMode === 'symptom') {
      // Go to category selection first
      setMode('category');
    } else {
      setMode(selectedMode);
      setMessages([{
        type: "bot",
        text: `Hi${ownerName ? ` ${ownerName}` : ""}! What would you like to know about pet care? Ask me anything!`
      }]);
    }
  };

  const selectCategory = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setMode('symptom');
    const petDisplayName = petName && petName !== "your pet" ? petName : "your pet";
    const categoryLabel = SYMPTOM_CATEGORIES.find(c => c.id === categoryId)?.label || categoryId;
    setMessages([{
      type: "bot",
      text: `📋 **${categoryLabel}**\n\nDescribe ${petDisplayName}'s symptoms in detail, or upload a photo for assessment.`
    }]);
  };

  const handleSend = async (messageOverride?: string) => {
    const userMessage = messageOverride || input.trim();
    if (!userMessage && images.length === 0) return;

    const petContext = getPetContext();
    const { latitude, longitude } = getLocation();
    const currentImages = [...images];

    // Add user message to chat
    if (userMessage) {
      setMessages((msgs) => [...msgs, { type: "user", text: userMessage }]);
    }
    if (currentImages.length > 0) {
      currentImages.forEach(img => {
        setMessages((msgs) => [...msgs, { type: "user", text: "[Image]", image: img }]);
      });
    }

    setInput("");
    setImages([]);
    setIsLoading(true);

    try {
      let botResponse = "";
      let triageRiskLevel: string | undefined;

      // Prepare image data
      let imageBase64: string | undefined;
      let imageType: string | undefined;
      if (currentImages.length > 0) {
        const base64Match = currentImages[0].match(/^data:(image\/\w+);base64,(.+)$/);
        if (base64Match) {
          imageType = base64Match[1];
          imageBase64 = base64Match[2];
        }
      }

      if (mode === 'general') {
        // GENERAL QUESTION - use chat endpoint
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            session_id: `session_${Date.now()}`,
            pet_context: {
              name: petContext.name,
              species: petContext.species,
              breed: petContext.breed,
              age_years: petContext.age_years,
              weight: petContext.weight,
              weight_unit: petContext.weight_unit,
            },
            // Include conversation history
            history: messages.map(m => ({
              role: m.type === 'user' ? 'user' : 'assistant' as const,
              content: m.text
            })),
            // Include image if provided
            image_base64: imageBase64,
            image_type: imageType,
          }),
        });

        if (!response.ok) throw new Error(`API error: ${response.status}`);
        const data = await response.json();

        if (data.success && data.response) {
          botResponse = data.response;

          // Add source badges
          const toolsUsed = data.tools_used || [];
          const sourceLabels: string[] = [];
          if (toolsUsed.includes('vector_search')) sourceLabels.push('📚 Knowledge Base');
          if (toolsUsed.includes('web_search_tool')) sourceLabels.push('🌐 Web Search');
          if (toolsUsed.includes('analyze_image')) sourceLabels.push('📷 Image Analysis');
          if (sourceLabels.length > 0) {
            botResponse += `\n\n${sourceLabels.join(' • ')}`;
          }
        } else {
          botResponse = "I couldn't find an answer. Please try rephrasing your question.";
        }
      } else {
        // SYMPTOM CHECKER - use triage endpoint with selected category
        const response = await fetch(`${API_BASE_URL}/api/triage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            species: petContext.species,
            category: selectedCategory || "Something Else",
            user_description: userMessage || "See attached image",
            structured_fields: {},
            image_base64: imageBase64,
            image_type: imageType,
            latitude,
            longitude,
            pet_profile: {
              name: petContext.name,
              species: petContext.species,
              breed: petContext.breed,
              age: petContext.age_years?.toString(),
              weight: petContext.weight?.toString(),
            },
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error('Triage error:', errorData);
          throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.data) {
          const result = data.data;
          const riskStyle = getRiskStyle(result.risk_level);
          triageRiskLevel = result.risk_level;

          botResponse = `**${riskStyle.label}**\n\n`;

          if (result.category) {
            botResponse += `**📋 Category:** ${result.category}\n\n`;
          }

          if (result.reasoning_summary && result.reasoning_summary.length > 0) {
            botResponse += `**💡 Why:**\n${result.reasoning_summary.map((r: string) => `• ${r}`).join('\n')}\n\n`;
          }

          if (result.red_flags && result.red_flags.length > 0) {
            botResponse += `**⚠️ Red Flags:**\n${result.red_flags.map((f: string) => `• ${f}`).join('\n')}\n\n`;
          }

          if (result.recommended_actions && result.recommended_actions.length > 0) {
            botResponse += `**What to do:**\n${result.recommended_actions.map((a: string) => `• ${a}`).join('\n')}\n\n`;
          }

          if (result.what_to_monitor && result.what_to_monitor.length > 0) {
            botResponse += `**Watch for:**\n${result.what_to_monitor.map((m: string) => `• ${m}`).join('\n')}\n\n`;
          }

          if (result.follow_up_questions && result.follow_up_questions.length > 0) {
            botResponse += `**❓ Please answer:**\n${result.follow_up_questions.map((q: string) => `• ${q}`).join('\n')}\n\n`;
          }

          if (result.nearby_vets && result.nearby_vets.length > 0) {
            botResponse += `**📍 Nearby Vets:**\n${result.nearby_vets.map((v: {
              name: string;
              distance_miles?: number;
              distance_km?: number;
              phone?: string;
              is_24_hour?: boolean;
              is_emergency_clinic?: boolean;
              opening_hours?: string;
            }) => {
              const distance = v.distance_miles ? `${v.distance_miles} mi` : `${v.distance_km} km`;
              const badge = v.is_24_hour ? '🟢 24hr' : (v.is_emergency_clinic ? '🔴 ER' : '');
              const hours = v.opening_hours || '';
              return `• ${badge ? badge + ' ' : ''}${v.name} (${distance}) ${v.phone || ''}\n  ${hours}`;
            }).join('\n')}\n\n`;
          }

          botResponse += `\n⚕️ ${result.disclaimer || 'This is not a veterinary diagnosis. If symptoms worsen, seek care.'}`;

          // Show sources
          const sourceLabels: string[] = [];
          const ragCount = result.rag_source_count || 0;
          if (ragCount > 0) sourceLabels.push(`📚 ${ragCount} sources`);
          if (result.used_web_search) sourceLabels.push('🌐 Web Search');
          if (imageBase64) sourceLabels.push('📷 Image Analyzed');
          if (sourceLabels.length > 0) {
            botResponse += `\n\n${sourceLabels.join(' • ')}`;
          }
        } else {
          botResponse = "I couldn't analyze that. Please try again with more details.";
        }
      }

      setMessages((msgs) => [...msgs, { type: "bot", text: botResponse, riskLevel: triageRiskLevel }]);

    } catch (error) {
      console.error('API error:', error);
      setMessages((msgs) => [...msgs, {
        type: "bot",
        text: "Sorry, I couldn't connect to the AI service. Please make sure the backend is running."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const readers: Promise<string>[] = [];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        readers.push(new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        }));
      }
      Promise.all(readers).then((results) => {
        setImages((prev) => [...prev, ...results]);
      });
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSend(suggestion);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 relative flex flex-col" style={{ height: '85vh', maxHeight: '700px' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h2 className="text-lg font-bold text-gray-900">🐾 Fuzzy Friend</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl">×</button>
        </div>

        {/* Mode Selection */}
        {mode === 'select' && (
          <div className="flex-1 flex flex-col items-center justify-center p-6 gap-6">
            <p className="text-gray-600 text-center">
              Hi{ownerName ? ` ${ownerName}` : ""}! How can I help {petName && petName !== "your pet" ? petName : "your pet"} today?
            </p>

            <button
              onClick={() => selectMode('symptom')}
              className="w-full bg-red-50 hover:bg-red-100 border-2 border-red-200 rounded-xl p-6 text-left transition"
            >
              <div className="font-bold text-red-700 text-lg mt-2">🩺 Symptom Checker</div>
              <div className="text-red-600 text-sm mt-2 mb-2">Please describe symptoms or upload a photo for assessment. Open a new checker for a new symptom.</div>
            </button>

            <button
              onClick={() => selectMode('general')}
              className="w-full hover:bg-gray-50 rounded-xl p-4 text-left transition"
            >
              <div className="font-medium text-blue-700 text-sm mt-2">💬 General Question</div>
              <div className="text-blue-600 text-xs mt-1">Pet care, nutrition, behavior tips</div>
            </button>
          </div>
        )}

        {/* Category Selection */}
        {mode === 'category' && (
          <div className="flex-1 flex flex-col p-4 overflow-y-auto">
            <div className="mb-4">
              <button
                onClick={() => setMode('select')}
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                ← Back
              </button>
            </div>
            <h3 className="text-lg font-bold text-gray-800 mb-2">What's the issue?</h3>
            <p className="text-sm text-gray-500 mb-4">Select the category that best describes {petName && petName !== "your pet" ? petName : "your pet"}'s symptoms</p>

            <div className="grid grid-cols-2 gap-3">
              {SYMPTOM_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => selectCategory(cat.id)}
                  className="flex flex-col items-center justify-center p-4 bg-gray-50 hover:bg-blue-50 hover:border-blue-300 border-2 border-gray-200 rounded-xl transition text-center"
                >
                  <span className="text-2xl mb-2">{cat.icon}</span>
                  <span className="text-sm font-medium text-gray-700">{cat.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Interface */}
        {(mode === 'symptom' || mode === 'general') && (
          <>
            {/* Mode indicator */}
            <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">
                {mode === 'symptom'
                  ? `🩺 ${SYMPTOM_CATEGORIES.find(c => c.id === selectedCategory)?.label || 'Symptom Checker'}`
                  : '💬 General Question'}
              </span>
              <button
                onClick={() => setMode('select')}
                className="text-xs text-blue-600 hover:underline"
              >
                Switch mode
              </button>
            </div>

            {/* Messages */}
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-3" style={{ minHeight: 0 }}>
              {messages.map((msg, i) => {
                const urgencyBadge = msg.riskLevel ? getUrgencyBadge(msg.riskLevel) : null;
                return (
                  <div key={i} className={msg.type === "user" ? "text-right" : "text-left"}>
                    {msg.image && (
                      <img src={msg.image} alt="Upload" className="inline-block h-24 w-24 object-cover rounded-xl border-2 border-blue-200 mb-1" />
                    )}
                    <span className={
                      msg.type === "user"
                        ? "inline-block bg-blue-500 text-white rounded-2xl px-4 py-2 max-w-[85%] break-words"
                        : "inline-block bg-gray-100 text-gray-800 rounded-2xl px-4 py-2 text-left max-w-[90%] whitespace-pre-wrap text-sm break-words"
                    }>
                      {msg.text.split('**').map((part, idx) =>
                        idx % 2 === 1 ? <strong key={idx}>{part}</strong> : part
                      )}
                      {urgencyBadge && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <span className={`${urgencyBadge.className} text-xs font-bold px-3 py-1 rounded-full`}>
                            {urgencyBadge.label}
                          </span>
                        </div>
                      )}
                    </span>
                  </div>
                );
              })}

              {isLoading && (
                <div className="text-left">
                  <span className="inline-block bg-gray-100 text-gray-600 rounded-2xl px-4 py-2">
                    <span className="flex items-center gap-2">
                      <span className="animate-spin">⏳</span>
                      Analyzing...
                    </span>
                  </span>
                </div>
              )}
            </div>

            {/* Suggestions - only show if no messages yet (besides greeting) */}
            {messages.length === 1 && !isLoading && (
              <div className="px-4 pb-2">
                <div className="text-xs text-gray-500 mb-2">Quick suggestions:</div>
                <div className="flex flex-wrap gap-2">
                  {(mode === 'symptom' ? SYMPTOM_SUGGESTIONS : GENERAL_SUGGESTIONS).map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(s)}
                      className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-full px-3 py-1.5 transition"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Image preview */}
            {images.length > 0 && (
              <div className="px-4 pb-2 flex gap-2">
                {images.map((img, idx) => (
                  <div key={idx} className="relative">
                    <img src={img} alt="Preview" className="h-16 w-16 object-cover rounded-lg border" />
                    <button
                      onClick={() => setImages(images.filter((_, i) => i !== idx))}
                      className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Camera view */}
            {cameraOpen && (
              <div className="px-4 pb-2">
                <div className="relative bg-black rounded-lg overflow-hidden">
                  <video ref={videoRef} autoPlay playsInline className="w-full h-48 object-cover" />
                  <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-2">
                    <button
                      onClick={capturePhoto}
                      className="bg-white text-gray-800 rounded-full px-4 py-2 text-sm font-medium"
                    >
                      📸 Capture
                    </button>
                    <button
                      onClick={() => { stopCamera(); setCameraOpen(false); }}
                      className="bg-gray-800 text-white rounded-full px-4 py-2 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Input area */}
            <div className="p-4 border-t bg-white">
              <div className="flex items-center gap-2">
                <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleImageUpload} />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition"
                  title="Upload image"
                >
                  <Paperclip size={20} />
                </button>
                <button
                  onClick={() => { setCameraOpen(true); startCamera(); }}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition"
                  title="Take photo"
                >
                  <Camera size={20} />
                </button>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder={mode === 'symptom' ? "Describe symptoms..." : "Ask a question..."}
                  className="flex-1 border rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  disabled={isLoading}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={isLoading || (!input.trim() && images.length === 0)}
                  className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full px-4 py-2 text-sm font-medium transition"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
