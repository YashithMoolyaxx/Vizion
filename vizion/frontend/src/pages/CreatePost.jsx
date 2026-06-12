import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ImagePlus, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../api";
import { uploadFile, uploadErrorMessage } from "../lib/upload";

export default function CreatePost() {
  const [caption, setCaption] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!file) return toast.error("Select an image or video");
    setUploading(true);
    try {
      const imageUrl = await uploadFile(file);
      await api.post("/posts/", { image: imageUrl, caption });
      toast.success("Post published");
      navigate("/");
    } catch (err) {
      toast.error(uploadErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold tracking-tight">Create post</h1>
        <p className="text-sm text-muted mt-1">Share a photo or video with your audience</p>
      </div>

      <form onSubmit={submit} className="card overflow-hidden">
        <label
          className="group flex flex-col items-center justify-center border-b border-line bg-gradient-to-b from-indigo-50/80 to-white h-72 cursor-pointer transition hover:from-violet-50"
        >
          {preview ? (
            file?.type?.startsWith("video") ? (
              <video src={preview} controls className="max-h-64 rounded-lg shadow-sm" />
            ) : (
              <img src={preview} alt="" className="max-h-64 object-contain rounded-lg shadow-sm" />
            )
          ) : (
            <div className="text-center px-6">
              <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 to-sky-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 mb-4 group-hover:scale-105 transition-transform">
                <ImagePlus size={26} className="text-white" strokeWidth={1.75} />
              </div>
              <p className="font-medium text-ink">Drag & drop or tap to upload</p>
              <p className="text-sm text-muted mt-1">JPG, PNG, WEBP, HEIC, MP4 — up to 50 MB</p>
            </div>
          )}
          <input type="file" accept="image/*,video/*" className="hidden" onChange={onFile} />
        </label>

        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs font-medium text-muted uppercase tracking-wide">Caption</label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Write something about your post…"
              rows={3}
              className="input resize-none mt-1.5"
            />
          </div>

          <button type="submit" disabled={uploading || !file} className="btn-primary w-full py-3">
            {uploading ? (
              "Publishing…"
            ) : (
              <span className="inline-flex items-center gap-2">
                <Sparkles size={16} />
                Publish post
              </span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
