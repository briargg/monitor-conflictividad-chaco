import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from analyzer import analizar_noticia
from alertas import evaluar_alerta, enviar_alerta_telegram
from database import init_db, guardar_conflicto, obtener_conflictos
from informes import generar_resumen_semanal, generar_informe_mensual
from municipios import obtener_municipios_nacional, municipios_por_provincia, obtener_region
from scraper_chaco import buscar_noticias_chaco
from scheduler import iniciar_scheduler
from auth import autenticar_usuario, crear_token, usuario_actual
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
load_dotenv()

# Los 69 municipios del Chaco por región
MUNICIPIOS_CHACO = {
    "Región 1 — Sudoeste": [
        "Villa Ángela", "Coronel Du Graty", "Samuhú", "Enrique Urien",
        "Santa Sylvina", "La Tigra", "San Bernardo"
    ],
    "Región 2 — Centro-Este": [
        "Presidencia Roque Sáenz Peña", "Machagai", "Quitilipi",
        "Presidencia de la Plaza", "Villa Berthet", "Las Garcitas"
    ],
    "Región 3 — Oriental": [
        "Resistencia", "Barranqueras", "Fontana", "La Escondida", "Makallé",
        "Las Palmas", "La Leonesa", "Puerto Tirol", "Puerto Vilelas",
        "Basail", "Cote Lai", "Colonia Benítez", "Colonia Popular",
        "Charadai", "General Vedia", "Isla del Cerrito", "La Verde",
        "Laguna Blanca", "Lapachito", "Margarita Belén", "Puerto Bermejo",
        "Puerto Eva Perón", "Colonia Elisa"
    ],
    "Región 4 — Sudoeste II": [
        "Las Breñas", "Charata", "Corzuela", "General Capdevila",
        "General Pinedo", "Chorotis", "Hermoso Campo", "Gancedo"
    ],
    "Región 5 — Impenetrable": [
        "Juan José Castelli", "Tres Isletas", "Fuerte Esperanza",
        "Misión Nueva Pompeya", "Villa Río Bermejito", "El Sauzalito", "Miraflores"
    ],
    "Región 6 — Norte": [
        "General San Martín", "Capitán Solari", "Ciervo Petiso",
        "Colonias Unidas", "La Eduvigis", "Laguna Limpia", "Pampa Almirón",
        "Presidencia Roca", "Pampa del Indio"
    ],
    "Región 7 — Oeste": [
        "Pampa del Infierno", "Los Frentones", "Concepción del Bermejo",
        "Taco Pozo", "Campo Largo", "Napenay", "Avia Terai"
    ],
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    iniciar_scheduler()
    yield


app = FastAPI(title="Monitor de Conflictividad — Chaco", version="2.0.0", lifespan=lifespan)

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"estado": "ok"}


@app.get("/api/municipios")
def listar_municipios(provincia: str | None = None):
    municipios = municipios_por_provincia(provincia) if provincia else obtener_municipios_nacional()
    return {"total": len(municipios), "municipios": municipios}


@app.get("/api/analyze")
async def analizar_municipio(
    municipio: str = Query(..., min_length=2, max_length=100),
    provincia: str | None = Query(None, max_length=100),
    limite: int = Query(10, ge=1, le=20),
):
    noticias = await asyncio.to_thread(buscar_noticias_chaco, municipio, limite)
    if not noticias:
        return {"municipio": municipio, "total": 0, "conflictos": []}

    semaphore = asyncio.Semaphore(2)

    async def procesar(noticia):
        async with semaphore:
            try:
                analisis = await asyncio.to_thread(analizar_noticia, noticia)
                conflict_id = await asyncio.to_thread(guardar_conflicto, noticia, analisis)
                alerta = evaluar_alerta(analisis, noticia)
                if alerta and conflict_id:
                    await asyncio.to_thread(enviar_alerta_telegram, alerta, conflict_id)
                return {**noticia, "analisis": analisis}
            except Exception as exc:
                print(f"Análisis omitido: {exc}")
                return None

    resultados = await asyncio.gather(*(procesar(n) for n in noticias))
    validos = [r for r in resultados if r]
    scores = [int((v.get("analisis", {}).get("score") or 0)) for v in validos]

    return {
        "municipio": municipio,
        "total": len(validos),
        "score_promedio": round(sum(scores) / len(scores), 1) if scores else 0,
        "conflictos": validos,
    }


@app.get("/api/conflictos")
def listar_conflictos(
    provincia: str | None = None,
    municipio: str | None = None,
    desde: str | None = None,
    limite: int = Query(100, ge=1, le=500),
):
    return {"conflictos": obtener_conflictos(provincia, municipio, desde, limite)}


@app.get("/api/situacion-municipios")
def situacion_municipios():
    """
    Devuelve el análisis de situación por municipio del Chaco.
    Cada municipio incluye: score máximo, categorías activas, tendencia, riesgo de escalada.
    """
    from datetime import datetime, timedelta

    hace_30_dias = (datetime.now() - timedelta(days=30)).isoformat()
    conflictos = obtener_conflictos(desde=hace_30_dias, limite=3000)

    # Inicializar estructura para los 69 municipios
    municipios_data = {}
    for region, munis in MUNICIPIOS_CHACO.items():
        for m in munis:
            municipios_data[m] = {
                "municipio": m,
                "region": region,
                "score_max": 0,
                "score_promedio": 0,
                "total_analisis": 0,
                "categorias": {},
                "fase_predominante": "sin_datos",
                "puede_escalar": False,
                "tiempo_escalada": None,
                "consecuencia": None,
                "ultima_actualizacion": None,
                "problematicas": [],
            }

    # Agrupar conflictos
    for c in conflictos:
        m = c.get("municipio")
        if m not in municipios_data:
            continue
        info = municipios_data[m]
        info["total_analisis"] += 1

        score = c.get("escalabilidad", 0) or 0
        info["score_promedio"] += score
        if score > info["score_max"]:
            info["score_max"] = score

        cat = c.get("tipo", "otro")
        info["categorias"][cat] = info["categorias"].get(cat, 0) + 1

        if c.get("problematica"):
            info["problematicas"].append({
                "problematica": c["problematica"][:140],
                "score": score,
                "categoria": cat,
                "fecha": c.get("fecha_analisis"),
            })

        fecha = c.get("fecha_analisis") or ""
        if not info["ultima_actualizacion"] or fecha > info["ultima_actualizacion"]:
            info["ultima_actualizacion"] = fecha

        # Guardar la fase del conflicto de mayor score
        if score == info["score_max"] and c.get("fase"):
            info["fase_predominante"] = c["fase"]
        if score == info["score_max"] and c.get("requiere_alerta"):
            info["puede_escalar"] = True

    # Calcular promedios y top problemáticas
    resultado = []
    for m, info in municipios_data.items():
        if info["total_analisis"] > 0:
            info["score_promedio"] = round(info["score_promedio"] / info["total_analisis"], 1)
        info["problematicas"] = sorted(info["problematicas"], key=lambda x: -x["score"])[:3]
        resultado.append(info)

    # Ordenar por score
    resultado.sort(key=lambda x: -x["score_max"])

    return {
        "total_municipios": 69,
        "con_analisis": sum(1 for x in resultado if x["total_analisis"] > 0),
        "en_alerta": sum(1 for x in resultado if x["score_max"] >= 7),
        "municipios": resultado,
    }


@app.get("/api/resumen-semanal")
def resumen_semanal():
    return {"informe": generar_resumen_semanal()}


@app.get("/api/informe-mensual")
def informe_mensual():
    return {"informe": generar_informe_mensual()}

@app.get("/api/alertas-nuevas")
def alertas_nuevas():
    """
    Devuelve las alertas de las últimas 24 horas.
    Usado por el frontend para notificar en la web.
    """
    from datetime import datetime, timedelta

    hace_24hs = (datetime.now() - timedelta(hours=24)).isoformat()
    conflictos = obtener_conflictos(desde=hace_24hs, limite=200)

    # Filtrar solo los que requieren alerta
    alertas = [
        c for c in conflictos
        if c.get("escalabilidad", 0) >= 7 or c.get("requiere_alerta")
    ]

    # Agrupar por municipio
    por_municipio = {}
    for a in alertas:
        m = a.get("municipio")
        if m not in por_municipio:
            por_municipio[m] = []
        por_municipio[m].append({
            "problematica": a.get("problematica"),
            "score": a.get("escalabilidad"),
            "categoria": a.get("tipo"),
            "fecha": a.get("fecha_analisis"),
            "link": a.get("link"),
        })

    return {
        "total": len(alertas),
        "municipios_afectados": len(por_municipio),
        "alertas": por_municipio,
    }


@app.get("/api/clima-actual")
def clima_actual():
    """Datos meteorológicos en tiempo real del Chaco (CEDEI)."""
    from fuentes_externas import obtener_clima_cedei
    return obtener_clima_cedei() or {"error": "Sin datos"}


@app.get("/api/alerta-hidrologica")
def alerta_hidrologica():
    """Estado del río Paraná y alertas de crecida (INA)."""
    from fuentes_externas import obtener_alerta_hidrologica
    return obtener_alerta_hidrologica() or {"error": "Sin datos"}

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not autenticar_usuario(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = crear_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/me")
def obtener_usuario_actual(username: str = Depends(usuario_actual)):
    return {"username": username}