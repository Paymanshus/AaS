"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { getClientUser } from "@/lib/auth";
import { api } from "@/lib/api";

export default function JoinPage() {
  const router = useRouter();
  const params = useParams<{ argumentId: string }>();
  const searchParams = useSearchParams();

  const argumentId = params.argumentId;
  const inviteToken = searchParams.get("token") ?? "";

  const [status, setStatus] = useState("Joining argument...");

  useEffect(() => {
    const user = getClientUser();
    if (!user) {
      router.replace("/login");
      return;
    }

    if (!inviteToken) {
      setStatus("Missing invite token.");
      return;
    }

    api
      .joinArgument(user, argumentId, inviteToken)
      .then(() => {
        setStatus("Joined. Redirecting...");
        router.replace(`/arguments/${argumentId}`);
      })
      .catch((err: Error) => setStatus(err.message));
  }, [argumentId, inviteToken, router]);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
      <div className="tilt-card surface rounded-2xl p-6 text-center">
        <h1 className="mb-2 text-2xl font-bold">Invite Gateway</h1>
        <p>{status}</p>
      </div>
    </main>
  );
}
