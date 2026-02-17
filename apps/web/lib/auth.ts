import { ClientUser } from "@/lib/types";

const USER_KEY = "aas_user";

export function getClientUser(): ClientUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as ClientUser;
  } catch {
    return null;
  }
}

export function saveClientUser(handle: string): ClientUser {
  const user = {
    id: crypto.randomUUID(),
    handle,
  };
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  return user;
}

export function clearClientUser(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(USER_KEY);
}
