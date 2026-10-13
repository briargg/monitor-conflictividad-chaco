# scraper_chaco.py
import feedparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ⚠️ ACÁ van TODAS las fuentes con RSS verificado
FUENTES_RSS = [
    {"nombre": "Diario Norte", "url": "https://www.diarionorte.com/rss"},
    # Descomentá las que funcionen al verificar:
     {"nombre": "Data Chaco", "url": "https://www.datachaco.com/rss"},
    # {"nombre": "Diario 22", "url": "https://www.diario22.com.ar/feed"},
     {"nombre": "Chaco Día por Día", "url": "https://www.chacodiapordia.com/feed"},
    # {"nombre": "Primera Línea", "url": "https://www.primeralinea.com.ar/feed"},
]

KEYWORDS_CONFLICTO = [
    "protesta", "reclamo", "corte", "bloqueo", "desalojo",
    "toma", "manifestación", "paro", "huelga", "marcha",
    "piquete", "conflicto", "docente", "vecinos", "barrio",
    "municipio", "policía", "indígena", "ruta", "crecida",
    "inundación", "emergencia", "evacuados", "anegamiento",
    "reclaman", "reclamó", "protestan", "cortaron", "bloquearon",
    "desalojan", "desalojaron", "toman", "tomaron", "marchan",
    "reclamo salarial", "falta de agua", "corte de luz",
    "inseguridad", "violencia", "delito", "robo", "droga",
    "desborde", "alerta", "evacuación", "damnificados"
]


def _parsear_fecha(fecha_str):
    if not fecha_str:
        return None
    formatos = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _texto_del_item(entry):
    partes = [
        entry.get("title", ""),
        entry.get("description", ""),
        entry.get("summary", ""),
    ]
    for tag in entry.get("tags", []):
        if isinstance(tag, dict) and "term" in tag:
            partes.append(tag["term"])
        elif isinstance(tag, str):
            partes.append(tag)
    return " ".join(p for p in partes if p).lower()


def _leer_fuente(fuente, max_por_fuente=30):
    """Lee un feed RSS y devuelve lista de noticias crudas."""
    try:
        feed = feedparser.parse(fuente["url"])
        if feed.bozo and not feed.entries:
            return []
        return [
            {
                "titulo": e.get("title", "").strip(),
                "link": e.get("link", "").strip(),
                "fuente": fuente["nombre"],
                "fecha": e.get("published", e.get("updated", "")),
                "texto": _texto_del_item(e),
            }
            for e in feed.entries[:max_por_fuente]
            if e.get("title") and e.get("link")
        ]
    except Exception as exc:
        print(f"[scraper] Error leyendo {fuente['nombre']}: {exc}")
        return []


def buscar_noticias_chaco(municipio=None, max_resultados=15,
                          desde=None, hasta=None, solo_conflictos=False):
    """
    Busca noticias en MÚLTIPLES fuentes del Chaco en paralelo.
    """
    todas = []

    # Leer todas las fuentes en paralelo
    with ThreadPoolExecutor(max_workers=len(FUENTES_RSS)) as executor:
        futuros = {
            executor.submit(_leer_fuente, f): f for f in FUENTES_RSS
        }
        for fut in as_completed(futuros):
            todas.extend(fut.result())

    # Deduplicar por link
    vistos = set()
    unicas = []
    for n in todas:
        if n["link"] not in vistos:
            vistos.add(n["link"])
            unicas.append(n)

    # Filtrar
    resultados = []
    for n in unicas:
        if municipio and municipio.lower() not in n["texto"]:
            continue

        if desde or hasta:
            fecha = _parsear_fecha(n["fecha"])
            if not fecha:
                continue
            if desde and fecha < datetime.strptime(desde, "%Y-%m-%d"):
                continue
            if hasta and fecha > datetime.strptime(hasta, "%Y-%m-%d"):
                continue

        if solo_conflictos:
            if not any(kw in n["texto"] for kw in KEYWORDS_CONFLICTO):
                continue

        resultados.append({
            "titulo": n["titulo"],
            "link": n["link"],
            "fuente": n["fuente"],
            "fecha": n["fecha"],
            "municipio": municipio,
            "provincia": "Chaco",
        })

        if len(resultados) >= max_resultados:
            break

    return resultados


def listar_todas_las_noticias(max_por_fuente=50):
    """Devuelve TODAS las noticias de TODAS las fuentes (sin filtrar)."""
    todas = []
    with ThreadPoolExecutor(max_workers=len(FUENTES_RSS)) as executor:
        futuros = [
            executor.submit(_leer_fuente, f, max_por_fuente) for f in FUENTES_RSS
        ]
        for fut in as_completed(futuros):
            todas.extend(fut.result())

    vistos = set()
    unicas = []
    for n in todas:
        if n["link"] not in vistos:
            vistos.add(n["link"])
            unicas.append(n)

    return unicas