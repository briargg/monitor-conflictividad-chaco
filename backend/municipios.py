import requests
from functools import lru_cache

REGIONES = {
    "NOA": ["Catamarca", "Jujuy", "La Rioja", "Salta", "Santiago del Estero", "Tucumán"],
    "NEA": ["Chaco", "Corrientes", "Formosa", "Misiones"],
    "Centro": ["Buenos Aires", "Córdoba", "Entre Ríos", "Santa Fe", "La Pampa", "Ciudad Autónoma de Buenos Aires"],
    "Cuyo": ["Mendoza", "San Juan", "San Luis"],
    "Patagonia": ["Chubut", "Neuquén", "Río Negro", "Santa Cruz", "Tierra del Fuego"]
}

@lru_cache(maxsize=1)
def obtener_municipios_nacional():
    url = "https://apis.datos.gob.ar/georef/api/v2.0/municipios?max=5000"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return [{
            "id": m.get("id"), "nombre": m.get("nombre"),
            "provincia": (m.get("provincia") or {}).get("nombre"),
            "lat": (m.get("centroide") or {}).get("lat"),
            "lon": (m.get("centroide") or {}).get("lon")
        } for m in data.get("municipios", [])]
    except Exception as exc:
        print(f"No se pudo obtener Georef: {exc}")
        return []

def obtener_region(provincia: str | None) -> str:
    for region, provincias in REGIONES.items():
        if provincia in provincias: return region
    return "Desconocida"

def municipios_por_provincia(provincia: str):
    return [m for m in obtener_municipios_nacional() if m["provincia"] == provincia]
