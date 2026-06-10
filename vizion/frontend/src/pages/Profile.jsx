import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { Camera, MessageCircle, UserPlus } from "lucide-react";
import { api } from "../api";
import { avatarUrl } from "../lib/avatar";
import { useAuthStore } from "../store/authStore";
import PostModal from "../components/PostModal";

export default function Profile() {
  const { username } = useParams();
  const navigate = useNavigate();
  const { user: me, fetchMe } = useAuthStore();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);
  const [bio, setBio] = useState("");
  const [editing, setEditing] = useState(false);
  const [selectedPost, setSelectedPost] = useState(null);

  const load = () => {
    api.get(`/users/${username}/`).then((r) => {
      setProfile(r.data);
      setBio(r.data.bio || "");
    });
    api.get(`/users/${username}/posts/`).then((r) => setPosts(r.data.results || r.data));
  };

  useEffect(() => {
    load();
  }, [username]);

  const follow = async () => {
    await api.post(`/users/${profile.id}/follow/`);
    toast.success("Following");
    setProfile((p) => ({ ...p, is_following: true }));
  };

  const message = async () => {
    const { data } = await api.post("/chat/dm/", { user_id: profile.id });
    navigate(`/messages/${data.id}`);
  };

  const saveProfile = async () => {
    await api.patch("/auth/me/", { bio });
    toast.success("Profile updated");
    setEditing(false);
    fetchMe();
    load();
  };

  const openPost = async (postId) => {
    try {
      const { data } = await api.get(`/posts/${postId}/`);
      setSelectedPost(data);
    } catch {
      toast.error("Could not load post");
    }
  };

  const changeAvatar = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    await api.post("/auth/avatar/", form, { headers: { "Content-Type": "multipart/form-data" } });
    toast.success("Photo updated");
    fetchMe();
    load();
  };

  if (!profile) {
    return <div className="p-8 text-center text-muted text-sm">Loading profile…</div>;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="card p-6 mb-6">
        <div className="flex gap-6 items-start">
          <div className="relative shrink-0">
            <img
              src={avatarUrl(profile)}
              alt=""
              className="w-24 h-24 rounded-full object-cover border-2 border-ink"
            />
            {profile.is_me && (
              <label className="absolute bottom-0 right-0 p-1.5 rounded-full bg-ink text-white cursor-pointer hover:bg-neutral-800">
                <Camera size={14} />
                <input type="file" accept="image/*" className="hidden" onChange={changeAvatar} />
              </label>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-semibold tracking-tight">{profile.username}</h1>
            <div className="flex gap-5 mt-3 text-sm">
              <span><strong>{profile.posts_count}</strong> <span className="text-muted">posts</span></span>
              <span><strong>{profile.followers_count}</strong> <span className="text-muted">followers</span></span>
              <span><strong>{profile.following_count}</strong> <span className="text-muted">following</span></span>
            </div>
          </div>
        </div>

        {profile.is_me ? (
          <div className="mt-5 pt-5 border-t border-line">
            {editing ? (
              <div className="space-y-3">
                <textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={3} className="input resize-none" placeholder="Bio" />
                <div className="flex gap-2">
                  <button type="button" onClick={saveProfile} className="btn-primary">Save</button>
                  <button type="button" onClick={() => setEditing(false)} className="btn-secondary">Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-sm text-neutral-600">{profile.bio || "Add a bio to tell people about you."}</p>
                <button type="button" onClick={() => setEditing(true)} className="btn-secondary mt-3 text-xs">
                  Edit profile
                </button>
              </>
            )}
          </div>
        ) : (
          profile.bio && <p className="mt-4 text-sm text-neutral-600">{profile.bio}</p>
        )}
      </div>

      {!profile.is_me && (
        <div className="flex gap-2 mb-6">
          {!profile.is_following && (
            <button type="button" onClick={follow} className="btn-primary flex-1 gap-2">
              <UserPlus size={16} /> Follow
            </button>
          )}
          <button type="button" onClick={message} className="btn-secondary flex-1 gap-2">
            <MessageCircle size={16} /> Message
          </button>
        </div>
      )}

      <div className="grid grid-cols-3 gap-1 border border-line rounded-lg overflow-hidden">
        {posts.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => openPost(p.id)}
            className="aspect-square bg-panel hover:opacity-90 transition overflow-hidden"
          >
            {/\.(mp4|webm|mov)(\?|$)/i.test(p.image) ? (
              <video src={p.image} className="w-full h-full object-cover" muted />
            ) : (
              <img src={p.image} alt="" className="w-full h-full object-cover" />
            )}
          </button>
        ))}
      </div>

      {selectedPost && <PostModal post={selectedPost} onClose={() => setSelectedPost(null)} />}
    </div>
  );
}
