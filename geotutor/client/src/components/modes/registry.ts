import { MessageSquare, DraftingCompass, ScanSearch, type LucideIcon } from "lucide-react";

// Single source of truth for the app's three functionalities. Each one is a
// separate brain with its own endpoint and its own answer shape, so everything
// that varies per mode is declared here rather than scattered through the UI.

export type ModeId = "chat" | "design" | "forensic";

export interface ModeDefinition {
  id: ModeId;
  label: string;        // short label for the composer control
  fullName: string;     // spelled out, for badges and tooltips
  description: string;
  icon: LucideIcon;
  endpoint: string;     // brain route on the Python API
  enabled: boolean;     // false renders as "coming soon"
  accent: string;       // text colour class (theme token)
  tag: string;          // sidebar tag classes (theme tokens)
}

export const MODES: ModeDefinition[] = [
  {
    id: "chat",
    label: "Chat",
    fullName: "Chat",
    description: "Ask anything and get an answer grounded in the library",
    icon: MessageSquare,
    endpoint: "/ask-grounded",
    enabled: true,
    accent: "text-primary",
    tag: "bg-primary/10 text-primary border-primary/20",
  },
  {
    id: "design",
    label: "Design",
    fullName: "Geotech Design",
    description: "Solve a geotechnical design problem step by step",
    icon: DraftingCompass,
    endpoint: "/design",
    enabled: true,
    accent: "text-chart-2",
    tag: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  },
  {
    id: "forensic",
    label: "Forensic",
    fullName: "Forensic Analysis",
    description: "Trace cause and effect behind a geotechnical failure",
    icon: ScanSearch,
    endpoint: "/forensic",
    enabled: false,
    accent: "text-chart-1",
    tag: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  },
];

export const DEFAULT_MODE: ModeId = "chat";

export function getMode(id: ModeId | string | null | undefined): ModeDefinition {
  return MODES.find((m) => m.id === id) ?? MODES[0];
}

// ---------------------------------------------------------------------------
// Session history. Kept locally so the sidebar works for guests too; each entry
// records which mode produced it, which is what makes the list scannable.
// ---------------------------------------------------------------------------

const SESSIONS_KEY = "geotutor-sessions";
// the history panel keeps only the latest few tasks; older ones are dropped
// every time GeoTutor is opened
const MAX_SESSIONS = 5;

export interface SessionEntry {
  id: string;
  mode: ModeId;
  title: string;
  at: number;
}

export function readSessions(): SessionEntry[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    const list = raw ? (JSON.parse(raw) as SessionEntry[]) : [];
    return list.slice(0, MAX_SESSIONS);
  } catch {
    return [];
  }
}

export function recordSession(mode: ModeId, title: string): SessionEntry {
  const entry: SessionEntry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    mode,
    title: title.slice(0, 120),
    at: Date.now(),
  };
  try {
    const next = [entry, ...readSessions()].slice(0, MAX_SESSIONS);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(next));
    pruneSessionData(next);
    window.dispatchEvent(new Event("geotutor-sessions-changed"));
  } catch {
    /* storage unavailable: history just stays empty */
  }
  return entry;
}

// ---------------------------------------------------------------------------
// per-session conversation payloads, so a history click reopens the actual
// conversation rather than only its title
// ---------------------------------------------------------------------------

const DATA_PREFIX = `${SESSIONS_KEY}-data-`;

export function saveSessionData(id: string, data: unknown): void {
  try {
    localStorage.setItem(DATA_PREFIX + id, JSON.stringify(data));
  } catch {
    /* quota or storage unavailable: the session simply won't restore */
  }
}

export function readSessionData<T>(id: string): T | null {
  try {
    const raw = localStorage.getItem(DATA_PREFIX + id);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function pruneSessionData(kept: SessionEntry[]): void {
  try {
    const keep = new Set(kept.map((s) => DATA_PREFIX + s.id));
    const stale: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(DATA_PREFIX) && !keep.has(k)) stale.push(k);
    }
    stale.forEach((k) => localStorage.removeItem(k));
  } catch {
    /* best effort */
  }
}
