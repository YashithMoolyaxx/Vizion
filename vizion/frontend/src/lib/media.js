export function mediaTypeFromFile(file) {
  if (!file) return "image";
  if (file.type.startsWith("video/")) return "video";
  if (file.type.startsWith("audio/")) return "audio";
  if (file.type.startsWith("image/")) return "image";
  const name = file.name?.toLowerCase() || "";
  if (/\.(mp4|webm|mov)$/.test(name)) return "video";
  if (/\.(mp3|wav|ogg|m4a|aac)$/.test(name)) return "audio";
  return "image";
}

export function mediaTypeFromUrl(url) {
  if (/\.(mp4|webm|mov)(\?|$)/i.test(url || "")) return "video";
  if (/\.(mp3|wav|ogg|m4a|aac)(\?|$)/i.test(url || "")) return "audio";
  return "image";
}
