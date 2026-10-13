import json
import os
from groq import Groq
from dotenv import load_dotenv
from municipios import obtener_region

load_dotenv()

# Modelo actual de Groq (el anterior llama-3.1-8b-instant fue retirado el 16/08/2026)
MODELO = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

PROMPT_SISTEMA = """Sos un analista de conflictividad social del Chaco, Argentina.
Tu tarea es clasificar y ANALIZAR la noticia (no solo describirla). Devolvé JSON válido:

{
  "categoria": "laboral|servicios|clima|vivienda|seguridad|politico|salud|educativo|tierra|otro",
  "subcategoria": "docente|estatal|desalojo|crecida|inseguridad|etc (libre pero breve)",
  "problematica": "qué está pasando concretamente (1-2 oraciones)",
  "municipio": "nombre o Sin confirmar",
  "region": "Región 1|Región 2|...|Sin confirmar",
  "nivel": "bajo|medio|alto|critico",
  "score": 1,
  "puede_escalar": true,
  "tiempo_estimado_escalada": "48-72hs|1 semana|inmediato|no aplica",
  "consecuencia_probable": "qué puede pasar si no se atiende (ej: corte de ruta, paro, toma, emergencia social)",
  "actores": [{"nombre": "actor", "rol": "demandante|autoridad|mediador|opositor"}],
  "fase": "latente|escalada|crisis|dialogo|resuelto",
  "requiere_alerta_inmediata": false
}

REGLAS POR CATEGORÍA:

- laboral: evaluá si puede escalar a paro, movilización o corte. Score alto si hay amenaza de paro.
- servicios: evaluá si puede derivar en protesta vecinal o corte de ruta.
- clima: NO es conflicto per se. Evaluá si puede DERIVAR en emergencia social (evacuados, falta de agua, salud). Score alto si hay riesgo social.
- vivienda: evaluá si puede escalar a violencia, toma o desalojo forzoso.
- seguridad: evaluá si puede derivar en movilización vecinal o justicia por mano propia.
- politico: evaluá si puede generar crisis institucional o movilización.
- salud: evaluá si puede derivar en protesta por falta de insumos.
- educativo: evaluá si puede escalar a toma de escuelas o paro.
- tierra: evaluá si puede escalar a conflicto territorial o violencia.

ESCALA (score):
1-3: bajo, sin indicios de escalada
4-6: medio, conflicto activo pero contenido
7-8: alto, escalada documentada
9-10: crítico, crisis con violencia o toma

requiere_alerta_inmediata = true si score >= 7 O hay evidencia explícita de corte, violencia, toma.

Respondé SOLO con JSON válido. No agregues texto."""


def analizar_noticia(noticia: dict):
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Falta GROQ_API_KEY en backend/.env")

    client = Groq(api_key=key)
    prompt = (
        f"Título: {noticia.get('titulo')}\n"
        f"Medio: {noticia.get('fuente')}\n"
        f"Fecha: {noticia.get('fecha')}\n"
        f"Municipio buscado: {noticia.get('municipio')}\n"
        f"Provincia: Chaco\n"
        f"Enlace: {noticia.get('link')}\n"
        f"Devolvé el JSON solicitado."
    )

    response = client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1200,
    )

    data = json.loads(response.choices[0].message.content)

    # Completar region si falta
    provincia = data.get("provincia") or noticia.get("provincia") or "Chaco"
    data["region"] = data.get("region") or obtener_region(provincia) or "Sin confirmar"

    return data