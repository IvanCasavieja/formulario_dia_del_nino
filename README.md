# Formulario Día del Niño — Tienda Inglesa

Landing + formulario de inscripción para la campaña de Día del Niño: los padres suben
un video corto de su hijo/a para participar en un sorteo. Pensado para recibir tráfico
real de pauta paga desde el día uno.

## Arquitectura

- **Frontend público** (`/frontend`): Next.js (App Router) → Vercel. Landing +
  formulario de inscripción. Es lo único que ve un padre/madre.
- **Panel de admin** (`/admin`): Next.js (App Router) separado → su propio proyecto de
  Vercel (dominio/subdominio distinto del formulario público). Solo lo usa el equipo
  de marketing para revisar los videos marcados para revisión manual. Es intencional
  que sea una app aparte y no rutas `/admin/*` dentro del sitio público: separa por
  completo la superficie pública de la interna, aunque ambas comparten el mismo
  backend.
- **Backend** (`/backend`): FastAPI → Render (`web` + `worker` + `cron`, ver `render.yaml`).
  Ambos frontends le hablan a la misma API.
- **Storage de video**: Cloudflare R2 (S3-compatible). El navegador sube el video
  directo a R2 con una URL pre-firmada — nunca pasa por el backend.
- **Base de datos**: PostgreSQL.
- **Cola**: Redis + RQ, para el procesamiento de moderación en background (un worker
  separado del proceso web).
- **Moderación**: se extraen 4-5 frames del video con `ffmpeg` y se corren por AWS
  Rekognition (`DetectModerationLabels`, API de imagen) — nunca se copia el video a un
  bucket S3 de AWS.
- **Validaciones reales de duración/tamaño/formato ocurren en el worker**, no solo en
  el navegador: una URL pre-firmada de PUT no puede hacer cumplir un tamaño máximo por
  sí sola, así que el navegador es solo la primera línea de defensa (para no hacerle
  perder tiempo de upload a nadie), y el worker vuelve a validar con `ffprobe` sobre el
  archivo real después de subido.
- `/shared/validationConstants.json` es la única fuente de verdad para los límites
  (60s, 200MB, tipos de archivo permitidos): tanto el backend (`app/shared_constants.py`)
  como el frontend (`lib/validationConstants.ts`) lo leen directamente, para que nunca
  queden desincronizados.
- **Salesforce Marketing Cloud**: apenas se confirma la subida del video, se dispara un
  job en background (`app/worker/salesforce_tasks.py`) que inserta una fila en una Data
  Extension vía la REST API de Marketing Cloud (`app/salesforce.py`). Es *best-effort*:
  nunca bloquea el formulario ni la moderación; si falla (reintenta unas veces), queda
  registrado en `salesforce_sync_error` y visible en el panel de admin para reintentar a
  mano. Apagado por defecto (`SFMC_ENABLED=false`) hasta que existan credenciales reales
  — ver "Variables de entorno" y "Notas operativas" más abajo. El endpoint/payload de la
  API de Marketing Cloud se armó siguiendo la documentación pública de Salesforce, pero
  nunca se probó contra un tenant real (no había credenciales al construirlo) — conviene
  validarlo con un caso de prueba real antes de confiar en él en producción.

## Requisitos para desarrollo local

- Python 3.12+
- Node.js 20+
- Docker (para `docker-compose` con Postgres + Redis locales) — opcional si ya tenés
  Postgres/Redis corriendo de otra forma.
- `ffmpeg` instalado localmente si vas a correr el worker fuera de Docker (`ffmpeg -version`).

## Variables de entorno

Copiar [backend/.env.example](backend/.env.example) a `backend/.env` y completar:

| Variable | Qué es |
|---|---|
| `DATABASE_URL` | Connection string de Postgres |
| `REDIS_URL` | Connection string de Redis (cola RQ + rate limiting) |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Credenciales de un API token de Cloudflare R2 con permisos de lectura/escritura sobre el bucket |
| `R2_ENDPOINT_URL` | `https://<account_id>.r2.cloudflarestorage.com` |
| `R2_BUCKET_NAME` | Bucket donde se guardan los videos |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | Credenciales de un usuario de IAM **solo** para Rekognition (ver política abajo) |
| `UPLOAD_TOKEN_SECRET` | Secreto para firmar el JWT de subida (`python backend/scripts/generate_secret.py`) |
| `ADMIN_JWT_SECRET` | Secreto para firmar la sesión de admin — **distinto** del anterior |
| `ADMIN_PASSWORD_HASH` | Hash bcrypt de la contraseña de admin (`python backend/scripts/generate_admin_password_hash.py`) |
| `CORS_ALLOW_ORIGINS` | Origen(es) del frontend permitidos, separados por coma (ej. `https://diadelnino.tiendainglesa.com.uy`) |
| `SFMC_ENABLED` | `false` hasta tener credenciales reales de Marketing Cloud — con `false` el resto de las `SFMC_*` puede quedar vacío |
| `SFMC_SUBDOMAIN` / `SFMC_CLIENT_ID` / `SFMC_CLIENT_SECRET` / `SFMC_ACCOUNT_ID` | Credenciales del "Installed Package" (API Integration, server-to-server) creado en Marketing Cloud |
| `SFMC_DATA_EXTENSION_KEY` | External Key de la Data Extension donde se insertan las inscripciones |

El resto de las variables (`RATE_LIMIT_*`, `MODERATION_*`, TTLs) tienen defaults
razonables en `backend/app/config.py` — no hace falta tocarlas para levantar el proyecto.

Para cada frontend (son proyectos separados, cada uno con su propio `.env.local`):
`frontend/.env.local` y `admin/.env.local`, ambos con
`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (o la URL del backend desplegado en
Render) — ver `frontend/.env.local.example` y `admin/.env.local.example`.

`CORS_ALLOW_ORIGINS` en el backend tiene que incluir el origen de **los dos**
frontends (formulario público + panel de admin), separados por coma, ya que vas a
tener dos dominios distintos hablándole a la misma API.

## Correr en local

### Backend + Postgres + Redis vía Docker

```bash
cd backend
docker compose up --build
```

Después, aplicar las migraciones (una sola vez / cada vez que cambie el esquema):

```bash
cd backend
source .venv/Scripts/activate  # o el venv que uses
alembic upgrade head
```

### Backend sin Docker

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
# en otra terminal, el worker:
python -m app.worker.run
```

### Tests del backend

```bash
cd backend
pytest
```

### Frontend público (formulario)

```bash
cd frontend
npm install
npm run dev
```

### Panel de admin

```bash
cd admin
npm install
npm run dev  # por defecto en :3000 también - correr uno de los dos a la vez, o cambiar el puerto de uno con -p
```

Generar la contraseña de admin localmente con `python backend/scripts/generate_admin_password_hash.py`
y ponerla en `backend/.env` como `ADMIN_PASSWORD_HASH` antes de probar el login.

## Despliegue

### Backend (Render)

`render.yaml` en la raíz define los 4 servicios: `web`, `worker`, un `cron` (limpieza
de inscripciones abandonadas) y la base Postgres, más un Redis. Todos comparten
`backend/Dockerfile` (necesario porque `ffmpeg` no está disponible en el buildpack
nativo de Python de Render). Al importar el blueprint, Render va a pedir completar las
variables marcadas `sync: false` (credenciales de R2/AWS, secretos, `CORS_ALLOW_ORIGINS`).

### Frontends (Vercel)

Son **dos proyectos de Vercel separados**, ambos apuntando a este mismo repo pero con
"Root Directory" distinto:

- Proyecto 1 → Root Directory `frontend` → el formulario público, en el subdominio que
  asigne Tienda Inglesa.
- Proyecto 2 → Root Directory `admin` → el panel de revisión, en un subdominio interno
  (ej. `admin-diadelnino.vercel.app` o similar) — no necesita ser un dominio "lindo",
  nadie externo debería llegar a esta URL.

En ambos, configurar `NEXT_PUBLIC_API_BASE_URL` apuntando a la URL del backend en
Render.

### Subdominio de Tienda Inglesa

Cuando Tienda Inglesa asigne el subdominio final para el formulario: apuntarlo al
proyecto de Vercel del `frontend`, y actualizar `CORS_ALLOW_ORIGINS` en Render con ese
dominio **y** con el dominio del panel de admin (el default de
`CORS_ALLOW_ORIGIN_REGEX` ya cubre cualquier `*.vercel.app`, pero no un dominio
propio).

## Pasos manuales que no se pueden automatizar desde acá

Estos requieren acceso a las consolas de Cloudflare/AWS/Render/Vercel — no hay
credenciales en este entorno para hacerlos:

1. **Crear el bucket de R2** y un API token con permisos de lectura/escritura sobre
   ese bucket únicamente.
2. **Configurar CORS del bucket de R2** para permitir el `PUT` directo desde el
   navegador. JSON a aplicar (reemplazar por el/los dominio(s) reales):
   ```json
   [
     {
       "AllowedOrigins": [
         "https://<dominio-de-tienda-inglesa>",
         "https://<proyecto>.vercel.app",
         "http://localhost:3000"
       ],
       "AllowedMethods": ["PUT"],
       "AllowedHeaders": ["Content-Type"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3000
     }
   ]
   ```
3. **Crear un usuario de IAM en AWS** solo para Rekognition, con esta política de
   mínimo privilegio (el `Resource: "*"` es correcto acá — Rekognition no soporta
   scoping por recurso en esta API):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["rekognition:DetectModerationLabels"],
         "Resource": "*"
       }
     ]
   }
   ```
4. **Generar los secretos y el hash de la contraseña de admin** (scripts en
   `backend/scripts/`) y cargarlos como variables de entorno en Render — nunca en el
   repo.
5. **Importar `render.yaml` como Blueprint en Render** y completar las variables
   `sync: false`.
6. **Conectar el repo a Vercel dos veces** (dos proyectos, uno con Root Directory
   `frontend` y otro con Root Directory `admin`), configurar `NEXT_PUBLIC_API_BASE_URL`
   en ambos, y más adelante apuntar el subdominio que asigne Tienda Inglesa al proyecto
   del `frontend`.

## Notas operativas

- El texto legal del checkbox de términos y condiciones / autorización de imagen del
  menor es un **placeholder** (`frontend/components/RegistrationForm/ConsentCheckbox.tsx`)
  — el equipo legal de Tienda Inglesa debe reemplazarlo antes de salir a producción.
- El panel de admin (`/admin`, proyecto separado) usa una única contraseña compartida
  (no hay cuentas de usuario) — pensado para un equipo chico de marketing revisando una
  campaña puntual. Al ser una app separada de la pública, conviene no indexarla ni
  enlazarla desde ningún lado público (ya tiene `robots: noindex` seteado).
- Los videos marcados `needs_review` por Rekognition requieren aprobación manual desde
  el panel de admin; los marcados `rejected` o `approved` son automáticos según los
  umbrales de confianza configurados (`MODERATION_REJECT_CONFIDENCE` /
  `MODERATION_REVIEW_CONFIDENCE` en `backend/app/config.py`).
- Retención de datos: los registros (aprobados, rechazados o lo que sea) quedan
  indefinidamente en Postgres — no hay borrado automático, según confirmaron. Además se
  sincronizan a Salesforce Marketing Cloud (ver arriba).
- Selección y notificación del ganador del sorteo es 100% manual, por fuera de este
  proyecto (celular/correo) — no hay nada construido para eso, a propósito.
- Para habilitar el envío a Salesforce: crear el "Installed Package" en Marketing Cloud,
  la Data Extension con las columnas que espera `app/worker/salesforce_tasks.py`
  (`SubmissionId`, `ParentFirstName`, `ParentLastName`, `ParentCedula`, `ParentEmail`,
  `ParentPhone`, `ChildFullName`, `ChildCedula`, `Status`, `SubmittedAt` — todos string),
  cargar las credenciales, y poner `SFMC_ENABLED=true`. Si la Data Extension real usa
  otros nombres de columna, el único lugar que hay que tocar es `_submission_to_de_fields`
  en ese archivo.
