import { useState, useEffect } from "react";
import { MUNICIPIOS_CHACO } from "./municipiosChaco";
//port "leaflet.heat";
const NIVELES = {
  critico: { label: "CRÍTICO", color: "#ff3b5c", bg: "rgba(255,59,92,0.08)", border: "rgba(255,59,92,0.4)" },
  alto: { label: "ALTO", color: "#ff8c42", bg: "rgba(255,140,66,0.08)", border: "rgba(255,140,66,0.4)" },
  medio: { label: "MEDIO", color: "#ffd93d", bg: "rgba(255,217,61,0.08)", border: "rgba(255,217,61,0.4)" },
  bajo: { label: "BAJO", color: "#00d9ff", bg: "rgba(0,217,255,0.08)", border: "rgba(0,217,255,0.4)" },
  sin_datos: { label: "SIN DATOS", color: "#4a5568", bg: "rgba(74,85,104,0.05)", border: "rgba(74,85,104,0.3)" },
};

const CATEGORIA_META = {
  laboral: { icon: "⚡", label: "LABORAL", color: "#ffd93d" },
  servicios: { icon: "🔌", label: "SERVICIOS", color: "#ff8c42" },
  clima: { icon: "🌊", label: "CLIMA", color: "#00d9ff" },
  vivienda: { icon: "🏚", label: "VIVIENDA", color: "#ff8c42" },
  seguridad: { icon: "🚨", label: "SEGURIDAD", color: "#ff3b5c" },
  politico: { icon: "⚖", label: "POLÍTICO", color: "#a78bfa" },
  salud: { icon: "✚", label: "SALUD", color: "#ff3b5c" },
  educativo: { icon: "📚", label: "EDUCATIVO", color: "#ffd93d" },
  tierra: { icon: "◆", label: "TIERRA", color: "#4ade80" },
  otro: { icon: "·", label: "OTRO", color: "#718096" },
};

const nivelDeScore = (score) => {
  if (score >= 8) return "critico";
  if (score >= 6) return "alto";
  if (score >= 4) return "medio";
  if (score >= 1) return "bajo";
  return "sin_datos";
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [municipioSeleccionado, setMunicipioSeleccionado] = useState(null);
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null);
  const [regionFiltro, setRegionFiltro] = useState("TODAS");

  const cargar = async () => {
    try {
      const res = await fetch("/api/situacion-municipios");
      const json = await res.json();
      setData(json);
      setUltimaActualizacion(new Date().toLocaleString("es-AR"));
    } catch (err) {
      console.error("Error:", err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
    const interval = setInterval(cargar, 60000);
    return () => clearInterval(interval);
  }, []);

  if (cargando) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-cyan-400 font-mono text-sm animate-pulse">
          ► CARGANDO SISTEMA DE ANÁLISIS...
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-red-500 font-mono text-sm">
          ✕ ERROR CARGANDO DATOS
        </div>
      </div>
    );
  }

  // Agrupar por región
  const porRegion = {};
  data.municipios.forEach((m) => {
    if (!porRegion[m.region]) porRegion[m.region] = [];
    porRegion[m.region].push(m);
  });

  const regionesVisibles =
    regionFiltro === "TODAS"
      ? Object.keys(MUNICIPIOS_CHACO)
      : [regionFiltro];

  // Top prioridades (score más alto, con análisis)
  const prioridades = data.municipios
    .filter((m) => m.total_analisis > 0)
    .sort((a, b) => b.score_max - a.score_max)
    .slice(0, 5);

  // Municipios con alerta por escalada
  const enEscalada = data.municipios.filter(
    (m) => m.puede_escalar || m.score_max >= 6
  );

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

      {/* Top bar */}
      <div className="relative border-b border-cyan-900/40 bg-black/60 backdrop-blur sticky top-0 z-30">
        <div className="max-w-[1800px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(0,217,255,0.9)]" />
              <span className="font-mono text-xs tracking-[0.2em] text-cyan-400">
                LIVE
              </span>
            </div>
            <span className="text-slate-800">|</span>
            <span className="font-mono text-xs text-slate-500 tracking-wider">
              SYNC {ultimaActualizacion}
            </span>
            <span className="text-slate-800">|</span>
            <span className="font-mono text-xs text-slate-500 tracking-wider">
              {data.con_analisis}/{data.total_municipios} MUNICIPIOS ACTIVOS
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-slate-600 tracking-wider hidden md:block">
            l
            </span>
            <button
              onClick={cargar}
              className="font-mono text-xs tracking-wider px-3 py-1.5 border border-cyan-500/60 text-cyan-400 hover:bg-cyan-500 hover:text-black transition-all"
            >
              ► REFRESCAR
            </button>
          </div>
        </div>
      </div>

      <div className="relative max-w-[1800px] mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex items-end justify-between">
          <div>
            <div className="font-mono text-xs tracking-[0.3em] text-cyan-500 mb-1">
              SISTEMA DE INTELIGENCIA · CONFLICTIVIDAD SOCIAL
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Análisis de Conflictividad{" "}
              <span className="text-cyan-400">— Chaco</span>
            </h1>
          </div>
          <div className="text-right font-mono text-xs text-slate-600">
            <div>PRÓX SYNC</div>
            <div className="text-cyan-400">{new Date(Date.now() + 3600000).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })}</div>
          </div>
        </div>

        {/* Métricas grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <MetricCard
            label="MUNICIPIOS"
            value={data.total_municipios}
            color="#00d9ff"
            sub="Chaco"
          />
          <MetricCard
            label="ANALIZADOS"
            value={data.con_analisis}
            color="#a78bfa"
            sub="Últimos 30 días"
          />
          <MetricCard
            label="ÚLTIMAS 24HS"
            value={Math.min(data.con_analisis, prioridades.length)}
            color="#4ade80"
            sub="Eventos nuevos"
          />
          <MetricCard
            label="ESCALADA"
            value={enEscalada.length}
            color="#ff8c42"
            sub="Score ≥ 6"
          />
          <MetricCard
            label="ALERTA CRÍTICA"
            value={data.en_alerta}
            color="#ff3b5c"
            sub="Score ≥ 7"
          />
        </div>

        {/* Grid principal */}
        <div className="grid grid-cols-12 gap-4">
          {/* Columna izquierda: prioridades + mapa */}
          <div className="col-span-12 xl:col-span-4 space-y-4">
            {/* Prioridades */}
            <Panel titulo="PRIORIDADES DE ANÁLISIS" color="#ff3b5c">
              {prioridades.length === 0 ? (
                <div className="text-slate-600 font-mono text-xs p-4 text-center">
                  Sin análisis aún. Ejecutá el scheduler.
                </div>
              ) : (
                <div className="space-y-2">
                  {prioridades.map((m, idx) => {
                    const nivel = nivelDeScore(m.score_max);
                    const est = NIVELES[nivel];
                    return (
                      <button
                        key={m.municipio}
                        onClick={() => setMunicipioSeleccionado(m)}
                        className="w-full text-left border rounded-lg p-3 transition-all hover:border-cyan-500/50"
                        style={{
                          backgroundColor: est.bg,
                          borderColor: est.border,
                        }}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-slate-600">
                              #{String(idx + 1).padStart(2, "0")}
                            </span>
                            <span className="font-bold text-white text-sm">
                              {m.municipio}
                            </span>
                          </div>
                          <span
                            className="font-mono text-xs font-bold px-2 py-0.5 rounded"
                            style={{ backgroundColor: est.color, color: "#000" }}
                          >
                            {m.score_max}/10
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1 mb-1.5">
                          {Object.entries(m.categorias)
                            .sort((a, b) => b[1] - a[1])
                            .slice(0, 3)
                            .map(([cat]) => {
                              const meta = CATEGORIA_META[cat] || CATEGORIA_META.otro;
                              return (
                                <span
                                  key={cat}
                                  className="font-mono text-xs px-1.5 py-0.5 border rounded"
                                  style={{
                                    color: meta.color,
                                    borderColor: `${meta.color}40`,
                                  }}
                                >
                                  {meta.icon} {meta.label}
                                </span>
                              );
                            })}
                        </div>
                        <div className="text-xs text-slate-400 line-clamp-2">
                          {m.problematicas[0]?.problematica || "Sin detalle"}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </Panel>

            {/* Seguimiento de escalabilidad */}
            <Panel titulo="SEGUIMIENTO DE ESCALABILIDAD" color="#ff8c42">
              <div className="space-y-2">
                {enEscalada.slice(0, 5).map((m) => {
                  const nivel = nivelDeScore(m.score_max);
                  const est = NIVELES[nivel];
                  return (
                    <div
                      key={m.municipio}
                      className="border border-slate-800 rounded p-2.5 bg-black/40"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-white">
                          {m.municipio}
                        </span>
                        <span
                          className="font-mono text-xs"
                          style={{ color: est.color }}
                        >
                          {est.label}
                        </span>
                      </div>
                      <div className="w-full h-1 bg-slate-900 rounded-full overflow-hidden">
                        <div
                          className="h-full transition-all"
                          style={{
                            width: `${m.score_max * 10}%`,
                            backgroundColor: est.color,
                            boxShadow: `0 0 8px ${est.color}`,
                          }}
                        />
                      </div>
                      {m.consecuencia && (
                        <div className="text-xs text-slate-500 mt-1.5">
                          ▸ {m.consecuencia}
                        </div>
                      )}
                    </div>
                  );
                })}
                {enEscalada.length === 0 && (
                  <div className="text-slate-600 font-mono text-xs text-center py-4">
                    Sin focos en escalada
                  </div>
                )}
              </div>
            </Panel>

            {/* Próximamente: redes */}
            <Panel titulo="ANÁLISIS DE REDES SOCIALES" color="#a78bfa" disabled>
              <div className="text-center py-6">
                <div className="font-mono text-xs text-slate-600 tracking-widest">
                  PRÓXIMAMENTE
                </div>
                <div className="text-xs text-slate-700 mt-2">
                  Integración con X, Facebook y otras fuentes
                </div>
              </div>
            </Panel>
          </div>

          {/* Columna central + derecha: municipios por región */}
          <div className="col-span-12 xl:col-span-8 space-y-4">
            {/* Filtro de regiones */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setRegionFiltro("TODAS")}
                className={`font-mono text-xs tracking-wider px-3 py-1.5 border transition-all ${
                  regionFiltro === "TODAS"
                    ? "border-cyan-500 text-cyan-400 bg-cyan-500/10"
                    : "border-slate-800 text-slate-500 hover:border-slate-700"
                }`}
              >
                TODAS
              </button>
              {Object.keys(MUNICIPIOS_CHACO).map((r) => (
                <button
                  key={r}
                  onClick={() => setRegionFiltro(r)}
                  className={`font-mono text-xs tracking-wider px-3 py-1.5 border transition-all ${
                    regionFiltro === r
                      ? "border-cyan-500 text-cyan-400 bg-cyan-500/10"
                      : "border-slate-800 text-slate-500 hover:border-slate-700"
                  }`}
                >
                  {r.split(" — ")[0].toUpperCase()}
                </button>
              ))}
            </div>

            {/* Cuadros por región */}
            {regionesVisibles.map((region) => {
              const municipios = MUNICIPIOS_CHACO[region] || [];
              const datosRegion = porRegion[region] || [];
              const maxScore = Math.max(...datosRegion.map((m) => m.score_max), 0);

              return (
                <div
                  key={region}
                  className="border border-slate-900 rounded-xl bg-black/40 backdrop-blur p-4"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: NIVELES[nivelDeScore(maxScore)].color,
                          boxShadow: `0 0 6px ${NIVELES[nivelDeScore(maxScore)].color}`,
                        }}
                      />
                      <h3 className="font-bold text-white text-sm tracking-wide">
                        {region}
                      </h3>
                      <span className="font-mono text-xs text-slate-600">
                        {municipios.length} MUN
                      </span>
                    </div>
                    <div className="font-mono text-xs text-slate-600">
                      MAX {maxScore}/10
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    {municipios.map((nombre) => {
                      const info = datosRegion.find((d) => d.municipio === nombre);
                      return (
                        <CuadroMunicipio
                          key={nombre}
                          municipio={nombre}
                          info={info}
                          onClick={() =>
                            setMunicipioSeleccionado(info || { municipio: nombre })
                          }
                          seleccionado={
                            municipioSeleccionado?.municipio === nombre
                          }
                        />
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Modal/panel de detalle */}
      {municipioSeleccionado && (
        <PanelDetalleMunicipio
          info={municipioSeleccionado}
          onClose={() => setMunicipioSeleccionado(null)}
        />
      )}
    </div>
  );
}

function MetricCard({ label, value, color, sub }) {
  return (
    <div
      className="border rounded-lg p-4 bg-black/40 backdrop-blur relative overflow-hidden"
      style={{ borderColor: `${color}30` }}
    >
      <div
        className="absolute top-0 right-0 w-16 h-16 rounded-full blur-3xl opacity-20"
        style={{ backgroundColor: color }}
      />
      <div
        className="font-mono text-xs tracking-widest mb-2"
        style={{ color }}
      >
        {label}
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
      <div className="font-mono text-xs text-slate-600 mt-1">{sub}</div>
    </div>
  );
}

function Panel({ titulo, color, children, disabled }) {
  return (
    <div
      className={`border rounded-xl bg-black/40 backdrop-blur overflow-hidden ${
        disabled ? "opacity-60" : ""
      }`}
      style={{ borderColor: `${color}25` }}
    >
      <div
        className="px-4 py-3 border-b flex items-center gap-2"
        style={{ borderColor: `${color}20` }}
      >
        <div
          className="w-1 h-3 rounded"
          style={{ backgroundColor: color }}
        />
        <h3
          className="font-mono text-xs tracking-widest font-bold"
          style={{ color }}
        >
          {titulo}
        </h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function CuadroMunicipio({ municipio, info, onClick, seleccionado }) {
  const score = info?.score_max || 0;
  const nivel = nivelDeScore(score);
  const est = NIVELES[nivel];
  const cats = Object.entries(info?.categorias || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);
  const tieneDatos = info?.total_analisis > 0;

  return (
    <button
      onClick={onClick}
      className={`text-left rounded-lg border p-2.5 transition-all hover:scale-[1.02] relative overflow-hidden ${
        seleccionado ? "ring-2 ring-cyan-400" : ""
      }`}
      style={{
        backgroundColor: tieneDatos ? est.bg : "rgba(15,23,42,0.3)",
        borderColor: tieneDatos ? est.border : "rgba(30,41,59,0.5)",
      }}
    >
      {tieneDatos && (
        <div
          className="absolute top-0 left-0 w-full h-0.5"
          style={{ backgroundColor: est.color }}
        />
      )}
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="text-xs font-bold text-white leading-tight truncate">
          {municipio}
        </div>
        <div
          className="font-mono text-xs font-bold px-1.5 rounded flex-shrink-0"
          style={{
            backgroundColor: tieneDatos ? est.color : "transparent",
            color: tieneDatos ? "#000" : "#475569",
            border: tieneDatos ? "none" : "1px solid #1e293b",
          }}
        >
          {score}
        </div>
      </div>

      {tieneDatos ? (
        <>
          <div className="flex flex-wrap gap-1 mb-1.5">
            {cats.map(([cat]) => {
              const meta = CATEGORIA_META[cat] || CATEGORIA_META.otro;
              return (
                <span
                  key={cat}
                  className="font-mono text-xs"
                  style={{ color: meta.color }}
                  title={meta.label}
                >
                  {meta.icon}
                </span>
              );
            })}
          </div>
          <div className="text-xs text-slate-500 line-clamp-2 leading-tight">
            {info.problematicas[0]?.problematica?.slice(0, 60) || ""}
          </div>
        </>
      ) : (
        <div className="font-mono text-xs text-slate-700 italic">
          SIN ANÁLISIS
        </div>
      )}
    </button>
  );
}

function PanelDetalleMunicipio({ info, onClose }) {
  const score = info.score_max || 0;
  const nivel = nivelDeScore(score);
  const est = NIVELES[nivel];

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-slate-950 border border-cyan-900/40 rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="p-6 border-b sticky top-0 z-10 backdrop-blur"
          style={{
            backgroundColor: "rgba(2,6,23,0.95)",
            borderColor: `${est.color}30`,
          }}
        >
          <div className="flex items-start justify-between">
            <div>
              <div
                className="font-mono text-xs tracking-widest mb-1"
                style={{ color: est.color }}
              >
                {est.label} · SCORE {score}/10
              </div>
              <h2 className="text-2xl font-bold text-white">
                {info.municipio}
              </h2>
              <div className="font-mono text-xs text-slate-500 mt-1">
                {info.region}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-slate-500 hover:text-white font-mono text-xl w-8 h-8 flex items-center justify-center"
            >
              ×
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Score bar */}
          <div>
            <div className="font-mono text-xs text-slate-500 tracking-widest mb-2">
              NIVEL DE CONFLICTIVIDAD
            </div>
            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${score * 10}%`,
                  backgroundColor: est.color,
                  boxShadow: `0 0 12px ${est.color}`,
                }}
              />
            </div>
            {info.total_analisis > 0 && (
              <div className="font-mono text-xs text-slate-600 mt-2">
                {info.total_analisis} análisis · promedio {info.score_promedio}/10
              </div>
            )}
          </div>

          {/* Escalabilidad */}
          {info.puede_escalar && (
            <div
              className="border rounded-lg p-4"
              style={{
                backgroundColor: "rgba(255,59,92,0.05)",
                borderColor: "rgba(255,59,92,0.3)",
              }}
            >
              <div className="font-mono text-xs text-red-400 tracking-widest mb-2">
                ⚠ RIESGO DE ESCALADA
              </div>
              {info.tiempo_escalada && (
                <div className="text-sm text-white mb-1">
                  Tiempo estimado: <strong>{info.tiempo_escalada}</strong>
                </div>
              )}
              {info.consecuencia && (
                <div className="text-sm text-slate-400">
                  {info.consecuencia}
                </div>
              )}
            </div>
          )}

          {/* Categorías */}
          {Object.keys(info.categorias || {}).length > 0 && (
            <div>
              <div className="font-mono text-xs text-slate-500 tracking-widest mb-2">
                CATEGORÍAS DETECTADAS
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(info.categorias)
                  .sort((a, b) => b[1] - a[1])
                  .map(([cat, count]) => {
                    const meta = CATEGORIA_META[cat] || CATEGORIA_META.otro;
                    return (
                      <div
                        key={cat}
                        className="border rounded px-2 py-1 flex items-center gap-1.5"
                        style={{
                          borderColor: `${meta.color}40`,
                          backgroundColor: `${meta.color}10`,
                        }}
                      >
                        <span style={{ color: meta.color }}>
                          {meta.icon}
                        </span>
                        <span className="font-mono text-xs text-white">
                          {meta.label}
                        </span>
                        <span className="font-mono text-xs text-slate-500">
                          {count}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Análisis */}
          {info.problematicas?.length > 0 && (
            <div>
              <div className="font-mono text-xs text-slate-500 tracking-widest mb-2">
                ANÁLISIS DETALLADO
              </div>
              <div className="space-y-2">
                {info.problematicas.map((p, i) => {
                  const meta = CATEGORIA_META[p.categoria] || CATEGORIA_META.otro;
                  const pNivel = nivelDeScore(p.score);
                  const pEst = NIVELES[pNivel];
                  return (
                    <div
                      key={i}
                      className="border border-slate-800 rounded-lg p-3 bg-black/40"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span style={{ color: meta.color }}>
                            {meta.icon}
                          </span>
                          <span className="font-mono text-xs text-slate-400">
                            {meta.label}
                          </span>
                        </div>
                        <span
                          className="font-mono text-xs font-bold px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: pEst.color,
                            color: "#000",
                          }}
                        >
                          {p.score}/10
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 leading-relaxed">
                        {p.problematica}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {info.total_analisis === 0 && (
            <div className="text-center py-8">
              <div className="font-mono text-xs text-slate-600 tracking-widest">
                SIN ANÁLISIS EN LOS ÚLTIMOS 30 DÍAS
              </div>
              <div className="text-xs text-slate-700 mt-2">
                El scheduler recolecta automáticamente cada 6 horas
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}