import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "data" / "conflictos.db")))

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conflictos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                municipio TEXT NOT NULL, provincia TEXT, region TEXT,
                titulo TEXT NOT NULL, link TEXT UNIQUE, fuente TEXT,
                fecha_noticia TEXT, fecha_analisis TEXT DEFAULT CURRENT_TIMESTAMP,
                problematica TEXT, tipo TEXT, escalabilidad INTEGER DEFAULT 0,
                fase TEXT, requiere_alerta INTEGER DEFAULT 0,
                actores_json TEXT DEFAULT '[]', factores_json TEXT DEFAULT '[]'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conflicto_id INTEGER, timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                municipio TEXT, escalabilidad INTEGER, problematica TEXT,
                enviada INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_municipio ON conflictos(municipio)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_provincia ON conflictos(provincia)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON conflictos(fecha_analisis)")

def guardar_conflicto(noticia: dict, analisis: dict) -> int | None:
    esc = analisis.get("escalabilidad") or {}
    actores = analisis.get("actores") or []
    factores = esc.get("factores") or []
    with _connect() as conn:
        cur = conn.execute("""
            INSERT OR IGNORE INTO conflictos
            (municipio, provincia, region, titulo, link, fuente, fecha_noticia,
             problematica, tipo, escalabilidad, fase, requiere_alerta,
             actores_json, factores_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analisis.get("municipio") or noticia.get("municipio") or "Sin municipio",
            analisis.get("provincia") or noticia.get("provincia"),
            analisis.get("region"), noticia.get("titulo") or "Sin título",
            noticia.get("link"), noticia.get("fuente"), noticia.get("fecha"),
            analisis.get("problematica"), analisis.get("tipo"),
            int(esc.get("score") or 0), analisis.get("fase"),
            int(bool(analisis.get("requiere_alerta_inmediata")) or int(esc.get("score") or 0) >= 7),
            json.dumps(actores, ensure_ascii=False), json.dumps(factores, ensure_ascii=False)
        ))
        return cur.lastrowid if cur.rowcount else None

def obtener_conflictos(provincia: str = None, municipio: str = None,
                       desde: str = None, limite: int = 100) -> list[dict]:
    query, params = "SELECT * FROM conflictos WHERE 1=1", []
    if provincia:
        query += " AND provincia = ?"; params.append(provincia)
    if municipio:
        query += " AND municipio = ?"; params.append(municipio)
    if desde:
        query += " AND fecha_analisis >= ?"; params.append(desde)
    query += " ORDER BY escalabilidad DESC, fecha_analisis DESC LIMIT ?"
    params.append(max(1, min(int(limite), 500)))
    with _connect() as conn:
        rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    for row in rows:
        for src, dest in (("actores_json", "actores"), ("factores_json", "factores")):
            try: row[dest] = json.loads(row.get(src) or "[]")
            except (ValueError, TypeError): row[dest] = []
    return rows

def guardar_alerta(conflicto_id: int | None, municipio: str, escalabilidad: int, problematica: str):
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO alertas (conflicto_id, municipio, escalabilidad, problematica) VALUES (?, ?, ?, ?)",
            (conflicto_id, municipio, escalabilidad, problematica)
        )
        return cur.lastrowid
