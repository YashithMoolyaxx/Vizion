export function avatarUrl(user) {
  if (!user) return "https://api.dicebear.com/7.x/notionists/svg?seed=guest";
  return user.avatar_url || user.profile_picture || `https://api.dicebear.com/7.x/notionists/svg?seed=${user.username}`;
}
