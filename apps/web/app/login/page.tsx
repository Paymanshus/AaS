"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { saveClientUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [handle, setHandle] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const clean = handle.trim();
    if (clean.length < 2) {
      setError("Pick a handle with at least 2 characters.");
      return;
    }
    saveClientUser(clean);
    router.push("/app");
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-lg items-center px-6">
      <div className="tilt-card surface w-full rounded-3xl p-8">
        <h1 className="mb-2 text-3xl font-bold">Sign in and start cooking</h1>
        <p className="mb-6 opacity-75">MVP login is local-only for now. Supabase auth can plug in later.</p>

        <form className="space-y-4" onSubmit={onSubmit}>
          <label className="block text-sm font-medium">Handle</label>
          <input
            className="w-full rounded-xl border border-[#d6ddda] bg-white px-4 py-3 text-base"
            placeholder="your_name"
            value={handle}
            onChange={(event) => setHandle(event.target.value)}
          />
          {error ? <p className="text-sm text-[#a82408]">{error}</p> : null}
          <button
            type="submit"
            className="w-full rounded-xl bg-[#1f2a26] px-4 py-3 font-semibold text-white"
          >
            Enter Arena
          </button>
        </form>
      </div>
    </main>
  );
}
