"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getClientUser } from "@/lib/auth";
import { api } from "@/lib/api";
import { ArgumentView, ClientUser, TurnView, WrappedReport } from "@/lib/types";

type DraftTurn = {
  speaker_participant_id: string;
  content: string;
};

export default function ArgumentPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();

  const argumentId = params.id;
  const audienceToken = searchParams.get("audienceToken") ?? "";

  const [user, setUser] = useState<ClientUser | null>(null);
  const [argument, setArgument] = useState<ArgumentView | null>(null);
  const [turns, setTurns] = useState<TurnView[]>([]);
  const [drafts, setDrafts] = useState<Record<number, DraftTurn>>({});
  const [badges, setBadges] = useState<Record<number, Array<{ badge_key: string; reason: string }>>>({});
  const [reactions, setReactions] = useState<Array<{ emoji: string; turn_index: number | null }>>([]);
  const [phaseHint, setPhaseHint] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [participantInvite, setParticipantInvite] = useState<string | null>(null);
  const [spectatorInvite, setSpectatorInvite] = useState<string | null>(null);

  const [stance, setStance] = useState("");
  const [points, setPoints] = useState(["", "", ""]);
  const [redLines, setRedLines] = useState("");

  const [report, setReport] = useState<WrappedReport | null>(null);
  const [reportSummary, setReportSummary] = useState<string>("");

  const participantMap = useMemo(() => {
    const map = new Map<string, number>();
    argument?.participants.forEach((participant) => map.set(participant.id, participant.seat_order));
    return map;
  }, [argument]);

  const myParticipant = useMemo(() => {
    if (!user || !argument) {
      return null;
    }
    return argument.participants.find((participant) => participant.user_id === user.id) ?? null;
  }, [argument, user]);

  useEffect(() => {
    const current = getClientUser();
    if (!current) {
      if (audienceToken) {
        setUser({ id: `guest-${crypto.randomUUID()}`, handle: "spectator" });
        return;
      }
      router.replace("/login");
      return;
    }
    setUser(current);
  }, [audienceToken, router]);

  useEffect(() => {
    if (!user) {
      return;
    }

    const load = async () => {
      try {
        const [argumentView, turnBundle] = await Promise.all([
          api.getArgument(user, argumentId, audienceToken || undefined),
          api.turns(user, argumentId, audienceToken || undefined),
        ]);

        setArgument(argumentView);
        setTurns(turnBundle.turns);

        const mine = argumentView.participants.find((participant) => participant.user_id === user.id);
        if (mine?.persona_snapshot) {
          setStance(mine.persona_snapshot.stance);
          setPoints(mine.persona_snapshot.defend_points.slice(0, 3));
          setRedLines((mine.persona_snapshot.red_lines ?? []).join(", "));
        }

        if (argumentView.status === "completed") {
          try {
            const reportResponse = await api.report(user, argumentId, audienceToken || undefined);
            setReport(reportResponse.report);
            setReportSummary(reportResponse.summary);
          } catch {
            // Report may still be processing.
          }
        }
      } catch (err) {
        setError((err as Error).message);
      }
    };

    void load();
  }, [argumentId, audienceToken, user]);

  useEffect(() => {
    if (!user) {
      return;
    }

    const wsBase = api.apiUrl.replace(/^http/, "ws");
    const wsUrl = `${wsBase}/v1/arguments/${argumentId}/stream?userId=${encodeURIComponent(user.id)}${
      audienceToken ? `&audienceToken=${encodeURIComponent(audienceToken)}` : ""
    }`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = async (message) => {
      try {
        const event = JSON.parse(message.data) as {
          event_type: string;
          payload: Record<string, unknown>;
          turn_index: number | null;
        };

        if (event.event_type === "turn.token") {
          const turnIndex = Number(event.turn_index ?? 0);
          const speaker = String(event.payload.speaker_participant_id ?? "");
          const token = String(event.payload.token ?? "");
          setDrafts((prev) => {
            const current = prev[turnIndex] ?? { speaker_participant_id: speaker, content: "" };
            return {
              ...prev,
              [turnIndex]: {
                speaker_participant_id: current.speaker_participant_id || speaker,
                content: `${current.content}${token}`,
              },
            };
          });
          return;
        }

        if (event.event_type === "turn.final") {
          const turnIndex = Number(event.turn_index ?? 0);
          const speaker = String(event.payload.speaker_participant_id ?? "");
          const content = String(event.payload.content ?? "");
          const phase = String(event.payload.phase ?? "opening") as TurnView["phase"];

          setTurns((prev) => {
            const existing = prev.find((item) => item.turn_index === turnIndex);
            if (existing) {
              return prev.map((item) =>
                item.turn_index === turnIndex
                  ? { ...item, content, speaker_participant_id: speaker, phase }
                  : item,
              );
            }
            const next = [
              ...prev,
              {
                id: `live-${turnIndex}`,
                turn_index: turnIndex,
                speaker_participant_id: speaker,
                phase,
                content,
                metrics: {},
                model_metadata: {},
                created_at: new Date().toISOString(),
              },
            ];
            next.sort((a, b) => a.turn_index - b.turn_index);
            return next;
          });

          setDrafts((prev) => {
            const next = { ...prev };
            delete next[turnIndex];
            return next;
          });
          return;
        }

        if (event.event_type === "badge.awarded") {
          const turnIndex = Number(event.turn_index ?? 0);
          const badgeKey = String(event.payload.badge_key ?? "badge");
          const reason = String(event.payload.reason ?? "");
          setBadges((prev) => ({
            ...prev,
            [turnIndex]: [...(prev[turnIndex] ?? []), { badge_key: badgeKey, reason }],
          }));
          return;
        }

        if (event.event_type === "phase.changed") {
          setPhaseHint(String(event.payload.phase ?? ""));
          setArgument((prev) => (prev ? { ...prev, phase: String(event.payload.phase ?? prev.phase) as ArgumentView["phase"] } : prev));
          return;
        }

        if (event.event_type === "turn.meta") {
          const state = String(event.payload.state ?? "");
          if (state) {
            setStatusMessage(state);
          }
          return;
        }

        if (event.event_type === "argument.completed") {
          setArgument((prev) => (prev ? { ...prev, status: "completed" } : prev));
          try {
            const reportResponse = await api.report(user, argumentId, audienceToken || undefined);
            setReport(reportResponse.report);
            setReportSummary(reportResponse.summary);
          } catch {
            // no-op
          }
          return;
        }

        if (event.event_type === "reaction.added") {
          const emoji = String(event.payload.emoji ?? "🔥");
          const turnIndex = event.payload.turn_index ? Number(event.payload.turn_index) : null;
          setReactions((prev) => [{ emoji, turn_index: turnIndex }, ...prev].slice(0, 12));
        }
      } catch {
        // ignore malformed event
      }
    };

    ws.onerror = () => {
      setStatusMessage("live stream disconnected; refresh to retry");
    };

    return () => {
      ws.close();
    };
  }, [argumentId, audienceToken, user]);

  const onSavePersona = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!user) {
      return;
    }
    try {
      await api.setPersona(user, argumentId, {
        stance,
        defend_points: points,
        red_lines: redLines
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setStatusMessage("persona saved");
      setArgument(await api.getArgument(user, argumentId, audienceToken || undefined));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const onReady = async () => {
    if (!user) {
      return;
    }
    try {
      await api.ready(user, argumentId);
      setStatusMessage("ready locked in");
      setArgument(await api.getArgument(user, argumentId, audienceToken || undefined));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const onStart = async () => {
    if (!user) {
      return;
    }
    try {
      await api.start(user, argumentId);
      setStatusMessage("argument is starting...");
      setArgument(await api.getArgument(user, argumentId, audienceToken || undefined));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const onCreateInvite = async (role: "participant" | "spectator") => {
    if (!user || !argument) {
      return;
    }
    try {
      const invite = await api.createInvite(user, argument.id, role);
      if (role === "participant") {
        setParticipantInvite(invite.url);
      } else {
        setSpectatorInvite(invite.url);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const onReact = async (emoji: string) => {
    if (!user || !argument || !argument.audience_mode) {
      return;
    }
    try {
      await api.react(user, argument.id, { emoji }, audienceToken || undefined);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const renderBubble = (speakerParticipantId: string, content: string, turnIndex: number, isDraft = false) => {
    const side = (participantMap.get(speakerParticipantId) ?? 0) % 2 === 0 ? "right" : "left";
    const bubbleClass = side === "right" ? "chat-bubble chat-right ml-auto" : "chat-bubble chat-left";

    return (
      <div key={`${isDraft ? "draft" : "final"}-${turnIndex}`} className="mb-3">
        <div className={`flex ${side === "right" ? "justify-end" : "justify-start"}`}>
          <div className={bubbleClass}>
            <p className="mb-1 text-xs uppercase opacity-70">
              {speakerParticipantId.slice(0, 8)} · turn {turnIndex} {isDraft ? "(typing...)" : ""}
            </p>
            <p>{content}</p>
          </div>
        </div>
        {(badges[turnIndex] ?? []).length > 0 ? (
          <div className="mt-1 flex flex-wrap justify-end gap-2">
            {badges[turnIndex].map((badge, index) => (
              <span key={`${badge.badge_key}-${index}`} className="badge-chip">
                {badge.badge_key}: {badge.reason}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    );
  };

  if (!user) {
    return null;
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-6">
      <div className="mb-4 flex items-center justify-between">
        <button className="rounded-xl border border-[#d8dfdc] bg-white px-3 py-2 text-sm" onClick={() => router.push("/app")}>Back</button>
        <div className="rounded-xl bg-white px-4 py-2 text-sm">Live phase: {phaseHint || argument?.phase || "opening"}</div>
      </div>

      {error ? <p className="mb-4 rounded-xl bg-[#fff0ed] p-3 text-[#9d2f18]">{error}</p> : null}
      {statusMessage ? <p className="mb-4 rounded-xl bg-[#eef9f4] p-3 text-[#1f5f3d]">{statusMessage}</p> : null}

      <section className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <div className="tilt-card surface rounded-2xl p-4">
            <h1 className="mb-2 text-2xl font-bold">{argument?.topic ?? "Loading..."}</h1>
            <p className="text-sm opacity-70">Status: {argument?.status ?? "..."}</p>
            <p className="text-sm opacity-70">Participants ready: {argument?.participants.filter((p) => p.ready).length ?? 0}</p>
          </div>

          {argument && argument.creator_user_id === user.id ? (
            <div className="tilt-card surface rounded-2xl p-4">
              <p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] opacity-70">Invite Controls</p>
              <div className="flex gap-2">
                <button className="rounded-xl border border-[#d6ddda] bg-white px-3 py-2 text-sm" onClick={() => onCreateInvite("participant")}>Participant Link</button>
                <button className="rounded-xl border border-[#d6ddda] bg-white px-3 py-2 text-sm" onClick={() => onCreateInvite("spectator")}>Spectator Link</button>
              </div>
              {participantInvite ? <p className="mt-2 break-all text-xs">P: {participantInvite}</p> : null}
              {spectatorInvite ? <p className="mt-1 break-all text-xs">S: {spectatorInvite}</p> : null}
            </div>
          ) : null}

          {myParticipant && argument?.status === "waiting" ? (
            <form className="tilt-card surface space-y-3 rounded-2xl p-4" onSubmit={onSavePersona}>
              <p className="text-sm font-semibold uppercase tracking-[0.14em] opacity-70">Persona Setup</p>
              <input className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2" placeholder="My stance" value={stance} onChange={(event) => setStance(event.target.value)} required />
              {points.map((point, index) => (
                <input
                  key={index}
                  className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
                  placeholder={`Defend point ${index + 1}`}
                  value={point}
                  onChange={(event) => {
                    const next = [...points];
                    next[index] = event.target.value;
                    setPoints(next);
                  }}
                  required
                />
              ))}
              <textarea
                className="h-20 w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
                placeholder="Red lines (comma separated, optional)"
                value={redLines}
                onChange={(event) => setRedLines(event.target.value)}
              />
              <div className="flex gap-2">
                <button type="submit" className="rounded-xl border border-[#d6ddda] bg-white px-3 py-2 text-sm">Save Persona</button>
                <button type="button" className="rounded-xl bg-[#1f2a26] px-3 py-2 text-sm text-white" onClick={onReady}>Mark Ready</button>
              </div>
            </form>
          ) : null}

          {argument && argument.creator_user_id === user.id && argument.status === "waiting" ? (
            <button className="w-full rounded-xl bg-[#ff4f2a] px-3 py-3 font-semibold text-white" onClick={onStart}>
              Start Argument
            </button>
          ) : null}

          {report ? (
            <div className="tilt-card surface rounded-2xl p-4">
              <p className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] opacity-70">Wrapped</p>
              <p className="mb-2 text-sm">{reportSummary}</p>
              <p className="text-sm"><strong>Who cooked:</strong> {report.who_cooked}</p>
              <p className="text-sm"><strong>Most stubborn point:</strong> {report.most_stubborn_point}</p>
              <p className="text-sm"><strong>Common ground:</strong> {report.unexpected_common_ground}</p>
              <ul className="mt-2 space-y-1 text-sm">
                {report.highlights.map((item, idx) => (
                  <li key={idx} className="rounded-md bg-white px-2 py-1">{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>

        <section className="tilt-card surface rounded-2xl p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-xl font-bold">Live Argument Feed</h2>
            <span className="rounded-full border border-[#d8dfdc] bg-white px-3 py-1 text-xs">same UI for live + replay</span>
          </div>

          {argument?.audience_mode ? (
            <div className="mb-4 rounded-xl border border-[#d6ddda] bg-white p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.12em] opacity-70">Audience Reactions</p>
                <div className="flex gap-2">
                  {["🔥", "🧠", "💀", "👏"].map((emoji) => (
                    <button
                      key={emoji}
                      className="rounded-lg border border-[#d6ddda] px-2 py-1 text-sm"
                      onClick={() => onReact(emoji)}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                {reactions.length ? (
                  reactions.map((reaction, idx) => (
                    <span key={`${reaction.emoji}-${idx}`} className="rounded-full bg-[#f4f6f6] px-2 py-1">
                      {reaction.emoji} {reaction.turn_index ? `turn ${reaction.turn_index}` : ""}
                    </span>
                  ))
                ) : (
                  <span className="text-xs opacity-65">No reactions yet.</span>
                )}
              </div>
            </div>
          ) : null}

          <div className="max-h-[72vh] overflow-y-auto pr-2">
            {turns.map((turn) => renderBubble(turn.speaker_participant_id, turn.content, turn.turn_index, false))}
            {Object.entries(drafts)
              .sort((a, b) => Number(a[0]) - Number(b[0]))
              .map(([index, draft]) =>
                renderBubble(draft.speaker_participant_id, draft.content, Number(index), true),
              )}
            {!turns.length && Object.keys(drafts).length === 0 ? (
              <p className="rounded-xl border border-dashed border-[#d6ddda] p-4 text-sm opacity-70">
                Waiting for the first hit...
              </p>
            ) : null}
          </div>
        </section>
      </section>
    </main>
  );
}
