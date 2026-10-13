import requests
from functools import lru_cache
from datetime import datetime

# CEDEI - Estaciones meteorológicas del Chaco (actualización cada 10 min) [citation:10]
CEDEI_API = "https://estaciones-produccion.chaco.gob.ar/api/estaciones"

# INA - Sistema de Alerta Hidrológico Cuenca del Plata [citation:2]
INA_API = "https://alerta.ina.gob.ar/a5/secciones"


def obtener_clima_cedei():
    """
    Obtiene datos meteorológicos en tiempo real del Chaco.
    Fuente: Red de Estaciones Meteorológicas de la Provincia del Chaco.
    Actualización cada 10 minutos.
    """
    try:
        r = requests.get(CEDEI_API, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # Buscar estación más cercana a Resistencia o promediar
            estaciones = data.get("estaciones", data.get("data", []))
            if estaciones:
                # Promediar datos de toda la provincia
                lluvia_total = sum(e.get("lluvia", 0) for e in estaciones)
                temp_prom = sum(e.get("temperatura", 0) for e in estaciones) / len(estaciones)
                return {
                    "lluvia_promedio_mm": round(lluvia_total / len(estaciones), 1),
                    "temperatura_promedio": round(temp_prom, 1),
                    "estaciones_activas": len(estaciones),
                    "fuente": "CEDEI Chaco",
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as exc:
        print(f"[fuentes_externas] Error CEDEI: {exc}")
    return None


def obtener_alerta_hidrologica():
    """
    Consulta el Sistema de Información y Alerta Hidrológico del INA.
    Incluye datos de caudal del río Paraná y estado de alerta. [citation:2]
    """
    try:
        r = requests.get(INA_API, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # Buscar sección del Chaco / Barranqueras
            for seccion in data:
                nombre = str(seccion.get("nombre", "")).lower()
                if "chaco" in nombre or "barranqueras" in nombre:
                    return {
                        "nivel_m": seccion.get("altura"),
                        "estado": seccion.get("estado"),
                        "alerta": seccion.get("alerta"),
                        "evacuacion": seccion.get("evacuacion"),
                        "fuente": "INA",
                        "timestamp": datetime.now().isoformat()
                    }
    except Exception as exc:
        print(f"[fuentes_externas] Error INA: {exc}")
    return None


def enriquecer_analisis(analisis: dict) -> dict:
    """
    Agrega contexto meteorológico e hidrológico al análisis
    si la categoría lo requiere.
    """
    cat = analisis.get("categoria", "")
    contexto = []

    if cat in ("clima", "emergencia"):
        clima = obtener_clima_cedei()
        if clima and clima.get("lluvia_promedio_mm", 0) > 0:
            contexto.append(f"Lluvia prom: {clima['lluvia_promedio_mm']}mm")
        if clima and clima.get("temperatura_promedio"):
            contexto.append(f"Temp: {clima['temperatura_promedio']}°C")

    # Siempre consultar alerta hidrológica si es emergencia o clima
    if cat in ("clima", "emergencia", "vivienda"):
        rio = obtener_alerta_hidrologica()
        if rio and rio.get("nivel_m"):
            contexto.append(f"Río Paraná: {rio['nivel_m']}m")
        if rio and rio.get("alerta"):
            contexto.append(f"Alerta: {rio['alerta']}")

    if contexto:
        analisis["contexto_externo"] = " | ".join(contexto)

    return analisis