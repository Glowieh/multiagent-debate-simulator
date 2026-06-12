export function resolveApiUrl(path: string): string {
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";
  if (!base) {
    return path;
  }
  return `${base}${path}`;
}
