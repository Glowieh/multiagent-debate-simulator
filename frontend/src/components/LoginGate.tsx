import { useState } from "react";
import type { FormEvent } from "react";
import { login } from "../api/auth";

type LoginGateProps = {
  onAuthenticated: () => void;
};

export function LoginGate({ onAuthenticated }: LoginGateProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(password);
      onAuthenticated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="app login-gate">
      <header>
        <h1>LangGraph Debate Simulator</h1>
        <p>Enter the demo password to continue.</p>
      </header>

      <form className="login-form" onSubmit={handleSubmit}>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
          disabled={isSubmitting}
        />
        <button type="submit" disabled={isSubmitting || password.length === 0}>
          {isSubmitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
    </main>
  );
}
