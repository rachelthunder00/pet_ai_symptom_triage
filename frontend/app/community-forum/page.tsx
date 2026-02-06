"use client";

import { MessageSquare, Heart, Share2, Zap, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import BottomNav from "@/components/BottomNav";
import ChatbotModal from "@/components/chatbot/ChatbotModal";


interface Post {
  id: string;
  title: string;
  description: string;
  author: string;
  avatar: string;
  replies: number;
  likes: number;
  category: "care" | "health" | "behavior" | "training";
  timestamp: string;
}

export default function CommunityForum() {
  const router = useRouter();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [chatbotOpen, setChatbotOpen] = useState(false);

  const posts: Post[] = [
    {
      id: "1",
      title: "My Golden Retriever Won't Stop Shedding - Help!",
      description: "My 2-year-old golden retriever sheds excessively. I've tried different grooming techniques and dietary changes, but nothing seems to help. Has anyone dealt with similar issues? Any recommendations?",
      author: "Sarah Mitchell",
      avatar: "🐕",
      replies: 24,
      likes: 156,
      category: "care",
      timestamp: "2 hours ago",
    },
    {
      id: "2",
      title: "New to Cat Ownership - First Time Tips",
      description: "Just adopted my first cat yesterday! I'm overwhelmed with questions about litter training, feeding schedules, and general care. What were your biggest challenges when you first got a cat?",
      author: "James Chen",
      avatar: "🐱",
      replies: 47,
      likes: 298,
      category: "training",
      timestamp: "5 hours ago",
    },
    {
      id: "3",
      title: "Best Budget-Friendly Pet Insurance Options",
      description: "Looking for affordable pet insurance that actually covers what you need. Would love to hear about your experiences with different providers and whether they're worth the investment.",
      author: "Emma Rodriguez",
      avatar: "💚",
      replies: 35,
      likes: 189,
      category: "health",
      timestamp: "1 day ago",
    },
    {
      id: "4",
      title: "Success Story: Training Our Stubborn Pup",
      description: "After 6 months of consistent training and patience, our rescue dog finally mastered basic commands! Sharing our journey and the techniques that worked best for us. Would love to inspire others!",
      author: "David Turner",
      avatar: "⭐",
      replies: 62,
      likes: 412,
      category: "behavior",
      timestamp: "3 days ago",
    },
  ];

  const categories = [
    { id: "care", label: "Care & Nutrition", icon: "🍗" },
    { id: "health", label: "Health & Wellness", icon: "🏥" },
    { id: "behavior", label: "Behavior", icon: "🐾" },
    { id: "training", label: "Training", icon: "🎯" },
  ];

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "care":
        return "bg-green-100 text-green-700 border-green-300";
      case "health":
        return "bg-red-100 text-red-700 border-red-300";
      case "behavior":
        return "bg-purple-100 text-purple-700 border-purple-300";
      case "training":
        return "bg-blue-100 text-blue-700 border-blue-300";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  const getCategoryLabel = (category: string) => {
    const cat = categories.find((c) => c.id === category);
    return cat?.label || category;
  };

  const filteredPosts = selectedCategory
    ? posts.filter((post) => post.category === selectedCategory)
    : posts;

  return (
    <main className="min-h-screen pb-24" style={{ backgroundColor: '#f2dcdd' }}>
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 pt-6 pb-8 shadow-lg">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push("/")}
              className="p-2 hover:bg-blue-700 rounded-full transition-colors"
              title="Go back to home"
            >
              <ArrowLeft size={24} />
            </button>
            <h1 className="text-3xl font-bold" style={{ fontFamily: "var(--font-poppins)" }}>
              Fuzzy Community
            </h1>
          </div>
          <p className="text-blue-100 text-sm ml-12">Learn from other pet owners and share your experiences</p>

          {/* CTA Button */}
          <button className="mt-4 w-full bg-white text-blue-600 font-bold py-3 px-4 rounded-2xl hover:bg-gray-50 transition-all active:scale-95 shadow-md flex items-center justify-center gap-2">
            <MessageSquare size={20} />
            Start a New Discussion
          </button>
        </div>
      </header>

      {/* Category Filter */}
      <div className="px-4 py-6 max-w-2xl mx-auto">
        <p className="text-sm font-semibold text-gray-700 mb-3" style={{ fontFamily: "var(--font-poppins)" }}>
          Filter by Category
        </p>
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`flex-shrink-0 px-4 py-2 rounded-full font-semibold text-sm transition-all whitespace-nowrap ${selectedCategory === null
              ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md"
              : "bg-white text-gray-700 border border-gray-200 hover:border-blue-300"
              }`}
            style={{ fontFamily: "var(--font-poppins)" }}
          >
            All Posts
          </button>
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`flex-shrink-0 px-4 py-2 rounded-full font-semibold text-sm transition-all whitespace-nowrap flex items-center gap-1 ${selectedCategory === category.id
                ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md"
                : "bg-white text-gray-700 border border-gray-200 hover:border-blue-300"
                }`}
              style={{ fontFamily: "var(--font-poppins)" }}
            >
              {category.icon} {category.label}
            </button>
          ))}
        </div>
      </div>

      {/* Discussion Posts */}
      <div className="px-4 max-w-2xl mx-auto space-y-4">
        {filteredPosts.length > 0 ? (
          filteredPosts.map((post) => (
            <div
              key={post.id}
              className="bg-white rounded-3xl p-5 shadow-md hover:shadow-lg transition-all cursor-pointer border border-gray-100 hover:border-blue-200"
            >
              {/* Post Header */}
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-start gap-3 flex-1">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-lg flex-shrink-0">
                    {post.avatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm" style={{ fontFamily: "var(--font-poppins)" }}>
                      {post.author}
                    </p>
                    <p className="text-xs text-gray-500">{post.timestamp}</p>
                  </div>
                </div>
                <span className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-bold border ${getCategoryColor(post.category)}`}>
                  {getCategoryLabel(post.category)}
                </span>
                <span className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-bold border ${getCategoryColor(post.category)}`}>
                  {getCategoryLabel(post.category)}
                </span>
              </div>

              {/* Post Title */}
              <h3 className="font-bold text-gray-900 mb-2 leading-snug" style={{ fontFamily: "var(--font-poppins)" }}>
                {post.title}
              </h3>

              {/* Post Description */}
              <p className="text-gray-600 text-sm leading-relaxed mb-4" style={{ fontFamily: "var(--font-poppins)" }}>
                {post.description}
              </p>

              {/* Post Footer - Stats & Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="flex gap-4 text-xs">
                  <button className="flex items-center gap-1 text-gray-600 hover:text-blue-600 transition-colors font-semibold">
                    <MessageSquare size={16} />
                    {post.replies} Replies
                  </button>
                  <button className="flex items-center gap-1 text-gray-600 hover:text-blue-600 transition-colors font-semibold">
                    <Heart size={16} />
                    {post.likes} Likes
                  </button>
                </div>
                <button className="text-gray-400 hover:text-blue-600 transition-colors">
                  <Share2 size={18} />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 font-semibold" style={{ fontFamily: "var(--font-poppins)" }}>
              No discussions in this category yet
            </p>
          </div>
        )}
      </div>

      {/* Engagement Section */}
      <div className="px-4 max-w-2xl mx-auto mt-8 mb-4">
        <div className="bg-gradient-to-br from-blue-100 to-blue-50 border-2 border-blue-200 rounded-3xl p-6">
          <div className="flex items-start gap-3">
            <Zap className="text-blue-600 flex-shrink-0 mt-1" size={24} />
            <div>
              <h4 className="font-bold text-gray-900 mb-2" style={{ fontFamily: "var(--font-poppins)" }}>
                💡 Community Tips
              </h4>
              <p className="text-sm text-gray-700 leading-relaxed" style={{ fontFamily: "var(--font-poppins)" }}>
                Be respectful, share your experiences honestly, and remember that every pet is unique. If you notice signs of serious illness, always consult a veterinarian!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNav onChatClick={() => setChatbotOpen(true)} />

      {/* Chatbot Modal */}
      <ChatbotModal open={chatbotOpen} onClose={() => setChatbotOpen(false)} />

    </main>
  );
}

