import { useState } from "react";
import { API_URL } from "./api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setCargando(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Credenciales incorrectas");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="border border-cyan-900/40 rounded-xl bg-black/60 backdrop-blur p-8 w-full max-w-sm">
        <div className="font-mono text-xs tracking-[0.3em] text-cyan-500 mb-2">
          ACCESO RESTRINGIDO
        </div>
        <h1 className="text-2xl font-bold text-white mb-6">
          Monitor de Conflictividad
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-mono text-xs tracking-widest text-cyan-500 mb-2">
              USUARIO
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-black border border-slate-800 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-500 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block font-mono text-xs tracking-widest text-cyan-500 mb-2">
              CONTRASEÑA
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-black border border-slate-800 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-500 focus:outline-none"
              required
            />
          </div>

          {error && (
            <div className="text-red-400 font-mono text-xs border border-red-900/50 bg-red-950/30 px-3 py-2 rounded">
              ✕ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={cargando}
            className="w-full font-mono text-xs tracking-wider border border-cyan-500 text-cyan-400 py-3 rounded hover:bg-cyan-500 hover:text-black transition-all disabled:opacity-30"
          >
            {cargando ? "► VERIFICANDO..." : "► INGRESAR"}
          </button>
        </form>
      </div>
    </div>
  );
}