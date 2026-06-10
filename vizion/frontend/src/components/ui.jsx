export function Button({ className = "", variant = "primary", ...props }) {
  const base = variant === "primary" ? "btn-primary" : "btn-secondary";
  return <button type="button" className={`${base} ${className}`} {...props} />;
}

export function Card({ className = "", children }) {
  return <div className={`card p-4 ${className}`}>{children}</div>;
}
