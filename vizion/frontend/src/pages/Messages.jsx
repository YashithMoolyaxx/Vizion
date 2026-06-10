import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api";
import { avatarUrl } from "../lib/avatar";

export default function Messages() {
  const [rooms, setRooms] = useState([]);
  const location = useLocation();

  const load = () => api.get("/chat/rooms/").then((r) => setRooms(r.data));

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [location.pathname]);

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold mb-4 tracking-tight">Messages</h1>
      {rooms.length === 0 ? (
        <div className="card p-10 text-center text-sm text-muted">
          No conversations yet. Visit a profile and tap Message.
        </div>
      ) : (
        <div className="card divide-y divide-line overflow-hidden">
          {rooms.map((room) => {
            const active = location.pathname === `/messages/${room.id}`;
            return (
              <Link
                key={room.id}
                to={`/messages/${room.id}`}
                className={`flex items-center gap-3 p-4 transition ${active ? "bg-ink text-white" : "hover:bg-panel"}`}
              >
                <img
                  src={avatarUrl(room.other_user)}
                  alt=""
                  className={`w-11 h-11 rounded-full border ${active ? "border-white/30" : "border-line"}`}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold truncate">{room.other_user?.username}</p>
                  <p className={`text-xs truncate mt-0.5 ${active ? "text-white/70" : "text-muted"}`}>
                    {room.last_message || "Start chatting"}
                  </p>
                </div>
                {room.unread_count > 0 && !active && (
                  <span className="text-xs font-semibold bg-ink text-white px-2 py-0.5 rounded-full">
                    {room.unread_count}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
