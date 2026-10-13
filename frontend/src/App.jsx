import { useState, useEffect } from "react";
import Dashboard from "./dashboard"; 
import { MUNICIPIOS_CHACO } from "./municipiosChaco";

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [region, setRegion] = useState("Región 3 — Oriental");
  const [municipio, setMunicipio] = useState("Resistencia");
  const [resultado, setResultado] = useState(null);
  const [cargando, setCargando] = useState(false);

  // Estado para las alertas
  const [alertas, setAlertas] = useState({ total: 0, municipios_afectados: 0, alertas: {} });
  const [mostrarAlertas, setMostrarAlertas] = useState(true);

  // Cargar alertas cada 60 segundos
  useEffect(() => {
    const cargarAlertas = async () => {
      try {
        const res = await fetch("/api/alertas-nuevas");
        if (!res.ok) return;
        const data = await res.json();
        setAlertas(data);
      } catch (e) {
        console.error("Error cargando alertas:", e);
      }
    };
    cargarAlertas();
    const interval = setInterval(cargarAlertas, 60000);
    return () => clearInterval(interval);
  }, []);

  const buscar = async () => {
    setCargando(true);
    try {
      const res = await fetch(
        `/api/analyze?municipio=${encodeURIComponent(municipio)}&provincia=Chaco&limite=10`
      );
      const data = await res.json();
      setResultado(data);
    } catch (error) {
      console.error("Error:", error);
    }
    setCargando(false);
  };

  const colorScore = (score) => {
    if (score >= 8) return "text-red-400";
    if (score >= 6) return "text-orange-400";
    if (score >= 4) return "text-yellow-400";
    if (score >= 2) return "text-cyan-400";
    return "text-emerald-400";
  };

  return (
    <div className="min-h-screen bg-black text-slate-300 font-sans">
      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(#00d9ff 1px, transparent 1px), linear-gradient(90deg, #00d9ff 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Header global */}
      <div className="relative border-b border-cyan-900/30 bg-black/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-[1800px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-lg font-bold text-white tracking-tight">
              Monitor de Conflictividad Social{" "}
              <span className="text-cyan-400">— Chaco</span>
            </h1>
            <div className="flex gap-2">
              <button
                onClick={() => setTab("dashboard")}
                className={`font-mono text-xs tracking-wider px-3 py-1.5 border transition-all ${
                  tab === "dashboard"
                    ? "border-cyan-500 text-cyan-400 bg-cyan-500/10"
                    : "border-slate-800 text-slate-500 hover:border-slate-700"
                }`}
              >
                ► DASHBOARD
              </button>
              <button
                onClick={() => setTab("buscar")}
                className={`font-mono text-xs tracking-wider px-3 py-1.5 border transition-all ${
                  tab === "buscar"
                    ? "border-cyan-500 text-cyan-400 bg-cyan-500/10"
                    : "border-slate-800 text-slate-500 hover:border-slate-700"
                }`}
              >
                ► BÚSQUEDA
              </button>
            </div>
          </div>
          <div className="font-mono text-xs text-slate-600 tracking-wider hidden md:block">
            69 MUNICIPIOS · 7 REGIONES
          </div>
        </div>
      </div>

      {/* Banner de alertas */}
      {mostrarAlertas && alertas.total > 0 && (
        <div className="relative bg-red-950/40 border-b border-red-500/40 px-6 py-3 flex items-center justify-between">
          <div className="max-w-[1800px] mx-auto flex items-center gap-3 w-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(255,59,92,0.9)]" />
            <span className="font-mono text-xs text-red-400 tracking-wider font-bold">
              ⚠ {alertas.total} ALERTA{alertas.total > 1 ? "S" : ""} EN LAS ÚLTIMAS 24HS
            </span>
            <span className="font-mono text-xs text-slate-500">
              · {alertas.municipios_afectados} municipio{alertas.municipios_afectados > 1 ? "s" : ""} afectado{alertas.municipios_afectados > 1 ? "s" : ""}
            </span>
            <div className="ml-auto flex items-center gap-2">
              <span className="font-mono text-xs text-slate-500">
                {Object.keys(alertas.alertas || {}).slice(0, 3).join(" · ")}
              </span>
              <button
                onClick={() => setMostrarAlertas(false)}
                className="font-mono text-xs text-slate-500 hover:text-white px-2"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {tab === "dashboard" && <Dashboard />}

      {tab === "buscar" && (
        <div className="relative max-w-4xl mx-auto px-6 py-8">
          <div className="border border-cyan-900/30 rounded-xl bg-black/40 backdrop-blur p-6 mb-6">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block font-mono text-xs tracking-widest text-cyan-500 mb-2">
                  REGIÓN
                </label>
                <select
                  value={region}
                  onChange={(e) => {
                    setRegion(e.target.value);
                    setMunicipio(MUNICIPIOS_CHACO[e.target.value][0]);
                  }}
                  className="w-full bg-black border border-slate-800 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-500 focus:outline-none"
                >
                  {Object.keys(MUNICIPIOS_CHACO).map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-mono text-xs tracking-widest text-cyan-500 mb-2">
                  MUNICIPIO
                </label>
                <select
                  value={municipio}
                  onChange={(e) => setMunicipio(e.target.value)}
                  className="w-full bg-black border border-slate-800 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-500 focus:outline-none"
                >
                  {MUNICIPIOS_CHACO[region].map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
              </div>
            </div>
            <button
              onClick={buscar}
              disabled={cargando}
              className="w-full font-mono text-xs tracking-wider border border-cyan-500 text-cyan-400 py-3 rounded hover:bg-cyan-500 hover:text-black transition-all disabled:opacity-30"
            >
              {cargando ? "► ANALIZANDO..." : "► BUSCAR Y ANALIZAR"}
            </button>
          </div>

          {resultado && (
            <div>
              <div className="border border-cyan-900/30 rounded-xl bg-black/40 backdrop-blur p-5 mb-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {resultado.municipio}
                    </h2>
                    <div className="font-mono text-xs text-slate-500 mt-1">
                      {resultado.total} análisis · Chaco
                    </div>
                  </div>
                  <span className={`font-mono text-2xl font-bold ${colorScore(resultado.score_promedio || 0)}`}>
                    {resultado.score_promedio || 0}/10
                  </span>
                </div>
              </div>

              {resultado.conflictos?.map((c, i) => (
                <div
                  key={i}
                  className="border border-slate-900 rounded-lg bg-black/40 backdrop-blur p-4 mb-3"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-white text-sm pr-4">
                      {c.titulo}
                    </h3>
                    <span
                      className={`font-mono text-xs font-bold ${colorScore(c.analisis?.score || 0)}`}
                    >
                      {c.analisis?.score || 0}/10
                    </span>
                  </div>
                  <p className="text-sm text-slate-400 mb-2">
                    {c.analisis?.problematica}
                  </p>
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    <span className="font-mono text-xs text-cyan-400 border border-cyan-900/50 px-2 py-0.5 rounded">
                      {c.analisis?.categoria || "otro"}
                    </span>
                    <span className="font-mono text-xs text-slate-500 border border-slate-800 px-2 py-0.5 rounded">
                      {c.analisis?.fase || "—"}
                    </span>
                    <span className="font-mono text-xs text-slate-600">
                      {c.fuente}
                    </span>
                  </div>
                  <a
                    href={c.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block font-mono text-xs text-cyan-400 hover:text-cyan-300 mt-2"
                  >
                    ▸ VER NOTICIA
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}