from datetime import datetime, timedelta
from collections import Counter, defaultdict
from database import obtener_conflictos

def generar_resumen_semanal():
    hoy = datetime.now()
    inicio = hoy - timedelta(days=7)
    conflictos = obtener_conflictos(desde=inicio.strftime("%Y-%m-%d"), limite=500)
    if not conflictos: return "Sin conflictos registrados en los últimos siete días."
    regiones = defaultdict(list)
    for c in conflictos: regiones[c.get("region") or "Desconocida"].append(c)
    lineas = ["# RESUMEN SEMANAL DE CONFLICTIVIDAD", f"Período: {inicio:%d/%m/%Y} — {hoy:%d/%m/%Y}",
              f"Focos registrados: {len(conflictos)}", "", "## Focos por región"]
    for region, items in sorted(regiones.items(), key=lambda item: -len(item[1])):
        scores = [int(x.get("escalabilidad") or 0) for x in items]
        promedio = sum(scores) / len(scores) if scores else 0
        lineas.append(f"\n### {region}: {len(items)} focos; escalabilidad promedio {promedio:.1f}/10")
        for item in items[:5]: lineas.append(f"- {item.get('municipio')}: {item.get('problematica') or item.get('titulo')}")
    alertas = [c for c in conflictos if c.get("requiere_alerta")]
    lineas.extend(["", f"## Alertas estimadas (score ≥ 7): {len(alertas)}"])
    for a in alertas[:10]: lineas.append(f"- {a.get('municipio')}: {a.get('titulo')}")
    return "\n".join(lineas)

def generar_informe_mensual(mes=None, anio=None):
    hoy = datetime.now()
    desde = hoy - timedelta(days=30)
    conflictos = obtener_conflictos(desde=desde.strftime("%Y-%m-%d"), limite=1000)
    temas = Counter(c.get("tipo") or "otro" for c in conflictos)
    municipios = Counter(c.get("municipio") or "Sin confirmar" for c in conflictos)
    provincias = Counter(c.get("provincia") or "Sin confirmar" for c in conflictos)
    lineas = ["# INFORME MENSUAL DE CONFLICTIVIDAD", f"Período móvil de 30 días hasta {hoy:%d/%m/%Y}",
              f"Focos registrados: {len(conflictos)}", "", "## Temas frecuentes"]
    lineas.extend(f"- {k}: {v}" for k,v in temas.most_common(10))
    lineas.extend(["", "## Municipios con más registros"])
    lineas.extend(f"- {k}: {v}" for k,v in municipios.most_common(10))
    lineas.extend(["", "## Provincias con más registros"])
    lineas.extend(f"- {k}: {v}" for k,v in provincias.most_common(10))
    return "\n".join(lineas)
