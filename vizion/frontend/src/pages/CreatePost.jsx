import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { api } from "../api";

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
      const form = new FormData();
      form.append("file", file);
      const { data: upload } = await api.post("/upload/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await api.post("/posts/", { image: upload.url, caption });
      toast.success("Post published");
      navigate("/");
    } catch {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold mb-4">New post</h1>
      <form onSubmit={submit} className="card p-6 space-y-4">
        <label className="flex flex-col items-center justify-center border border-dashed border-line rounded-md h-64 cursor-pointer hover:bg-panel transition">
          {preview ? (
            file?.type?.startsWith("video") ? (
              <video src={preview} controls className="max-h-56 rounded" />
            ) : (
              <img src={preview} alt="" className="max-h-56 object-contain" />
            )
          ) : (
            <div className="text-center text-muted text-sm px-4">
              <p className="font-medium text-ink">Upload media</p>
              <p className="mt-1">Image or video (MP4)</p>
            </div>
          )}
          <input type="file" accept="image/*,video/*" className="hidden" onChange={onFile} />
        </label>

        <textarea
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="Caption"
          rows={3}
          className="input resize-none"
        />

        <button type="submit" disabled={uploading} className="btn-primary w-full">
          {uploading ? "Publishing…" : "Publish"}
        </button>
      </form>
    </div>
  );
}
