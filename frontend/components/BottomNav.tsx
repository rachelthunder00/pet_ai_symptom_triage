"use client";

import { Home, User, MessageCircle, Users, Settings } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

interface BottomNavProps {
  onChatClick?: () => void;
}

const tabs = [
  { id: "home", icon: Home, label: "Home", href: "/" },
  { id: "profile", icon: User, label: "Profile", href: "/profile" },
  { id: "chat", icon: MessageCircle, label: "Chat", href: undefined }, // href undefined for chat
  { id: "forum", icon: Users, label: "Forum", href: "/community-forum" },
  { id: "settings", icon: Settings, label: "Settings", href: "/settings" },
];


export default function BottomNav({ onChatClick }: BottomNavProps) {
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-2xl z-30">
      <style>{`
        @keyframes pop {
          0% { transform: scale(1) rotate(0deg); }
          50% { transform: scale(1.4) rotate(-10deg); }
          100% { transform: scale(1) rotate(0deg); }
        }
        .icon-pop:hover {
          animation: pop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
      `}</style>
      <div className="mx-auto max-w-2xl px-4 flex justify-around items-center">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = tab.href ? isActive(tab.href) : false;
          const handleClick = () => {
            if (tab.id === "chat" && onChatClick) {
              onChatClick();
            } else if (tab.href) {
              router.push(tab.href);
            }
          };
          return (
            <button
              key={tab.id}
              onClick={handleClick}
              className="flex-1 py-4 px-2 flex flex-col items-center gap-1 transition-all duration-200 group relative"
              title={tab.label}
            >
              <div className="absolute inset-0 rounded-full bg-blue-100 opacity-0 group-hover:opacity-100 transition-opacity duration-200 -z-10 scale-75"></div>
              <Icon
                size={28}
                className={`transition-all duration-200 icon-pop ${active
                    ? "text-blue-600 scale-125"
                    : "text-gray-600 group-hover:text-blue-500 group-hover:scale-125"
                  }`}
                strokeWidth={active ? 2.5 : 2}
                fill={active ? "currentColor" : "none"}
              />
              <span
                className={`text-xs font-bold transition-all ${active ? "text-blue-600 opacity-100" : "text-gray-600 opacity-0 group-hover:opacity-75"
                  }`}
                style={{ fontFamily: "var(--font-poppins)" }}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
