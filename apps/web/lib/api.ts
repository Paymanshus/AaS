import {
  ArgumentControls,
  ArgumentView,
  ClientUser,
  MyArgumentsResponse,
  TurnView,
  WrappedReport,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit,
  user: ClientUser,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-user-id": user.id,
      "x-user-handle": user.handle,
      ...(options.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export const api = {
  apiUrl: API_URL,

  myArguments(user: ClientUser): Promise<MyArgumentsResponse> {
    return request<MyArgumentsResponse>("/v1/me/arguments", { method: "GET" }, user);
  },

  createArgument(user: ClientUser, topic: string, controls: ArgumentControls): Promise<ArgumentView> {
    return request<ArgumentView>(
      "/v1/arguments",
      {
        method: "POST",
        body: JSON.stringify({ topic, controls }),
      },
      user,
    );
  },

  getArgument(user: ClientUser, argumentId: string, audienceToken?: string): Promise<ArgumentView> {
    const query = audienceToken ? `?audience_token=${encodeURIComponent(audienceToken)}` : "";
    return request<ArgumentView>(`/v1/arguments/${argumentId}${query}`, { method: "GET" }, user);
  },

  createInvite(user: ClientUser, argumentId: string, role: "participant" | "spectator") {
    return request<{ token: string; role: string; url: string; expires_at: string }>(
      `/v1/arguments/${argumentId}/invites`,
      {
        method: "POST",
        body: JSON.stringify({ role, expires_in_minutes: role === "participant" ? 240 : 1440 }),
      },
      user,
    );
  },

  joinArgument(user: ClientUser, argumentId: string, token: string) {
    return request<{ argument_id: string; role: string }>(
      `/v1/arguments/${argumentId}/join`,
      {
        method: "POST",
        body: JSON.stringify({ token }),
      },
      user,
    );
  },

  setPersona(
    user: ClientUser,
    argumentId: string,
    payload: { stance: string; defend_points: string[]; red_lines: string[] },
  ) {
    return request<{ ok: boolean }>(
      `/v1/arguments/${argumentId}/participants/me/persona`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
      user,
    );
  },

  ready(user: ClientUser, argumentId: string) {
    return request<{ ok: boolean }>(
      `/v1/arguments/${argumentId}/ready`,
      {
        method: "POST",
      },
      user,
    );
  },

  start(user: ClientUser, argumentId: string) {
    return request<{ argument_id: string; status: "started" | "already_started" }>(
      `/v1/arguments/${argumentId}/start`,
      {
        method: "POST",
        body: JSON.stringify({ idempotency_key: crypto.randomUUID() }),
      },
      user,
    );
  },

  turns(user: ClientUser, argumentId: string, audienceToken?: string) {
    const query = audienceToken ? `?audience_token=${encodeURIComponent(audienceToken)}` : "";
    return request<{ turns: TurnView[]; events: unknown[] }>(
      `/v1/arguments/${argumentId}/turns${query}`,
      {
        method: "GET",
      },
      user,
    );
  },

  report(user: ClientUser, argumentId: string, audienceToken?: string) {
    const query = audienceToken ? `?audience_token=${encodeURIComponent(audienceToken)}` : "";
    return request<{ argument_id: string; summary: string; report: WrappedReport; created_at: string }>(
      `/v1/arguments/${argumentId}/report${query}`,
      {
        method: "GET",
      },
      user,
    );
  },

  react(
    user: ClientUser,
    argumentId: string,
    payload: { emoji: string; turn_index?: number },
    audienceToken?: string,
  ) {
    const query = audienceToken ? `?audience_token=${encodeURIComponent(audienceToken)}` : "";
    return request<{ ok: boolean }>(
      `/v1/arguments/${argumentId}/reactions${query}`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      user,
    );
  },
};
