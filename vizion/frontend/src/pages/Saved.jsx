import { useEffect, useState } from "react";
import { api } from "../api";

export default function Saved() {
  const [collections, setCollections] = useState([]);
  const [active, setActive] = useState(null);
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    api.get("/collections/").then((r) => {
      setCollections(r.data);
      if (r.data.length) setActive(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!active) return;
    api.get(`/collections/${active}/posts/`).then((r) => setPosts(r.data.results || r.data));
  }, [active]);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-lg font-semibold mb-1">Saved</h1>
      <p className="text-sm text-muted mb-4">Smart collections auto-sort your bookmarks</p>

      <div className="flex gap-2 overflow-x-auto pb-4 mb-4 scrollbar-hide">
        {collections.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setActive(c.id)}
            className={`shrink-0 px-3 py-1.5 text-sm rounded-md border ${
              active === c.id ? "border-ink bg-ink text-white" : "border-line bg-white text-muted"
            }`}
          >
            {c.icon} {c.name} ({c.post_count})
          </button>
        ))}
      </div>

      {collections.length === 0 ? (
        <div className="card p-10 text-center text-sm text-muted">Save posts from your feed to build collections</div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {posts.map((sp) => (
            <div key={sp.id} className="card overflow-hidden">
              <img src={sp.post?.image} alt="" className="aspect-square object-cover w-full" />
              <div className="p-3">
                <p className="text-xs text-muted line-clamp-2">{sp.post?.caption}</p>
                {sp.auto_categorized && (
                  <p className="text-[11px] text-muted mt-1">Confidence {(sp.ai_confidence * 100).toFixed(0)}%</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
