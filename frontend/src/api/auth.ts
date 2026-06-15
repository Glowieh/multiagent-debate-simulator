const ACCESS_TOKEN_KEY = "debate_access_token";

export function isAuthRequired(): boolean {
  if (import.meta.env.DEV) {
    return false;
  }
  return import.meta.env.VITE_SKIP_AUTH !== "true";
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
}

export async function login(password: string): Promise<void> {
  const { resolveApiUrl } = await import("./config");
  const response = await fetch(resolveApiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Invalid credentials");
    }
    throw new Error(`Login failed: ${response.status}`);
  }

  const data = (await response.json()) as { accessToken?: string };
  if (!data.accessToken) {
    throw new Error("Login response missing accessToken");
  }
  setAccessToken(data.accessToken);
}
