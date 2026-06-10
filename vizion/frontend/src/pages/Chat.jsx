import { useEffect, useRef, useState, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Paperclip, Send } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../api";
import { getAccessToken } from "../lib/auth";
import { avatarUrl } from "../lib/avatar";
import { mediaTypeFromFile } from "../lib/media";
import { useAuthStore } from "../store/authStore";
import MessageBubble from "../components/MessageBubble";

function wsUrl(roomId) {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const token = getAccessToken();
  return `${proto}://${window.location.host}/ws/chat/${roomId}/?token=${encodeURIComponent(token || "")}`;
}

function normalizeMessage(data) {
  return {
    id: data.id,
    content: data.message ?? data.content ?? "",
    media_url: data.media_url || "",
    media_type: data.media_type || "",
    sender: data.sender || {
      id: data.sender_id,
      username: data.sender_username,
      avatar_url: data.sender_avatar,
    },
    created_at: data.created_at,
  };
}

export default function Chat() {
  const { id } = useParams();
  const { user: me } = useAuthStore();
  const [room, setRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [online, setOnline] = useState(false);
  const [uploading, setUploading] = useState(false);
  const bottomRef = useRef(null);
  const wsRef = useRef(null);
  const fileRef = useRef(null);
  const seenIds = useRef(new Set());

  const mergeMessages = useCallback((incoming) => {
    setMessages((prev) => {
      const map = new Map(prev.map((m) => [m.id, m]));
      incoming.forEach((m) => {
        if (m.id) map.set(m.id, m);
      });
      return Array.from(map.values()).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    });
  }, []);

  const loadMessages = useCallback(async () => {
    const { data } = await api.get(`/chat/rooms/${id}/messages/`);
    const list = (data.results || data).map(normalizeMessage);
    list.forEach((m) => seenIds.current.add(m.id));
    mergeMessages(list);
  }, [id, mergeMessages]);

  const pushMessage = useCallback(
    (raw) => {
      const m = normalizeMessage(raw);
      if (m.id && seenIds.current.has(m.id)) return;
      if (m.id) seenIds.current.add(m.id);
      mergeMessages([m]);
    },
    [mergeMessages]
  );

  useEffect(() => {
    api.get(`/chat/rooms/${id}/`).then((r) => setRoom(r.data));
    loadMessages();
    api.post(`/chat/rooms/${id}/read/`).catch(() => {});

    const ws = new WebSocket(wsUrl(id));
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "presence") {
        setOnline(data.online);
        return;
      }
      pushMessage(data);
    };

    const poll = setInterval(loadMessages, 5000);
    return () => {
      clearInterval(poll);
      ws.close();
    };
  }, [id, loadMessages, pushMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendPayload = async (payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    } else {
      const { data } = await api.post(`/chat/rooms/${id}/send/`, payload);
      pushMessage(data);
    }
  };

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    const content = text.trim();
    setText("");
    await sendPayload({ content });
  };

  const sendMedia = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data: upload } = await api.post("/upload/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const media_type = mediaTypeFromFile(file);
      await sendPayload({ content: text.trim(), media_url: upload.url, media_type });
      setText("");
      toast.success("Media sent");
    } catch {
      toast.error("Could not send media");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const other = room?.other_user;

  return (
    <div className="max-w-lg mx-auto flex flex-col h-[calc(100vh-3.5rem)] border-x border-line bg-white">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-line bg-panel/50">
        <Link to="/messages" className="p-1.5 rounded-md hover:bg-white border border-transparent hover:border-line">
          <ArrowLeft size={18} />
        </Link>
        {other && (
          <>
            <img src={avatarUrl(other)} alt="" className="w-9 h-9 rounded-full border border-line" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">{other.username}</p>
              <p className="text-xs text-muted">{online ? "Active in chat" : "Offline"}</p>
            </div>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-[#fafafa]">
        {messages.length === 0 && (
          <p className="text-center text-sm text-muted py-8">Send a message or share media to start the conversation.</p>
        )}
        {messages.map((m) => {
          const mine = m.sender?.id === me?.id;
          return (
            <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[82%] ${mine ? "" : "flex gap-2 items-end"}`}>
                {!mine && (
                  <img src={avatarUrl(m.sender)} alt="" className="w-7 h-7 rounded-full border border-line shrink-0" />
                )}
                <div
                  className={`px-3.5 py-2.5 text-sm rounded-2xl ${
                    mine ? "bg-ink text-white rounded-br-md" : "bg-white border border-line rounded-bl-md shadow-sm text-ink"
                  }`}
                >
                  {!mine && <p className="text-[11px] font-medium text-muted mb-1">{m.sender?.username}</p>}
                  <MessageBubble message={m} mine={mine} />
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={send} className="flex gap-2 p-4 border-t border-line bg-white items-center">
        <input ref={fileRef} type="file" accept="image/*,video/*,audio/*,.mp3,.wav,.ogg,.m4a" className="hidden" onChange={sendMedia} />
        <button
          type="button"
          disabled={uploading}
          onClick={() => fileRef.current?.click()}
          className="btn-secondary px-3 shrink-0"
          title="Send image, video, or audio"
        >
          <Paperclip size={18} />
        </button>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={uploading ? "Uploading…" : `Message ${other?.username || ""}…`}
          className="input flex-1"
          disabled={uploading}
        />
        <button type="submit" disabled={uploading} className="btn-primary px-3.5 shrink-0">
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
