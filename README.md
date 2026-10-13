# Monitor de Conflictividad Social — Argentina

Aplicación web en español para buscar noticias públicas por municipio, obtener un resumen estructurado con IA, consultar registros históricos en SQLite, visualizar puntos geográficos y generar informes semanales/mensuales.

> **Uso responsable:** el sistema analiza noticias, no personas. Los puntajes son estimaciones automáticas limitadas por la calidad de las fuentes; no son predicciones ni una evaluación de peligrosidad. Verificá cada resultado con la noticia original y criterio humano. No uses el sistema como única base para decisiones sobre personas, comunidades o despliegues operativos.

## Requisitos

- Docker Desktop (recomendado para Windows) **o** Python 3.11+ y Node.js 20+.
- Una clave de Groq para el análisis con IA: https://console.groq.com/keys
- Opcional: bot de Telegram y su chat ID para notificaciones.
- Conexión a Internet para Google News RSS, Georef, OpenStreetMap y Groq.

**Seguridad:** en el texto original se incluyó una clave de Groq. Se omitió deliberadamente de este proyecto. Si esa clave era real, revocala y creá otra. Nunca pegues claves en el código ni las subas a GitHub.

## Opción A — Ejecutar con Docker (más simple)

1. Descomprimí el ZIP.
2. Copiá `backend/.env.example` a `backend/.env`.
3. Abrí `backend/.env` y completá `GROQ_API_KEY` con una clave nueva. Telegram es opcional.
4. Instalá y abrí Docker Desktop.
5. Desde PowerShell, entrá a la carpeta descomprimida (la que contiene `docker-compose.yml`) y ejecutá:

   ```powershell
   docker compose up --build -d
   ```

6. Abrí:
   - Aplicación web: http://localhost:8080
   - API: http://localhost:8000
   - Documentación de API: http://localhost:8000/docs

Para ver registros: `docker compose logs -f backend`. Para detener: `docker compose down`. La base SQLite persiste en un volumen Docker aunque se reconstruyan los contenedores; `docker compose down -v` elimina ese volumen y **borra los datos**.

## Opción B — Ejecutar sin Docker en Windows

### 1. Backend

Instalá Python 3.11 o superior. En PowerShell, desde la carpeta del proyecto:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Editá `backend/.env` y completá `GROQ_API_KEY`. Luego iniciá:

```powershell
uvicorn main:app --reload --port 8000
```

Dejá esa terminal abierta.

### 2. Frontend

Instalá Node.js 20 o superior desde https://nodejs.org. Abrí una segunda terminal de PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Abrí http://localhost:5173. Si PowerShell dice que `node` o `npm` no se reconoce, cerrá y volvé a abrir la terminal después de instalar Node.js. Comprobá con `node -v` y `npm -v`.

## Despliegue en un servidor

El `docker-compose.yml` levanta frontend y backend juntos, por lo que es la opción más directa para un VPS/servidor con Docker. Configurá dominio y HTTPS mediante un proxy inverso (por ejemplo Caddy o Nginx) antes de exponerlo públicamente. No publiques el backend sin autenticación si necesitás restringir quién puede consumir cuota de Groq. Este prototipo no incluye usuarios, contraseñas ni roles.

Para producción se recomienda añadir autenticación, límites de uso, control de costos, copias de seguridad y monitoreo. El scheduler está desactivado por defecto para evitar consumo inesperado de API. Si querés habilitar la recolección automática en el contenedor backend, cambiá `ENABLE_SCHEDULER=true` en `backend/.env` y recreá el servicio. No se recomienda correr múltiples réplicas del backend con el scheduler activo.

## Despliegue web sin servidor propio (Render)

Este proyecto incluye `Dockerfile` y `render.yaml` para que Render construya y ejecute la aplicación en la nube. No necesitás instalar Docker Desktop en tu PC.

1. Creá una cuenta en GitHub y una en https://render.com/.
2. Creá un repositorio nuevo en GitHub y subí el contenido de esta carpeta (incluidos `Dockerfile` y `render.yaml`). No subas `backend/.env` ni claves secretas.
3. En Render, elegí **New + → Blueprint** y conectá el repositorio de GitHub.
4. Render detectará `render.yaml`. Al pedir `GROQ_API_KEY`, ingresá una clave nueva creada en https://console.groq.com/keys. No la compartas ni la guardes en el repositorio.
5. Confirmá la creación y esperá a que el despliegue termine. Render mostrará una dirección `https://...onrender.com`.
6. Abrí esa dirección. Para comprobar la API, agregá `/api/health` al final de la URL; debería devolver `{"estado":"ok"}`.

**Limitaciones del plan gratuito:** el servicio puede suspenderse cuando no se usa y el sistema de archivos no es persistente. En esta configuración, el historial SQLite puede perderse al reiniciar o volver a desplegar. Para conservar el historial de manera confiable, hay que configurar almacenamiento persistente (normalmente un plan pago compatible) o migrar la base a un servicio de base de datos administrado. Confirmá los precios y límites vigentes de Render antes de publicar.

**Seguridad:** esta versión no tiene inicio de sesión ni roles. Cualquier persona que conozca la URL podría utilizar la API y generar consumo de Groq. Usala como demostración pública solamente hasta añadir autenticación y límites de uso. `ENABLE_SCHEDULER` queda desactivado para evitar consumo automático.

## API

- `GET /api/health` — estado básico.
- `GET /api/municipios?provincia=Buenos%20Aires` — municipios y coordenadas de Georef.
- `GET /api/analyze?municipio=San%20Miguel&provincia=Buenos%20Aires&limite=10` — búsqueda y análisis de noticias (usa Groq).
- `GET /api/conflictos?limite=100` — historial.
- `GET /api/resumen-semanal` — resumen de últimos siete días.
- `GET /api/informe-mensual` — resumen móvil de últimos treinta días.

## Limitaciones conocidas

- Google News RSS no garantiza cobertura exhaustiva, exactitud territorial ni disponibilidad permanente.
- La consulta a Groq consume cuota y puede fallar por límites, cambios del modelo o falta de saldo/cuota.
- El análisis se hace sobre metadatos y titulares; no implica que el sistema haya leído o verificado el artículo completo.
- Los municipios se obtienen de la API de Georef. Nombres alternativos o localidades que no sean municipios pueden no encontrar coordenadas.
- SQLite está pensado para una primera versión de bajo volumen, no para despliegues de alta concurrencia.
- El sistema no cuenta con autenticación, autorización ni auditoría de usuarios. No lo expongas directamente a Internet sin añadir esas capas.
