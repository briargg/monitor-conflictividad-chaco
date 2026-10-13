import os
import requests
from database import guardar_alerta

UMBRAL_ALERTA = 7

def evaluar_alerta(analisis: dict, noticia: dict):
    esc = analisis.get("escalabilidad") or {}
    score = int(esc.get("score") or 0)
    if score >= UMBRAL_ALERTA or analisis.get("requiere_alerta_inmediata"):
        return {
            "tipo": "ALERTA_INMEDIATA", "municipio": analisis.get("municipio") or noticia.get("municipio"),
            "provincia": analisis.get("provincia") or noticia.get("provincia"),
            "problematica": analisis.get("problematica") or "Sin descripción",
            "escalabilidad": score, "fase": analisis.get("fase") or "Sin confirmar",
            "actores": analisis.get("actores") or [], "fuente": noticia.get("fuente"),
            "link": noticia.get("link"), "factores": esc.get("factores") or []
        }
    return None

def enviar_alerta_telegram(alerta: dict, conflicto_id: int | None = None):
    guardar_alerta(conflicto_id, alerta["municipio"], alerta["escalabilidad"], alerta["problematica"])
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram no configurado; alerta guardada en SQLite.")
        return
    actores = "\n".join(f"• {a.get('nombre','Actor no especificado')} ({a.get('rol','sin rol')})" for a in alerta["actores"][:5])
    mensaje = (
        f"🚨 ALERTA — {alerta['municipio']}\n\n"
        f"Problemática: {alerta['problematica']}\nEscalabilidad: {alerta['escalabilidad']}/10\n"
        f"Fase estimada: {alerta['fase']}\nActores mencionados: {actores or 'No identificados'}\n"
        f"Fuente: {alerta.get('fuente') or 'No indicada'}\n{alerta.get('link') or ''}\n\n"
        "Estimación automatizada basada en información pública; requiere verificación humana."
    )
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mensaje, "disable_web_page_preview": True}, timeout=10
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"Error enviando alerta a Telegram: {exc}")
