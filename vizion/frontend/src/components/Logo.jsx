const sizes = {
  sm: { box: "w-7 h-7", text: "text-lg", gap: "gap-2" },
  md: { box: "w-8 h-8", text: "text-xl", gap: "gap-2.5" },
  lg: { box: "w-11 h-11", text: "text-3xl", gap: "gap-3" },
};

export default function Logo({ size = "md", className = "" }) {
  const s = sizes[size] || sizes.md;

  return (
    <span className={`inline-flex items-center ${s.gap} ${className}`}>
      <span
        className={`${s.box} rounded-xl bg-gradient-to-br from-violet-600 via-indigo-600 to-sky-500 flex items-center justify-center shadow-md shadow-indigo-500/25 ring-1 ring-white/20`}
        aria-hidden
      >
        <svg viewBox="0 0 24 24" className="w-[55%] h-[55%]" fill="none">
          <circle cx="12" cy="12" r="3.5" stroke="white" strokeWidth="1.75" />
          <circle cx="12" cy="12" r="7" stroke="white" strokeWidth="1.75" strokeDasharray="3 2.5" />
          <circle cx="12" cy="12" r="1.25" fill="white" />
        </svg>
      </span>
      <span
        className={`font-bold tracking-tight ${s.text} bg-gradient-to-r from-violet-700 via-indigo-600 to-sky-600 bg-clip-text text-transparent`}
      >
        Vizion
      </span>
    </span>
  );
}
