import { Link } from "react-router-dom";
import { avatarUrl } from "../lib/avatar";

export default function UserChip({ user, size = "md", link = true, onClick }) {
  const sizes = { sm: "w-8 h-8 text-sm", md: "w-10 h-10 text-sm", lg: "w-14 h-14 text-base" };
  const inner = (
    <div className={`flex items-center gap-2.5 ${onClick ? "cursor-pointer" : ""}`} onClick={onClick}>
      <img
        src={avatarUrl(user)}
        alt={user?.username}
        className={`${sizes[size].split(" ").slice(0, 2).join(" ")} rounded-full object-cover border border-line bg-panel shrink-0`}
      />
      {user?.username && (
        <span className={`font-medium truncate ${sizes[size].split(" ")[2] || "text-sm"}`}>{user.username}</span>
      )}
    </div>
  );

  if (link && user?.username) {
    return <Link to={`/profile/${user.username}`} className="hover:opacity-80 transition">{inner}</Link>;
  }
  return inner;
}
