import urllib.parse
import feedparser
from datetime import datetime, timedelta

# Medios chaqueños principales (según tu región)
MEDIOS_CHACO = [
    "diarionorte.com",
    "datachaco.com",
    "primeralinea.com.ar",
    "diario22.com.ar",
    "chaconea.com",
]

def buscar_noticias_municipio(municipio: str, provincia: str | None = None,
                              max_resultados: int = 15) -> list[dict]:
    """
    Búsqueda mejorada: consulta cada medio chaqueño por separado,
    usando ventanas de fecha explícitas.
    """
    resultados = []
    vistos = set()

    # Calcular ventana: últimos 14 días
    hoy = datetime.now()
    hace_14_dias = hoy - timedelta(days=14)
    after = hace_14_dias.strftime("%Y-%m-%d")
    before = hoy.strftime("%Y-%m-%d")

    for medio in MEDIOS_CHACO:
        # Consulta simple: municipio + site:medio + rango de fechas
        # Sin comillas, sin OR complejos
        query = f'{municipio} site:{medio} after:{after} before:{before}'

        params = {
            "q": query,
            "hl": "es-419",
            "gl": "AR",
            "ceid": "AR:es-419",
        }
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
        feed = feedparser.parse(url)

        for entry in feed.entries:
            link = entry.get("link", "")
            if link in vistos:
                continue
            vistos.add(link)

            source = getattr(entry, "source", {}) or {}
            resultados.append({
                "titulo": entry.get("title", ""),
                "link": link,
                "fuente": source.get("title", medio),
                "fecha": entry.get("published", ""),
                "municipio": municipio,
                "provincia": provincia,
            })

        # Cortar si ya tenemos suficientes
        if len(resultados) >= max_resultados:
            break

    # Fallback: si no encontramos nada, buscar solo "municipio + provincia"
    if not resultados:
        query = f'{municipio} {provincia}' if provincia else municipio
        params = {"q": query, "hl": "es-419", "gl": "AR", "ceid": "AR:es-419"}
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
        feed = feedparser.parse(url)

        for entry in feed.entries[:max_resultados]:
            source = getattr(entry, "source", {}) or {}
            resultados.append({
                "titulo": entry.get("title", ""),
                "link": entry.get("link", ""),
                "fuente": source.get("title", "Google News"),
                "fecha": entry.get("published", ""),
                "municipio": municipio,
                "provincia": provincia,
            })

    return resultados[:max_resultados]