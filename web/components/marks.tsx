export function ProductMark({ id, className = "h-16 w-16" }: { id: string; className?: string }) {
  return (
    <svg viewBox="0 0 80 80" className={className} aria-hidden="true">
      {shape(id)}
    </svg>
  );
}

function shape(id: string) {
  const stroke = "currentColor";
  switch (id) {
    case "lamp":
      return (
        <>
          <path d="M40 12v16" stroke={stroke} strokeWidth="1.6" />
          <path d="M24 28h32" stroke={stroke} strokeWidth="1.6" />
          <path d="M28 28c1 14 5 26 12 26s11-12 12-26" stroke={stroke} strokeWidth="1.6" fill="none" />
          <path d="M34 62h12" stroke={stroke} strokeWidth="1.6" />
        </>
      );
    case "headphones":
      return (
        <path
          d="M18 42v-6a22 22 0 0 1 44 0v6M18 40v14h8V40M54 40v14h8V40"
          stroke={stroke}
          strokeWidth="1.6"
          fill="none"
        />
      );
    case "mug":
      return (
        <path
          d="M24 24h28v28a10 10 0 0 1-10 10H34a10 10 0 0 1-10-10V24zm28 6h6a8 8 0 0 1 0 16h-6"
          stroke={stroke}
          strokeWidth="1.6"
          fill="none"
        />
      );
    case "throw":
      return (
        <path
          d="M18 26h44v28H18zM18 36h44M28 26v28M42 26v28"
          stroke={stroke}
          strokeWidth="1.6"
          fill="none"
        />
      );
    case "brew":
      return (
        <>
          <path d="M30 18h20M34 18c4 10 4 16 0 24h12c-4-8-4-14 0-24" stroke={stroke} strokeWidth="1.6" fill="none" />
          <path d="M26 48h28v8a6 6 0 0 1-6 6H32a6 6 0 0 1-6-6v-8z" stroke={stroke} strokeWidth="1.6" fill="none" />
        </>
      );
    case "stand":
      return (
        <path
          d="M16 54h48M22 54 34 24h12l12 30M34 24h12"
          stroke={stroke}
          strokeWidth="1.6"
          fill="none"
        />
      );
    case "candle":
      return (
        <>
          <path d="M40 16c4 6 4 10 0 14-4-4-4-8 0-14z" stroke={stroke} strokeWidth="1.6" fill="none" />
          <path d="M30 36h20v22a4 4 0 0 1-4 4H34a4 4 0 0 1-4-4V36z" stroke={stroke} strokeWidth="1.6" fill="none" />
        </>
      );
    default:
      return (
        <>
          <circle cx="40" cy="36" r="14" stroke={stroke} strokeWidth="1.6" fill="none" />
          <path d="M40 50v12M32 62h16" stroke={stroke} strokeWidth="1.6" />
        </>
      );
  }
}

const TINT: Record<string, string> = {
  desk: "bg-[#efe2cf] text-moss-deep",
  audio: "bg-[#e5eee9] text-moss-deep",
  kitchen: "bg-[#f6e4d4] text-clay",
  textile: "bg-[#efe6da] text-ink",
  home: "bg-[#e6eee8] text-moss-deep",
};

export function tintFor(category: string): string {
  return TINT[category] ?? "bg-paper-deep text-ink";
}
