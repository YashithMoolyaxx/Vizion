import { X } from "lucide-react";
import PostCard from "./PostCard";

export default function PostModal({ post, onClose }) {
  if (!post) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          onClick={onClose}
          className="absolute top-3 right-3 z-10 p-2 rounded-full bg-white border border-line shadow-sm"
        >
          <X size={18} />
        </button>
        <PostCard post={post} />
      </div>
    </div>
  );
}
