import { Link, useLocation } from "react-router-dom";
import { Home, Search, PlusSquare, MessageCircle, Bell, Bookmark, LogOut } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { avatarUrl } from "../lib/avatar";
import Logo from "./Logo";

const nav = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/explore", icon: Search, label: "Explore" },
  { to: "/create", icon: PlusSquare, label: "Create" },
  { to: "/messages", icon: MessageCircle, label: "Messages" },
  { to: "/notifications", icon: Bell, label: "Notifications" },
  { to: "/saved", icon: Bookmark, label: "Saved" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const inChat = location.pathname.startsWith("/messages/");

  return (
    <div className="min-h-screen bg-[#f4f4f5] text-ink">
      {!inChat && (
        <header className="fixed top-0 left-0 right-0 z-40 border-b border-line/80 bg-white/90 backdrop-blur-md">
          <div className="max-w-6xl mx-auto flex items-center justify-between px-4 h-14">
            <Link to="/" className="hover:opacity-90 transition">
              <Logo size="sm" />
            </Link>
            <div className="flex items-center gap-3">
              {user && (
                <Link
                  to={`/profile/${user.username}`}
                  className="flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-full hover:bg-panel transition border border-transparent hover:border-line"
                >
                  <img src={avatarUrl(user)} alt="" className="w-8 h-8 rounded-full border border-line object-cover ring-2 ring-white" />
                  <span className="hidden sm:inline text-sm font-medium">{user.username}</span>
                </Link>
              )}
              <button type="button" onClick={() => logout()} className="p-2 rounded-lg text-muted hover:text-ink hover:bg-panel transition" title="Sign out">
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>
      )}

      <div className={`max-w-6xl mx-auto ${inChat ? "" : "pt-14"} flex`}>
        {!inChat && (
          <aside className="hidden md:flex flex-col w-56 fixed top-14 left-[max(0px,calc(50%-720px))] h-[calc(100vh-3.5rem)] p-4 border-r border-line/80 bg-white/80 backdrop-blur-sm">
            {nav.map(({ to, icon: Icon, label }) => {
              const active = location.pathname === to;
              return (
                <Link
                  key={to}
                  to={to}
                  className={`nav-item ${active ? "nav-active" : ""}`}
                >
                  <Icon size={20} strokeWidth={active ? 2 : 1.75} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </aside>
        )}

        <main className={`flex-1 w-full min-h-screen ${inChat ? "" : "md:ml-56 pb-20 md:pb-6"}`}>{children}</main>
      </div>

      {!inChat && (
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-line/80 bg-white/95 backdrop-blur-md flex justify-around py-2 safe-area-pb">
          {nav.slice(0, 5).map(({ to, icon: Icon }) => {
            const active = location.pathname === to;
            return (
              <Link
                key={to}
                to={to}
                className={`p-2.5 rounded-xl transition ${active ? "text-indigo-600 bg-indigo-50" : "text-muted"}`}
              >
                <Icon size={22} strokeWidth={active ? 2.25 : 1.75} />
              </Link>
            );
          })}
        </nav>
      )}
    </div>
  );
}
