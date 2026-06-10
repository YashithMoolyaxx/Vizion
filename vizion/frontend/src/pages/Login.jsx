import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuthStore } from "../store/authStore";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      toast.success("Signed in");
      navigate("/");
    } catch {
      toast.error("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-panel px-4">
      <div className="w-full max-w-md">
        <div className="card p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Vizion</h1>
            <p className="text-sm text-muted mt-1">Creator analytics platform</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-muted uppercase tracking-wide">Username</label>
              <input
                className="input mt-1"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted uppercase tracking-wide">Password</label>
              <input
                type="password"
                className="input mt-1"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-muted mt-6">
            New here?{" "}
            <Link to="/register" className="text-ink font-medium underline underline-offset-2">
              Create account
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-muted mt-4">
          Secured with JWT access tokens, HttpOnly refresh cookies, and server sessions.
        </p>
        <p className="text-center text-xs text-muted mt-1">Demo: alex_creator / demo1234</p>
      </div>
    </div>
  );
}
