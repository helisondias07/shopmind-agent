export function ProductFigure({ imageKey, label }: { imageKey: string; label: string }) {
  return (
    <svg viewBox="0 0 280 420" role="img" aria-label={label}>
      {imageKey === "lamp" ? <Lamp /> : null}
      {imageKey === "mug" ? <Mug /> : null}
      {imageKey === "headphones" ? <Headphones /> : null}
      {imageKey === "charger" ? <Charger /> : null}
      {imageKey === "throw" ? <Throw /> : null}
      {imageKey === "brew" ? <Brew /> : null}
      {imageKey === "stand" ? <Stand /> : null}
      {imageKey === "candle" ? <Candle /> : null}
    </svg>
  );
}

function Floor() {
  return <ellipse cx="140" cy="392" rx="78" ry="10" fill="#b7b2aa" />;
}

function Lamp() {
  return (
    <>
      <defs>
        <linearGradient id="ceramic" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#9e9890" />
          <stop offset="42%" stopColor="#d4cfc6" />
          <stop offset="100%" stopColor="#8f8981" />
        </linearGradient>
        <linearGradient id="ceramicTop" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#e2ddd4" />
          <stop offset="100%" stopColor="#b7b1a8" />
        </linearGradient>
        <linearGradient id="brass" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#c4a35a" />
          <stop offset="45%" stopColor="#8a6a32" />
          <stop offset="100%" stopColor="#5e4620" />
        </linearGradient>
        <linearGradient id="shadeOut" x1="0" y1="0" x2="0.3" y2="1">
          <stop offset="0%" stopColor="#efe8da" />
          <stop offset="100%" stopColor="#c9c0b0" />
        </linearGradient>
        <linearGradient id="shadeIn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fff6d8" />
          <stop offset="100%" stopColor="#e8c56a" />
        </linearGradient>
      </defs>
      <polygon points="100,172 216,162 208,300 84,292" fill="#f3e6c8" opacity="0.5" />
      <ellipse cx="118" cy="402" rx="72" ry="9" fill="#a8a29a" />
      <path d="M52 372 C52 358, 184 358, 184 372 L176 398 C176 408, 60 408, 60 398 Z" fill="url(#ceramic)" />
      <ellipse cx="118" cy="372" rx="66" ry="13" fill="url(#ceramicTop)" />
      <rect x="112" y="318" width="12" height="56" rx="2" fill="url(#brass)" />
      <circle cx="118" cy="318" r="8" fill="url(#brass)" />
      <path
        d="M118 318 L118 250 L170 204"
        fill="none"
        stroke="url(#brass)"
        strokeWidth="8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="118" cy="250" r="7" fill="#c4a35a" />
      <circle cx="118" cy="250" r="3.5" fill="#5e4620" />
      <circle cx="170" cy="204" r="7" fill="#c4a35a" />
      <circle cx="170" cy="204" r="3.5" fill="#5e4620" />
      <path d="M170 204 L170 150" fill="none" stroke="url(#brass)" strokeWidth="7" strokeLinecap="round" />
      <circle cx="170" cy="150" r="6" fill="url(#brass)" />
      <path d="M108 96 L228 112 L216 162 L94 148 Z" fill="url(#shadeOut)" stroke="#b7afa0" strokeWidth="0.75" />
      <path d="M108 96 L228 112 L222 124 L116 108 Z" fill="#f3ebda" />
      <path d="M108 142 L212 156 L206 166 L100 152 Z" fill="url(#shadeIn)" />
      <path d="M204 160 L208 184" stroke="#8a6a32" strokeWidth="1.2" />
      <circle cx="208" cy="188" r="2.4" fill="#8a6a32" />
    </>
  );
}

function Mug() {
  return (
    <>
      <Floor />
      <path d="M78 168 h96 v150 c0 28 -20 46 -48 46 s-48 -18 -48 -46 z" fill="#d4cfc6" stroke="#8f8981" />
      <path d="M78 168 h96 v18 h-96 z" fill="#efe8da" />
      <ellipse cx="126" cy="168" rx="48" ry="12" fill="#f4efe6" stroke="#b7b1a8" />
      <path d="M174 190 h22 a28 28 0 0 1 0 56 h-22" fill="none" stroke="#8a6a32" strokeWidth="8" />
    </>
  );
}

function Headphones() {
  return (
    <>
      <Floor />
      <path d="M78 210 a62 62 0 0 1 124 0" fill="none" stroke="#1a1c1f" strokeWidth="10" />
      <rect x="62" y="198" width="28" height="64" rx="8" fill="#c7c2ba" stroke="#8f8981" />
      <rect x="190" y="198" width="28" height="64" rx="8" fill="#c7c2ba" stroke="#8f8981" />
      <rect x="68" y="210" width="16" height="40" rx="4" fill="#5c4318" />
      <rect x="196" y="210" width="16" height="40" rx="4" fill="#5c4318" />
    </>
  );
}

function Charger() {
  return (
    <>
      <Floor />
      <ellipse cx="140" cy="250" rx="70" ry="22" fill="#c4a35a" />
      <ellipse cx="140" cy="242" rx="70" ry="22" fill="#e4d3a2" stroke="#8a6a32" />
      <circle cx="140" cy="242" r="16" fill="none" stroke="#5c4318" strokeWidth="3" />
      <path d="M190 250 q40 20 24 70" fill="none" stroke="#1a1c1f" strokeWidth="4" />
    </>
  );
}

function Throw() {
  return (
    <>
      <Floor />
      <path d="M70 150 h140 l-16 200 h-108 z" fill="#e8e2d4" stroke="#c7c2ba" />
      <path d="M70 190 h140 M78 230 h124 M86 270 h108" stroke="#c7c2ba" />
    </>
  );
}

function Brew() {
  return (
    <>
      <Floor />
      <path d="M108 150 h64 l-10 40 h-44 z" fill="#efe8da" stroke="#8f8981" />
      <path d="M100 190 h80 v90 a40 40 0 0 1 -80 0 z" fill="#d5e0e6" stroke="#9aa8b0" opacity="0.9" />
      <path d="M180 210 h28 a20 20 0 0 1 0 40 h-28" fill="none" stroke="#8a6a32" strokeWidth="6" />
    </>
  );
}

function Stand() {
  return (
    <>
      <Floor />
      <path d="M70 300 h150" stroke="#8f8981" strokeWidth="8" />
      <path d="M90 300 l40 -130 h70 l-20 130" fill="#d4cfc6" stroke="#8f8981" />
    </>
  );
}

function Candle() {
  return (
    <>
      <Floor />
      <rect x="108" y="210" width="64" height="120" rx="4" fill="#efe8da" stroke="#c7c2ba" />
      <path d="M140 210 v-28" stroke="#1a1c1f" strokeWidth="2" />
      <path d="M140 168 c10 14 10 24 0 32 c-10 -8 -10 -18 0 -32 z" fill="#f3e6c8" stroke="#8a6a32" />
    </>
  );
}
