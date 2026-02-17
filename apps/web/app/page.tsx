import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center px-6 py-12">
      <div className="tilt-card surface w-full rounded-3xl p-10 text-center">
        <p className="mb-4 inline-block rounded-full border border-[#ffd2c3] bg-[#fff3ef] px-4 py-1 text-xs uppercase tracking-[0.25em]">
          Argument as a Service
        </p>
        <h1 className="mb-4 text-5xl font-bold leading-tight sm:text-6xl">
          Stop arguing.
          <br />
          <span className="text-[#ff4f2a]">Delegate the chaos.</span>
        </h1>
        <p className="mx-auto mb-8 max-w-xl text-lg opacity-80">
          Set your stance, invite the other side, and watch agents go turn-by-turn live.
        </p>
        <Link
          href="/app"
          className="inline-flex items-center justify-center rounded-2xl bg-[#1f2a26] px-8 py-4 text-lg font-semibold text-white transition hover:translate-y-[-2px]"
        >
          Start an Argument
        </Link>
      </div>
    </main>
  );
}
