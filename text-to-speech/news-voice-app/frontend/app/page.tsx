"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Maximize2, Pause, Play, Radio, SkipForward, X } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Article {
  title: string;
  url: string;
  source: string;
}

interface Group {
  id: string;
  name: string;
  summary: string;
  image_url: string | null;
  updated_at: string;
  audio_ready: boolean;
  articles: Article[];
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

function Modal({ group, onClose }: { group: Group; onClose: () => void }) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(9,32,35,0.85)" }}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl p-6 shadow-2xl"
        style={{ backgroundColor: "var(--dark)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-full opacity-60 hover:opacity-100 transition-opacity"
          style={{ color: "var(--cream-muted)" }}
        >
          <X size={20} />
        </button>

        {group.image_url && (
          <img
            src={group.image_url}
            alt={group.name}
            className="w-full h-48 object-cover rounded-xl mb-5"
          />
        )}

        <h2 className="text-2xl font-bold mb-4" style={{ color: "var(--cream)" }}>
          {group.name}
        </h2>

        <p className="text-sm leading-relaxed whitespace-pre-wrap mb-6" style={{ color: "var(--cream-mid)" }}>
          {group.summary}
        </p>

        <div className="border-t pt-4" style={{ borderColor: "var(--bg)" }}>
          <h3 className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--teal)" }}>
            Sources
          </h3>
          <ul className="space-y-2">
            {group.articles.map((a) => (
              <li key={a.url} className="text-sm">
                <a
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                  style={{ color: "var(--blue)" }}
                >
                  {a.title}
                </a>
                <span className="ml-2 text-xs" style={{ color: "var(--cream-muted)" }}>
                  {a.source}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NewsCard
// ---------------------------------------------------------------------------

interface NewsCardProps {
  group: Group;
  isActive: boolean;
  isPaused: boolean;
  isCached: boolean;
  progress: number;
  duration: number;
  onCardClick: (group: Group) => void;
  onExpand: (group: Group) => void;
  onSeek: (group: Group, fraction: number) => void;
}

function NewsCard({ group, isActive, isPaused, isCached, progress, duration, onCardClick, onExpand, onSeek }: NewsCardProps) {
  const excerpt = group.summary.split(/\. /).slice(0, 2).join(". ") + ".";
  const isPlaying = isActive && !isPaused;

  const elapsed   = duration > 0 ? progress * duration : 0;
  const remaining = duration > 0 ? duration - elapsed : 0;

  function statusLabel() {
    if (!isCached)  return "Preparing...";
    if (isPlaying)  return "Playing — click to pause";
    if (isActive)   return "Paused — click to resume";
    return "Click to listen";
  }

  return (
    <div
      className={`relative flex flex-col rounded-2xl overflow-hidden transition-all duration-200 ${
        isCached
          ? "cursor-pointer hover:scale-[1.02] hover:shadow-2xl hover:-translate-y-0.5"
          : "cursor-default opacity-50"
      }`}
      style={{ backgroundColor: "var(--dark)" }}
      onClick={() => isCached && onCardClick(group)}
    >
      {/* Image or gradient placeholder */}
      <div className="relative">
        {group.image_url ? (
          <div className="w-full aspect-video overflow-hidden">
            <img
              src={group.image_url}
              alt={group.name}
              className="w-full h-full object-cover"
              onError={(e) => { (e.target as HTMLImageElement).parentElement!.style.display = "none"; }}
            />
          </div>
        ) : (
          <div
            className="w-full aspect-video flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, #0d2e32 0%, #1a4a4e 50%, #0a2428 100%)",
            }}
          >
            <Radio size={40} style={{ color: "var(--teal)", opacity: 0.35 }} />
          </div>
        )}

        {/* Article count badge */}
        {group.articles.length > 0 && (
          <span
            className="absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full font-medium"
            style={{
              backgroundColor: "rgba(9,32,35,0.75)",
              color: "var(--cream-muted)",
              backdropFilter: "blur(4px)",
            }}
          >
            {group.articles.length} source{group.articles.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="flex flex-col flex-1 p-4 gap-2">
        <h2 className="text-base font-semibold leading-snug" style={{ color: "var(--cream)" }}>
          {group.name}
        </h2>

        <p className="text-xs leading-relaxed flex-1" style={{ color: "var(--cream-muted)" }}>
          {excerpt}
        </p>

        {/* Seekable progress bar */}
        <div
          className="w-full relative flex items-center"
          style={{ height: "18px", cursor: isCached ? "pointer" : "default" }}
          onClick={(e) => {
            if (!isCached) return;
            e.stopPropagation();
            const rect = e.currentTarget.getBoundingClientRect();
            onSeek(group, Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)));
          }}
        >
          {/* Track */}
          <div className="w-full rounded-full overflow-hidden" style={{ height: "4px", backgroundColor: "rgba(255,255,255,0.1)" }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${progress * 100}%`,
                backgroundColor: isPaused ? "var(--yellow)" : isActive ? "var(--teal)" : "rgba(255,255,255,0.2)",
                transition: isActive ? "width 0.25s linear" : "none",
              }}
            />
          </div>
          {/* Thumb */}
          {isActive && (
            <div
              className="absolute w-3.5 h-3.5 rounded-full shadow"
              style={{
                left: `calc(${progress * 100}% - 7px)`,
                backgroundColor: isPaused ? "var(--yellow)" : "var(--teal)",
              }}
            />
          )}
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {!isCached ? (
              <Loader2 size={14} className="spin" style={{ color: "var(--cream-muted)" }} />
            ) : isPlaying ? (
              <>
                <span className="playing-dot inline-block w-2 h-2 rounded-full" style={{ backgroundColor: "var(--teal)" }} />
                <Pause size={14} style={{ color: "var(--teal)" }} />
              </>
            ) : (
              <Play size={14} style={{ color: isActive ? "var(--yellow)" : "var(--teal)", opacity: isCached ? 1 : 0.4 }} />
            )}
            <span className="text-xs" style={{ color: isPlaying ? "var(--teal)" : isActive ? "var(--yellow)" : "var(--cream-muted)" }}>
              {statusLabel()}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {duration > 0 && (
              <span className="text-xs tabular-nums" style={{ color: "var(--cream-muted)" }}>
                {isActive ? `-${formatTime(remaining)}` : formatTime(duration)}
              </span>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onExpand(group); }}
              className="p-1 rounded-lg opacity-50 hover:opacity-100 transition-opacity"
              style={{ color: "var(--cream-muted)" }}
              title="Read full summary"
            >
              <Maximize2 size={14} />
            </button>
          </div>
        </div>
      </div>

      {isActive && (
        <div
          className="absolute inset-0 rounded-2xl pointer-events-none"
          style={{ boxShadow: `inset 0 0 0 2px ${isPaused ? "var(--yellow)" : "var(--teal)"}` }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// MiniPlayer
// ---------------------------------------------------------------------------

const SPEEDS = [0.75, 1, 1.25, 1.5, 2] as const;

interface MiniPlayerProps {
  group: Group;
  isPaused: boolean;
  progress: number;
  duration: number;
  speed: number;
  hasNext: boolean;
  onPlayPause: () => void;
  onSeek: (fraction: number) => void;
  onSpeedChange: (s: number) => void;
  onSkipNext: () => void;
}

function MiniPlayer({
  group, isPaused, progress, duration, speed, hasNext,
  onPlayPause, onSeek, onSpeedChange, onSkipNext,
}: MiniPlayerProps) {
  const elapsed   = duration > 0 ? progress * duration : 0;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 px-4 py-3"
      style={{
        backgroundColor: "rgba(13,42,46,0.95)",
        backdropFilter: "blur(12px)",
        borderTop: "1px solid var(--dark)",
      }}
    >
      <div className="flex items-center gap-4 px-6 md:px-12">
        {/* Thumbnail */}
        <div className="shrink-0 w-10 h-10 rounded-lg overflow-hidden" style={{ backgroundColor: "var(--bg)" }}>
          {group.image_url ? (
            <img src={group.image_url} alt={group.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Radio size={18} style={{ color: "var(--teal)", opacity: 0.5 }} />
            </div>
          )}
        </div>

        {/* Title + seek bar */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: "var(--cream)" }}>
            {group.name}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <div
              className="flex-1 relative flex items-center cursor-pointer"
              style={{ height: "14px" }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                onSeek(Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)));
              }}
            >
              <div className="w-full rounded-full overflow-hidden" style={{ height: "3px", backgroundColor: "rgba(255,255,255,0.15)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${progress * 100}%`,
                    backgroundColor: isPaused ? "var(--yellow)" : "var(--teal)",
                    transition: !isPaused ? "width 0.25s linear" : "none",
                  }}
                />
              </div>
            </div>
            {duration > 0 && (
              <span className="text-xs tabular-nums shrink-0" style={{ color: "var(--cream-muted)" }}>
                {formatTime(elapsed)} / {formatTime(duration)}
              </span>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Speed selector */}
          <div className="hidden sm:flex items-center rounded-lg overflow-hidden" style={{ backgroundColor: "var(--bg)" }}>
            {SPEEDS.map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange(s)}
                className="px-2 py-1 text-xs transition-colors"
                style={{
                  color: speed === s ? "var(--bg)" : "var(--cream-muted)",
                  backgroundColor: speed === s ? "var(--teal)" : "transparent",
                  fontWeight: speed === s ? 600 : 400,
                }}
              >
                {s}×
              </button>
            ))}
          </div>

          {/* Play / Pause */}
          <button
            onClick={onPlayPause}
            className="w-9 h-9 rounded-full flex items-center justify-center transition-opacity hover:opacity-80"
            style={{ backgroundColor: "var(--teal)", color: "var(--bg)" }}
          >
            {isPaused ? <Play size={16} fill="currentColor" /> : <Pause size={16} fill="currentColor" />}
          </button>

          {/* Skip next */}
          <button
            onClick={onSkipNext}
            disabled={!hasNext}
            className="transition-opacity hover:opacity-80 disabled:opacity-30"
            style={{ color: "var(--cream-muted)" }}
            title="Play next story"
          >
            <SkipForward size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function Page() {
  const [groups, setGroups]             = useState<Group[]>([]);
  const [playingId, setPlayingId]       = useState<string | null>(null);
  const [isPaused, setIsPaused]         = useState(false);
  const [progressMap, setProgressMap]   = useState<Record<string, number>>({});
  const [durations, setDurations]       = useState<Record<string, number>>({});
  const [cachedIds, setCachedIds]       = useState<Set<string>>(new Set());
  const [expandedGroup, setExpanded]    = useState<Group | null>(null);
  const [error, setError]               = useState<string | null>(null);
  const [readyCount, setReadyCount]     = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [speed, setSpeed]               = useState<number>(1);

  const audioObjects  = useRef<Record<string, HTMLAudioElement>>({});
  const cacheVersion  = useRef<Record<string, string>>({});
  const prefetchAbort = useRef<AbortController | null>(null);
  // Refs so onended callbacks always see fresh state without stale closures
  const groupsRef    = useRef<Group[]>([]);
  const cachedIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => { groupsRef.current = groups; }, [groups]);
  useEffect(() => { cachedIdsRef.current = cachedIds; }, [cachedIds]);

  // Apply playback rate to all cached audio when speed changes
  useEffect(() => {
    Object.values(audioObjects.current).forEach((a) => { a.playbackRate = speed; });
  }, [speed]);

  // Keyboard shortcuts: Space = play/pause, ←/→ = seek ±10 s
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === "INPUT") return;
      if (!playingId) return;
      const audio = audioObjects.current[playingId];
      if (!audio) return;

      if (e.key === " ") {
        e.preventDefault();
        if (isPaused) { audio.play(); setIsPaused(false); }
        else          { audio.pause(); setIsPaused(true); }
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        audio.currentTime = Math.min(audio.duration, audio.currentTime + 10);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        audio.currentTime = Math.max(0, audio.currentTime - 10);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [playingId, isPaused]);

  useEffect(() => { fetchGroups(); }, []);

  async function handleRefresh() {
    setIsRefreshing(true);
    try {
      await fetch(`${API_URL}/refresh`, { method: "POST" });
    } catch (e) {
      console.error("Refresh failed:", e);
    } finally {
      setIsRefreshing(false);
    }
    await fetchGroups();
  }

  async function fetchGroups() {
    try {
      const res = await fetch(`${API_URL}/news`);
      if (!res.ok) throw new Error(`Backend returned ${res.status}`);
      const data: Group[] = await res.json();
      setGroups(data);
      setError(null);

      const staleIds = data
        .filter((g) => cacheVersion.current[g.id] && cacheVersion.current[g.id] !== g.updated_at)
        .map((g) => g.id);
      if (staleIds.length > 0) {
        staleIds.forEach((id) => {
          audioObjects.current[id]?.pause();
          delete audioObjects.current[id];
          delete cacheVersion.current[id];
        });
        setCachedIds((prev) => { const n = new Set(prev); staleIds.forEach((id) => n.delete(id)); return n; });
        setProgressMap((prev) => { const n = { ...prev }; staleIds.forEach((id) => delete n[id]); return n; });
        setDurations((prev)   => { const n = { ...prev }; staleIds.forEach((id) => delete n[id]); return n; });
      }

      prefetchAudio(data);
    } catch (e) {
      setError("Could not reach backend. Is it running on port 8000?");
      console.error(e);
    }
  }

  async function prefetchAudio(groupList: Group[]) {
    prefetchAbort.current?.abort();
    const controller = new AbortController();
    prefetchAbort.current = controller;

    setReadyCount(Object.keys(audioObjects.current).length);

    await Promise.allSettled(
      groupList.filter((g) => g.audio_ready).map(async (group) => {
        if (audioObjects.current[group.id]) return;
        try {
          const res = await fetch(`${API_URL}/audio/${group.id}`, { signal: controller.signal });
          if (!res.ok) return;

          const blob  = await res.blob();
          const url   = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.playbackRate = speed;

          audio.onloadedmetadata = () => {
            setDurations((prev) => ({ ...prev, [group.id]: audio.duration }));
          };

          audio.ontimeupdate = () => {
            if (audio.duration) {
              setProgressMap((prev) => ({ ...prev, [group.id]: audio.currentTime / audio.duration }));
            }
          };

          // Auto-play next cached story when this one finishes
          audio.onended = () => {
            const currentGroups = groupsRef.current;
            const currentCached = cachedIdsRef.current;
            const idx  = currentGroups.findIndex((g) => g.id === group.id);
            const next = currentGroups.slice(idx + 1).find((g) => currentCached.has(g.id));

            setProgressMap((prev) => ({ ...prev, [group.id]: 0 }));
            audio.currentTime = 0;

            if (next) {
              const nextAudio = audioObjects.current[next.id];
              if (nextAudio) {
                nextAudio.playbackRate = nextAudio.playbackRate; // already set
                setPlayingId(next.id);
                setIsPaused(false);
                nextAudio.play();
              }
            } else {
              setPlayingId(null);
              setIsPaused(false);
            }
          };

          audioObjects.current[group.id] = audio;
          cacheVersion.current[group.id] = group.updated_at;
          setCachedIds((prev) => new Set([...prev, group.id]));
          setReadyCount(Object.keys(audioObjects.current).length);
        } catch (e: unknown) {
          if ((e as Error)?.name !== "AbortError") {
            console.error(`Prefetch failed for ${group.id}:`, e);
          }
        }
      })
    );
  }

  const handleCardClick = useCallback((group: Group) => {
    const audio = audioObjects.current[group.id];
    if (!audio) return;

    if (playingId === group.id) {
      if (isPaused) { audio.play(); setIsPaused(false); }
      else          { audio.pause(); setIsPaused(true); }
      return;
    }

    if (playingId) audioObjects.current[playingId]?.pause();
    setIsPaused(false);
    audio.playbackRate = speed;
    audio.play();
    setPlayingId(group.id);
  }, [playingId, isPaused, speed]);

  const handleSeek = useCallback((group: Group, fraction: number) => {
    const audio = audioObjects.current[group.id];
    if (!audio || !audio.duration) return;
    audio.currentTime = fraction * audio.duration;
    setProgressMap((prev) => ({ ...prev, [group.id]: fraction }));
  }, []);

  const handleMiniSeek = useCallback((fraction: number) => {
    if (!playingId) return;
    const audio = audioObjects.current[playingId];
    if (!audio || !audio.duration) return;
    audio.currentTime = fraction * audio.duration;
    setProgressMap((prev) => ({ ...prev, [playingId]: fraction }));
  }, [playingId]);

  const handleSkipNext = useCallback(() => {
    if (!playingId) return;
    const idx  = groups.findIndex((g) => g.id === playingId);
    const next = groups.slice(idx + 1).find((g) => cachedIds.has(g.id));
    if (next) handleCardClick(next);
  }, [playingId, groups, cachedIds, handleCardClick]);

  const handleSpeedChange = useCallback((s: number) => {
    setSpeed(s);
    Object.values(audioObjects.current).forEach((a) => { a.playbackRate = s; });
  }, []);

  const playingGroup = playingId ? groups.find((g) => g.id === playingId) ?? null : null;
  const total = groups.length;
  const hasNext = playingId
    ? !!groups.slice(groups.findIndex((g) => g.id === playingId) + 1).find((g) => cachedIds.has(g.id))
    : false;

  return (
    <div className={`min-h-screen px-6 md:px-12 ${playingGroup ? "pb-24" : "pb-8"}`}>
      {/* Sticky header */}
      <header
        className="sticky top-0 z-40 -mx-6 md:-mx-12 px-6 md:px-12 py-4 mb-10 relative flex items-center justify-center"
        style={{
          backgroundColor: "rgba(9,32,35,0.92)",
          backdropFilter: "blur(10px)",
          borderBottom: "1px solid var(--dark)",
        }}
      >
        {/* Centered title */}
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-2">
            <Radio size={24} style={{ color: "var(--teal)" }} />
            <h1 className="text-2xl font-bold tracking-tight leading-none" style={{ color: "var(--teal)" }}>
              News Aggregator
            </h1>
          </div>
          <p className="text-xs" style={{ color: "var(--cream-muted)" }}>
            Catch summaries of latest major news across the world
          </p>
        </div>

        {/* Refresh pinned to top-right */}
        <div className="absolute right-6 md:right-12 flex items-center gap-3">
          {total > 0 && (
            <span className="text-xs hidden sm:inline">
              {readyCount < total ? (
                <span style={{ color: "var(--yellow)" }}>Preparing {readyCount}/{total}…</span>
              ) : (
                <span style={{ color: "var(--teal)" }}>{total} ready</span>
              )}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="text-xs px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80 disabled:opacity-40"
            style={{ backgroundColor: "var(--dark)", color: "var(--cream-mid)" }}
          >
            {isRefreshing ? "Fetching…" : "Refresh"}
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto">
        {error && (
          <div className="mb-6 rounded-xl px-4 py-3 text-sm" style={{ backgroundColor: "#3b1212", color: "var(--coral)" }}>
            {error}
          </div>
        )}

        {groups.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <Loader2 size={36} className="spin" style={{ color: "var(--teal)" }} />
            <p className="text-sm" style={{ color: "var(--cream-muted)" }}>
              Waiting for first sync — the backend fetches news on startup.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-x-14 lg:gap-y-10">
          {groups.map((group) => (
            <NewsCard
              key={group.id}
              group={group}
              isActive={playingId === group.id}
              isPaused={playingId === group.id && isPaused}
              isCached={cachedIds.has(group.id)}
              progress={progressMap[group.id] ?? 0}
              duration={durations[group.id] ?? 0}
              onCardClick={handleCardClick}
              onExpand={setExpanded}
              onSeek={handleSeek}
            />
          ))}
        </div>
      </div>

      {expandedGroup && (
        <Modal group={expandedGroup} onClose={() => setExpanded(null)} />
      )}

      {playingGroup && (
        <MiniPlayer
          group={playingGroup}
          isPaused={isPaused}
          progress={progressMap[playingGroup.id] ?? 0}
          duration={durations[playingGroup.id] ?? 0}
          speed={speed}
          hasNext={hasNext}
          onPlayPause={() => handleCardClick(playingGroup)}
          onSeek={handleMiniSeek}
          onSpeedChange={handleSpeedChange}
          onSkipNext={handleSkipNext}
        />
      )}
    </div>
  );
}
