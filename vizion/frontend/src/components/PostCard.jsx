import { useState } from "react";
import { Heart, MessageCircle, Bookmark, Send, Share2 } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../api";
import UserChip from "./UserChip";

function isVideo(url) {
  return /\.(mp4|webm|mov)(\?|$)/i.test(url || "");
}

export default function PostCard({ post, onUpdate }) {
  const [liked, setLiked] = useState(post.is_liked);
  const [likes, setLikes] = useState(post.likes_count);
  const [saved, setSaved] = useState(post.is_saved);
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState([]);
  const [showComments, setShowComments] = useState(false);

  const toggleLike = async () => {
    const { data } = await api.post(`/posts/${post.id}/like/`);
    setLiked(data.liked);
    setLikes(data.likes_count);
  };

  const toggleSave = async () => {
    try {
      const { data } = await api.post(`/posts/${post.id}/save/`);
      const newSaved = data.is_saved !== false;
      setSaved(newSaved);
      toast.success(newSaved ? "Saved to collection" : "Removed from collection");
    } catch {
      toast.error("Failed to save post");
    }
  };

  const sharePost = async () => {
    const url = `${window.location.origin}/post/${post.id}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: "Vizion", text: post.caption || "Check out this post", url });
      } else {
        await navigator.clipboard.writeText(url);
        toast.success("Link copied to clipboard");
      }
    } catch {
      await navigator.clipboard.writeText(url);
      toast.success("Link copied to clipboard");
    }
  };

  const loadComments = async () => {
    const { data } = await api.get(`/posts/${post.id}/comments/`);
    setComments(data);
    setShowComments(true);
  };

  const submitComment = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;
    const { data } = await api.post(`/posts/${post.id}/comment/`, { content: comment });
    setComments((c) => [data, ...c]);
    setComment("");
    onUpdate?.();
  };

  return (
    <article className="card mb-6 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-line">
        <UserChip user={post.user} size="sm" />
      </div>

      <div className="bg-neutral-100 aspect-square flex items-center justify-center">
        {isVideo(post.image) ? (
          <video src={post.image} controls className="max-h-[640px] w-full object-contain bg-black" />
        ) : (
          <img src={post.image} alt="" className="max-h-[640px] w-full object-contain" />
        )}
      </div>

      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center gap-4">
          <button type="button" onClick={toggleLike} className="flex items-center gap-1.5 text-sm">
            <Heart size={22} strokeWidth={1.75} className={liked ? "fill-ink text-ink" : ""} />
            <span className="text-muted">{likes}</span>
          </button>
          <button type="button" onClick={loadComments} className="flex items-center gap-1.5 text-sm">
            <MessageCircle size={22} strokeWidth={1.75} />
            <span className="text-muted">{post.comments_count}</span>
          </button>
          <button type="button" onClick={sharePost} className="flex items-center gap-1.5 text-sm" title="Share">
            <Share2 size={22} strokeWidth={1.75} />
          </button>
          <button type="button" onClick={toggleSave} className="ml-auto">
            <Bookmark size={22} strokeWidth={1.75} className={saved ? "fill-ink" : ""} />
          </button>
        </div>

        {post.caption && (
          <p className="text-sm leading-relaxed">
            <span className="font-medium mr-2">{post.user?.username}</span>
            {post.caption}
          </p>
        )}

        {showComments && (
          <div className="pt-3 border-t border-line space-y-2">
            {comments.map((c) => (
              <p key={c.id} className="text-sm">
                <span className="font-medium mr-2">{c.user?.username}</span>
                {c.content}
              </p>
            ))}
            <form onSubmit={submitComment} className="flex gap-2 pt-1">
              <input
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment…"
                className="input flex-1 py-2"
              />
              <button type="submit" className="btn-secondary px-3">
                <Send size={16} />
              </button>
            </form>
          </div>
        )}
      </div>
    </article>
  );
}
