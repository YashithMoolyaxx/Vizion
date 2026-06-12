import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Heart, MessageCircle, UserPlus } from "lucide-react";
import { api } from "../api";

const icons = { like: Heart, comment: MessageCircle, follow: UserPlus, message: MessageCircle };
const labels = {
  like: "liked your post",
  comment: "commented on your post",
  follow: "started following you",
  message: "sent you a message",
};

export default function Notifications() {
  const [notifs, setNotifs] = useState([]);

  useEffect(() => {
    api.get("/notifications/").then((r) => setNotifs(r.data));
    api.post("/notifications/read/");
  }, []);

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold mb-4">Notifications</h1>
      {notifs.length === 0 ? (
        <div className="card p-10 text-center text-sm text-muted">No notifications yet</div>
      ) : (
        <div className="card divide-y divide-line">
          {notifs.map((n) => {
            const Icon = icons[n.notification_type] || Heart;
            return (
              <div key={n.id} className="flex items-start gap-3 p-4">
                <Icon size={18} className="text-muted mt-0.5 shrink-0" strokeWidth={1.75} />
                <p className="text-sm">
                  <Link to={`/profile/${n.sender?.username}`} className="font-medium underline-offset-2 hover:underline">
                    {n.sender?.username}
                  </Link>{" "}
                  <span className="text-muted">{labels[n.notification_type] || n.notification_type}</span>
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
