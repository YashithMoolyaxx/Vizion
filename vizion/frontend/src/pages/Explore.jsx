import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "../api";
import { avatarUrl } from "../lib/avatar";
import PostModal from "../components/PostModal";
import UserChip from "../components/UserChip";

export default function Explore() {
  const [posts, setPosts] = useState([]);
  const [users, setUsers] = useState([]);
  const [q, setQ] = useState("");
  const [selectedPost, setSelectedPost] = useState(null);

  useEffect(() => {
    api.get("/posts/").then((r) => setPosts(r.data.results || r.data));
  }, []);

  const openPost = async (postId) => {
    const { data } = await api.get(`/posts/${postId}/`);
    setSelectedPost(data);
  };

  const search = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    const { data } = await api.get(`/users/search/?q=${encodeURIComponent(q)}`);
    setUsers(data);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold mb-4 tracking-tight">Explore</h1>

      <form onSubmit={search} className="flex gap-2 mb-6">
        <div className="flex-1 flex items-center gap-2 card px-3 py-0">
          <Search size={18} className="text-muted shrink-0" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search creators"
            className="flex-1 py-2.5 text-sm outline-none bg-transparent"
          />
        </div>
        <button type="submit" className="btn-primary">Search</button>
      </form>

      {users.length > 0 && (
        <div className="card divide-y divide-line mb-6">
          {users.map((u) => (
            <Link key={u.id} to={`/profile/${u.username}`} className="flex items-center gap-3 p-4 hover:bg-panel">
              <UserChip user={u} link={false} />
            </Link>
          ))}
        </div>
      )}

      <p className="text-xs text-muted uppercase tracking-wide mb-2 font-medium">Trending posts</p>
      <div className="grid grid-cols-3 gap-0.5 border border-line rounded-lg overflow-hidden">
        {posts.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => openPost(p.id)}
            className="aspect-square bg-panel relative group"
          >
            <img src={p.image} alt="" className="w-full h-full object-cover group-hover:scale-[1.02] transition duration-300" />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition" />
            {p.user && (
              <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition">
                <div className="flex items-center gap-1.5">
                  <img src={avatarUrl(p.user)} alt="" className="w-5 h-5 rounded-full border border-white/30" />
                  <span className="text-[11px] text-white font-medium truncate">{p.user.username}</span>
                </div>
              </div>
            )}
          </button>
        ))}
      </div>

      {selectedPost && <PostModal post={selectedPost} onClose={() => setSelectedPost(null)} />}
    </div>
  );
}
