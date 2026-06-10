export default function MessageBubble({ message, mine }) {
  const { content, media_url, media_type } = message;

  return (
    <div>
      {media_url && media_type === "image" && (
        <img src={media_url} alt="" className="rounded-lg max-w-full mb-1 border border-line" />
      )}
      {media_url && media_type === "video" && (
        <video src={media_url} controls className="rounded-lg max-w-full mb-1 bg-black" />
      )}
      {media_url && media_type === "audio" && (
        <audio src={media_url} controls className="w-full min-w-[220px] mb-1" />
      )}
      {content && <span>{content}</span>}
    </div>
  );
}
