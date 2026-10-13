import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, guardar_conflicto
from scraper_chaco import buscar_noticias_chaco
from analyzer import analizar_noticia
from alertas import evaluar_alerta, enviar_alerta_telegram

# Los 69 municipios del Chaco
MUNICIPIOS_PRIORITARIOS = [
    "Resistencia", "Barranqueras", "Fontana", "Puerto Vilelas",
    "La Escondida", "Makallé", "Las Palmas", "La Leonesa",
    "Puerto Tirol", "Basail", "Cote Lai", "Colonia Benítez",
    "Colonia Popular", "Charadai", "General Vedia", "Isla del Cerrito",
    "La Verde", "Laguna Blanca", "Lapachito", "Margarita Belén",
    "Puerto Bermejo", "Puerto Eva Perón", "Colonia Elisa",
    "Presidencia Roque Sáenz Peña", "Machagai", "Quitilipi",
    "Presidencia de la Plaza", "Villa Berthet", "Las Garcitas",
    "Villa Ángela", "Coronel Du Graty", "Samuhú", "Enrique Urien",
    "Santa Sylvina", "La Tigra", "San Bernardo",
    "Las Breñas", "Charata", "Corzuela", "General Capdevila",
    "General Pinedo", "Chorotis", "Hermoso Campo", "Gancedo",
    "Juan José Castelli", "Tres Isletas", "Fuerte Esperanza",
    "Misión Nueva Pompeya", "Villa Río Bermejito", "El Sauzalito",
    "Miraflores",
    "General San Martín", "Capitán Solari", "Ciervo Petiso",
    "Colonias Unidas", "La Eduvigis", "Laguna Limpia", "Pampa Almirón",
    "Presidencia Roca", "Pampa del Indio",
    "Pampa del Infierno", "Los Frentones", "Concepción del Bermejo",
    "Taco Pozo", "Campo Largo", "Napenay", "Avia Terai",
]

scheduler = BackgroundScheduler(timezone="America/Argentina/Buenos_Aires")


def procesar_municipio(municipio: str):
    try:
        # max_resultados=2 para no agotar la cuota de Groq
        noticias = buscar_noticias_chaco(
            municipio, max_resultados=2, solo_conflictos=True
        )

        if not noticias:
            return

        print(f"[{municipio}] {len(noticias)} noticias de conflicto")

        for noticia in noticias:
            try:
                analisis = analizar_noticia(noticia)
                conflict_id = guardar_conflicto(noticia, analisis)
                alerta = evaluar_alerta(analisis, noticia)
                if alerta and conflict_id:
                    enviar_alerta_telegram(alerta, conflict_id)
                    print(
                        f"[{municipio}] ⚠ ALERTA: "
                        f"{analisis.get('problematica', '')[:80]}"
                    )
            except Exception as exc:
                print(f"[{municipio}] Error analizando: {exc}")
    except Exception as exc:
        print(f"[{municipio}] Error general: {exc}")


def recoleccion_periodica():
    """Recorre los 69 municipios chaqueños."""
    print(f"\n[{datetime.now()}] === RECOLECCIÓN INICIADA ===")
    print(f"Municipios: {len(MUNICIPIOS_PRIORITARIOS)}")

    for municipio in MUNICIPIOS_PRIORITARIOS:
        procesar_municipio(municipio)

    print(f"[{datetime.now()}] === RECOLECCIÓN FINALIZADA ===\n")


def iniciar_scheduler():
    """Inicia el scheduler si ENABLE_SCHEDULER=true en el .env"""
    init_db()

    if os.getenv("ENABLE_SCHEDULER", "false").lower() != "true":
        print("Scheduler desactivado. Para activarlo: ENABLE_SCHEDULER=true")
        return

    if not scheduler.running:
        # Cada 4 horas (6 rondas/día → ~828 análisis, dentro del límite gratuito de 1,000)
        scheduler.add_job(
            recoleccion_periodica,
            "interval",
            hours=4,
            id="recoleccion",
            replace_existing=True,
            max_instances=1,
        )
        # Primera ejecución inmediata al arrancar
        scheduler.add_job(
            recoleccion_periodica,
            id="recoleccion_inicial",
            replace_existing=True,
        )
        scheduler.start()
        print("✅ Scheduler activo: recolección cada 4 HORAS")
        print(f"   Municipios: {len(MUNICIPIOS_PRIORITARIOS)}")
        print(f"   Modelo: openai/gpt-oss-20b (gratuito)")
        print(f"   Próxima ejecución: {scheduler.get_job('recoleccion').next_run_time}")
        print(f"   Recolección inicial: en curso")