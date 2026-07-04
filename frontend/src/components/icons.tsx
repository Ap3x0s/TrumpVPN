// SVG icon catalog. Apps use real brand paths from `simple-icons`.
// Devices use custom inline SVG. Country flags use regional-indicator emoji.

import type { JSX } from "react";
import {
  siYoutube, siTelegram, siInstagram, siX, siWhatsapp,
  siClaude, siTwitch, siSpotify, siTiktok, siDiscord,
} from "simple-icons";

// ChatGPT (OpenAI) is not in simple-icons — custom hexagonal-node path.
const CHATGPT_PATH = "M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v3l-2.597 1.5-2.607-1.5z";

const brandStroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function flagEmoji(code: string): string {
  return code.toUpperCase().replace(/./g, (c) => String.fromCodePoint(127397 + c.charCodeAt(0)));
}

/** Brand icon (filled, brand path from simple-icons). */
function BrandIcon({ path, size = 22 }: { path: string; size?: number }): JSX.Element {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} fill="currentColor" aria-hidden="true">
      <path d={path} />
    </svg>
  );
}

/** App icon by name. Falls back to a generic globe. */
export function appIcon(name: string): JSX.Element {
  const key = name.toLowerCase();
  const map: Record<string, string> = {
    youtube: siYoutube.path,
    telegram: siTelegram.path,
    instagram: siInstagram.path,
    x: siX.path,
    whatsapp: siWhatsapp.path,
    claude: siClaude.path,
    twitch: siTwitch.path,
    spotify: siSpotify.path,
    tiktok: siTiktok.path,
    discord: siDiscord.path,
    chatgpt: CHATGPT_PATH,
  };
  const path = map[key];
  if (path) return <BrandIcon path={path} />;
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" {...brandStroke}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </svg>
  );
}

/** Device icon by name (custom SVG, no brand kit available). */
export function deviceIcon(name: string): JSX.Element {
  const icons: Record<string, JSX.Element> = {
    phone: (
      <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
        <rect x="6" y="2.5" width="12" height="19" rx="3" />
        <path d="M10 18h4" />
      </svg>
    ),
    apple: (
      <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
        <path d="M16 2c-1 .5-2 1.5-2 3 0 .5 0 1 .3 1.5-1.5 0-3 .8-4 2-1.5 0-3 .5-4 2-1.5 2.5-1 6 1 9 1 1.5 2 2.5 3.5 2.5 1 0 1.5-.3 2.5-.3s1.5.3 2.5.3c1.5 0 2.5-1 3.5-2.5.8-1 1.3-2.3 1.5-3.5-1.5-.5-2.5-2-2.5-3.5 0-1.5 1-2.8 2.3-3.3C19.5 4 18 3 16 2.5z" />
      </svg>
    ),
    laptop: (
      <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
        <rect x="4" y="5" width="16" height="11" rx="1" />
        <path d="M2 20h20" />
      </svg>
    ),
    monitor: (
      <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
        <rect x="3" y="4" width="18" height="13" rx="2" />
        <path d="M9 21h6M12 17v4" />
      </svg>
    ),
    router: (
      <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
        <rect x="3" y="13" width="18" height="7" rx="2" />
        <path d="M7 17h.01M11 17h6" />
        <path d="M12 13V4M8 7l4-3 4 3" />
      </svg>
    ),
    tv: (
      <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
        <rect x="2" y="6" width="20" height="13" rx="2" />
        <path d="M8 3l4 3 4-3" />
      </svg>
    ),
  };
  return icons[name] ?? (
    <svg viewBox="0 0 24 24" width="26" height="26" {...brandStroke}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
    </svg>
  );
}
