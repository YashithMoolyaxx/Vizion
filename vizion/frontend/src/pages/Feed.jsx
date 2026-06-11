import { useEffect, useState } from "react";
import { api } from "../api";
import PostCard from "../components/PostCard";
import { avatarUrl } from "../lib/avatar";

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [stories, setStories] = useState([]);
  const [tab, setTab] = useState("feed");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const feedRequest = tab === "feed" ? api.get("/feed/") : api.get("/feed/semantic/");
      const [feedRes, storiesRes] = await Promise.all([
        feedRequest,
        api.get("/stories/feed/").catch(() => ({ data: [] })),
      ]);
      setPosts(feedRes.data.results || feedRes.data);
      setStories(storiesRes.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [tab]);

  const storyUsers = [...new Map(stories.map((s) => [s.user?.id, s])).values()];

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      {storyUsers.length > 0 && (
        <div className="flex gap-4 overflow-x-auto pb-4 mb-4 scrollbar-hide border-b border-line">
          {storyUsers.map((s) => (
            <div key={s.id} className="flex flex-col items-center shrink-0 w-16">
              <div className="w-14 h-14 rounded-full border-2 border-ink p-0.5">
                <img
                  src={avatarUrl(s.user)}
                  alt=""
                  className="w-full h-full rounded-full object-cover bg-panel"
                />
              </div>
              <span className="text-[11px] mt-1 truncate w-full text-center text-muted">{s.user?.username}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex border border-line rounded-md p-0.5 mb-6 bg-panel">
        <button
          type="button"
          onClick={() => setTab("feed")}
          className={`flex-1 py-2 text-sm rounded ${tab === "feed" ? "bg-white shadow-sm font-medium" : "text-muted"}`}
        >
          Following
        </button>
        <button
          type="button"
          onClick={() => setTab("explore")}
          className={`flex-1 py-2 text-sm rounded ${tab === "explore" ? "bg-white shadow-sm font-medium" : "text-muted"}`}
        >
          Discover
        </button>
      </div>

      {loading ? (
        <div className="space-y-6">
          {[1, 2].map((i) => (
            <div key={i} className="card h-80 animate-pulse bg-panel" />
          ))}
        </div>
      ) : posts.length === 0 ? (
        <div className="card p-10 text-center">
          <p className="font-medium">No posts in this feed</p>
          <p className="text-sm text-muted mt-1">Follow creators or switch to Discover</p>
        </div>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} onUpdate={load} />)
      )}
    </div>
  );
}
