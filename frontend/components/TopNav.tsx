import Link from "next/link";

const links = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/symptom-assistant", label: "Triage", icon: "🩺" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/community-forum", label: "Forum", icon: "👥" },
  { href: "/profile", label: "Profile", icon: "👤" },
];

export default function TopNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-2">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="flex w-full flex-col items-center justify-center gap-1 rounded-xl py-2 text-xs font-medium text-gray-700 hover:bg-gray-100 transition"
          >
            <span className="text-lg">{l.icon}</span>
            <span>{l.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}

