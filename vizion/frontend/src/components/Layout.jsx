import { Link, useLocation } from "react-router-dom";
import { Home, Search, PlusSquare, MessageCircle, Heart, Bookmark, LogOut } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { avatarUrl } from "../lib/avatar";

const nav = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/explore", icon: Search, label: "Explore" },
  { to: "/create", icon: PlusSquare, label: "Create" },
  { to: "/messages", icon: MessageCircle, label: "Messages" },
  { to: "/notifications", icon: Heart, label: "Activity" },
  { to: "/saved", icon: Bookmark, label: "Saved" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const inChat = location.pathname.startsWith("/messages/");

  return (
    <div className="min-h-screen bg-[#fafafa] text-ink">
      {!inChat && (
        <header className="fixed top-0 left-0 right-0 z-40 border-b border-line bg-white/95 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto flex items-center justify-between px-4 h-14">
            <Link to="/" className="text-lg font-bold tracking-tight">
              Vizion
            </Link>
            <div className="flex items-center gap-3">
              {user && (
                <Link
                  to={`/profile/${user.username}`}
                  className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-full hover:bg-panel transition border border-transparent hover:border-line"
                >
                  <img src={avatarUrl(user)} alt="" className="w-8 h-8 rounded-full border border-line object-cover" />
                  <span className="hidden sm:inline text-sm font-medium">{user.username}</span>
                </Link>
              )}
              <button type="button" onClick={() => logout()} className="p-2 rounded-md text-muted hover:text-ink hover:bg-panel" title="Sign out">
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </header>
      )}

      <div className={`max-w-6xl mx-auto ${inChat ? "" : "pt-14"} flex`}>
        {!inChat && (
          <aside className="hidden md:flex flex-col w-56 fixed top-14 left-[max(0px,calc(50%-720px))] h-[calc(100vh-3.5rem)] p-4 border-r border-line bg-white">
            {nav.map(({ to, icon: Icon, label }) => (
              <Link key={to} to={to} className={`nav-item ${location.pathname === to ? "nav-active" : ""}`}>
                <Icon size={20} strokeWidth={1.75} />
                <span>{label}</span>
              </Link>
            ))}
          </aside>
        )}

        <main className={`flex-1 w-full min-h-screen ${inChat ? "" : "md:ml-56 pb-20 md:pb-6"}`}>{children}</main>
      </div>

      {!inChat && (
        <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-line bg-white flex justify-around py-2">
          {nav.slice(0, 5).map(({ to, icon: Icon }) => (
            <Link key={to} to={to} className={`p-2.5 rounded-md ${location.pathname === to ? "text-ink" : "text-muted"}`}>
              <Icon size={22} strokeWidth={1.75} />
            </Link>
          ))}
        </nav>
      )}
    </div>
  );
}
