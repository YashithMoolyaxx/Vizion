import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";
import PostCard from "../components/PostCard";

export default function PostPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);

  useEffect(() => {
    api.get(`/posts/${id}/`).then((r) => setPost(r.data)).catch(() => navigate("/"));
  }, [id, navigate]);

  if (!post) {
    return <div className="p-8 text-center text-muted text-sm">Loading post…</div>;
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <PostCard post={post} />
    </div>
  );
}
