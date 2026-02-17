"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { clearClientUser, getClientUser } from "@/lib/auth";
import { api } from "@/lib/api";
import { ArgumentControls, ClientUser, MyArgumentsResponse } from "@/lib/types";

const DEFAULT_CONTROLS: ArgumentControls = {
  argument_composure: 42,
  argument_shape: "QUICK_SKIRMISH",
  win_condition: "EXPOSE_WEAK_POINTS",
  guardrails: {
    no_personal_attacks: true,
    no_moral_absolutism: false,
    no_hypotheticals: false,
    steelman_before_rebuttal: false,
    stay_on_topic: true,
  },
  audience_mode: true,
  pace_mode: "NORMAL",
  evidence_mode: "FREEFORM",
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<ClientUser | null>(null);
  const [data, setData] = useState<MyArgumentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [topic, setTopic] = useState("");
  const [controls, setControls] = useState<ArgumentControls>(DEFAULT_CONTROLS);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [spectatorUrl, setSpectatorUrl] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const creditsLabel = useMemo(() => {
    const credits = data?.credits_balance ?? 0;
    return `${credits} start${credits === 1 ? "" : "s"} left`;
  }, [data?.credits_balance]);

  useEffect(() => {
    const currentUser = getClientUser();
    if (!currentUser) {
      router.replace("/login");
      return;
    }
    setUser(currentUser);
  }, [router]);

  useEffect(() => {
    if (!user) {
      return;
    }
    api
      .myArguments(user)
      .then((res) => setData(res))
      .catch((err: Error) => setError(err.message));
  }, [user]);

  const onCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!user) {
      return;
    }

    setError(null);
    setIsCreating(true);
    try {
      const created = await api.createArgument(user, topic, controls);
      const participantInvite = await api.createInvite(user, created.id, "participant");
      const viewerInvite = await api.createInvite(user, created.id, "spectator");
      setInviteUrl(participantInvite.url);
      setSpectatorUrl(viewerInvite.url);
      setTopic("");
      setData(await api.myArguments(user));
      router.push(`/arguments/${created.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsCreating(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] opacity-60">AaS Dashboard</p>
          <h1 className="text-3xl font-bold">Welcome, @{user.handle}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full border border-[#d2d8d5] bg-white px-4 py-2 text-sm">{creditsLabel}</span>
          <button
            className="rounded-xl border border-[#d2d8d5] bg-white px-4 py-2 text-sm"
            onClick={() => {
              clearClientUser();
              router.replace("/login");
            }}
          >
            Logout
          </button>
        </div>
      </header>

      <section className="tilt-card surface mb-8 rounded-3xl p-6">
        <h2 className="mb-4 text-2xl font-bold">Create New Argument</h2>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={onCreate}>
          <label className="md:col-span-2">
            <span className="mb-1 block text-sm font-medium">Topic</span>
            <input
              className="w-full rounded-xl border border-[#d6ddda] bg-white px-4 py-3"
              placeholder="Ex: Is remote work killing creativity?"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              required
              minLength={5}
            />
          </label>

          <label>
            <span className="mb-1 block text-sm font-medium">Composure ({controls.argument_composure})</span>
            <input
              type="range"
              min={0}
              max={100}
              value={controls.argument_composure}
              onChange={(event) =>
                setControls((prev) => ({ ...prev, argument_composure: Number(event.target.value) }))
              }
              className="w-full"
            />
          </label>

          <label>
            <span className="mb-1 block text-sm font-medium">Shape</span>
            <select
              className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
              value={controls.argument_shape}
              onChange={(event) =>
                setControls((prev) => ({
                  ...prev,
                  argument_shape: event.target.value as ArgumentControls["argument_shape"],
                }))
              }
            >
              <option value="QUICK_SKIRMISH">Quick Skirmish</option>
              <option value="PROPER_THROWDOWN">Proper Throwdown</option>
              <option value="SLOW_BURN">Slow Burn</option>
            </select>
          </label>

          <label>
            <span className="mb-1 block text-sm font-medium">Win Condition</span>
            <select
              className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
              value={controls.win_condition}
              onChange={(event) =>
                setControls((prev) => ({
                  ...prev,
                  win_condition: event.target.value as ArgumentControls["win_condition"],
                }))
              }
            >
              <option value="BE_RIGHT">Be right</option>
              <option value="FIND_OVERLAP">Find overlap</option>
              <option value="EXPOSE_WEAK_POINTS">Expose weak points</option>
              <option value="UNDERSTAND_OTHER_SIDE">Understand other side</option>
            </select>
          </label>

          <label>
            <span className="mb-1 block text-sm font-medium">Pace</span>
            <select
              className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
              value={controls.pace_mode}
              onChange={(event) =>
                setControls((prev) => ({ ...prev, pace_mode: event.target.value as ArgumentControls["pace_mode"] }))
              }
            >
              <option value="FAST">Fast</option>
              <option value="NORMAL">Normal</option>
              <option value="DRAMATIC">Dramatic</option>
            </select>
          </label>

          <label>
            <span className="mb-1 block text-sm font-medium">Evidence</span>
            <select
              className="w-full rounded-xl border border-[#d6ddda] bg-white px-3 py-2"
              value={controls.evidence_mode}
              onChange={(event) =>
                setControls((prev) => ({
                  ...prev,
                  evidence_mode: event.target.value as ArgumentControls["evidence_mode"],
                }))
              }
            >
              <option value="FREEFORM">Freeform</option>
              <option value="RECEIPTS_PREFERRED">Receipts preferred</option>
            </select>
          </label>

          <label className="md:col-span-2 flex items-center gap-2 rounded-xl border border-[#d6ddda] bg-white px-4 py-3">
            <input
              type="checkbox"
              checked={controls.audience_mode}
              onChange={(event) =>
                setControls((prev) => ({ ...prev, audience_mode: event.target.checked }))
              }
            />
            Audience mode (spectator reactions + public replay)
          </label>

          <button
            type="submit"
            disabled={isCreating}
            className="md:col-span-2 rounded-xl bg-[#1f2a26] px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            {isCreating ? "Launching..." : "Launch Argument"}
          </button>
        </form>

        {inviteUrl ? (
          <div className="mt-4 rounded-xl border border-[#d6ddda] bg-white p-4 text-sm">
            <p>
              Participant invite: <a className="underline" href={inviteUrl}>{inviteUrl}</a>
            </p>
            <p>
              Spectator invite: <a className="underline" href={spectatorUrl ?? "#"}>{spectatorUrl}</a>
            </p>
          </div>
        ) : null}
      </section>

      {error ? <p className="mb-6 rounded-xl bg-[#fff0ed] p-3 text-[#9d2f18]">{error}</p> : null}

      <section className="grid gap-6 md:grid-cols-2">
        <div className="tilt-card surface rounded-2xl p-5">
          <h3 className="mb-3 text-xl font-bold">Active Arguments</h3>
          <div className="space-y-3">
            {data?.active.length ? (
              data.active.map((item) => (
                <Link key={item.id} href={`/arguments/${item.id}`} className="block rounded-xl border border-[#d6ddda] bg-white p-3">
                  <p className="font-medium">{item.topic}</p>
                  <p className="text-sm opacity-65">{item.status} · {item.phase}</p>
                </Link>
              ))
            ) : (
              <p className="text-sm opacity-65">Nothing active yet.</p>
            )}
          </div>
        </div>

        <div className="tilt-card surface rounded-2xl p-5">
          <h3 className="mb-3 text-xl font-bold">Past Arguments</h3>
          <div className="space-y-3">
            {data?.past.length ? (
              data.past.map((item) => (
                <Link key={item.id} href={`/arguments/${item.id}`} className="block rounded-xl border border-[#d6ddda] bg-white p-3">
                  <p className="font-medium">{item.topic}</p>
                  <p className="text-sm opacity-65">{item.status}</p>
                </Link>
              ))
            ) : (
              <p className="text-sm opacity-65">No completed battles yet.</p>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
