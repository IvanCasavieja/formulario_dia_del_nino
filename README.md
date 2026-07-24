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
- **Backend** (`/backend`): FastAPI → Render, un único servicio `web` (ver
  `render.yaml`). Ambos frontends le hablan a la misma API.
- **No hay base de datos propia, a propósito.** Por requisito explícito, ningún dato
  personal (nombre, cédula, email, teléfono) vive en ningún lado más que en la Data
  Extension de Salesforce Marketing Cloud - ver más abajo. Esto también significa que
  no hay worker ni cron separados: la moderación y el envío a Salesforce corren
  in-process en el mismo servicio web, vía `BackgroundTasks` de FastAPI (ver
  `app/routers/submissions.py` y `app/worker/tasks.py`).
- **Storage de video**: Cloudflare R2 (S3-compatible). El navegador sube el video
  directo a R2 con una URL pre-firmada — nunca pasa por el backend.
- **Salesforce Marketing Cloud es el único almacenamiento persistente del proyecto**
  (`app/salesforce.py`). La Data Extension **Formulario_Video_Nino** (carpeta
  Audiencias Segmentadas > Dia del Nino, external key
  `7CCD02A7-AA66-48EB-94A0-EA93BC09914D`) tiene `Cedula_Nino` (la cédula del menor)
  como **Primary Key** - un mismo niño/a no puede tener dos filas, pero un mismo
  adulto sí puede tener varias (uno por cada hijo/a que anote). Los datos del
  formulario recién se escriben ahí en `confirm_upload`, después de confirmar la
  subida del video - nunca antes. El estado de revisión (`Status`,
  `ModerationResult`, `AdminNotes`, `AdminReviewedBy`) también vive en esa misma DE,
  como columnas adicionales - no hay ningún otro lugar donde trackearlo. El panel de
  admin lee y escribe directo contra la API de Salesforce, no contra una base propia.
  Endpoint y payload ya se verificaron en vivo contra el tenant real
  (`backend/scripts/test_salesforce_sync.py`): el insert/update es por el endpoint
  *async* de Data Extension Rows (`/data/v1/async/dataextensions/key:.../rows`, POST
  inserta, PUT hace upsert por la primary key), con cada item como los valores del
  campo directamente, sin wrapper `"values"` - ver el docstring de `app/salesforce.py`
  para el detalle completo, incluyendo que un `202` no garantiza que la fila se haya
  escrito (hay que consultar el resultado async) y que el Get/`$filter` funciona sobre
  cualquier columna aunque la DE no sea "Sendable".
- **Moderación**: 100% manual. El proceso en background solo revalida
  formato/duración/tamaño con `ffprobe` sobre el archivo real; todo lo que pasa esa
  validación cae en `needs_review` y espera aprobación desde el panel de admin. No hay
  moderación automática de contenido.
- **Validaciones reales de duración/tamaño/formato ocurren en el backend**, no solo en
  el navegador: una URL pre-firmada de PUT no puede hacer cumplir un tamaño máximo por
  sí sola, así que el navegador es solo la primera línea de defensa (para no hacerle
  perder tiempo de upload a nadie), y el backend vuelve a validar con `ffprobe` sobre
  el archivo real después de subido.
- `/shared/validationConstants.json` es la única fuente de verdad para los límites
  (60s, 200MB, tipos de archivo permitidos): tanto el backend (`app/shared_constants.py`)
  como el frontend (`lib/validationConstants.ts`) lo leen directamente, para que nunca
  queden desincronizados.

## Requisitos para desarrollo local

- Python 3.12+
- Node.js 20+
- `ffmpeg` instalado localmente para correr el backend (`ffmpeg -version`) - lo usa la
  validación server-side del video (`ffprobe`).

## Variables de entorno

Copiar [backend/.env.example](backend/.env.example) a `backend/.env` y completar:

| Variable | Qué es |
|---|---|
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Credenciales de un API token de Cloudflare R2 con permisos de lectura/escritura sobre el bucket |
| `R2_ENDPOINT_URL` | `https://<account_id>.r2.cloudflarestorage.com` |
| `R2_BUCKET_NAME` | Bucket donde se guardan los videos |
| `UPLOAD_TOKEN_SECRET` | Secreto para firmar el JWT de subida (`python backend/scripts/generate_secret.py`) |
| `ADMIN_JWT_SECRET` | Secreto para firmar la sesión de admin — **distinto** del anterior |
| `ADMIN_PASSWORD_HASH` | Hash bcrypt de la contraseña de admin (`python backend/scripts/generate_admin_password_hash.py`) |
| `CORS_ALLOW_ORIGINS` | Origen(es) del frontend permitidos, separados por coma (ej. `https://diadelnino.tiendainglesa.com.uy`) |
| `SFMC_ENABLED` | `false` hasta tener credenciales reales de Marketing Cloud — con `false` el resto de las `SFMC_*` puede quedar vacío |
| `SFMC_SUBDOMAIN` / `SFMC_CLIENT_ID` / `SFMC_CLIENT_SECRET` / `SFMC_ACCOUNT_ID` | Credenciales del "Installed Package" (API Integration, server-to-server) creado en Marketing Cloud |
| `SFMC_DATA_EXTENSION_KEY` | External Key de la Data Extension donde se insertan las inscripciones |

El resto de las variables (`RATE_LIMIT_*`, TTLs) tienen defaults razonables en
`backend/app/config.py` — no hace falta tocarlas para levantar el proyecto.

Para cada frontend (son proyectos separados, cada uno con su propio `.env.local`):
`frontend/.env.local` y `admin/.env.local`, ambos con
`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (o la URL del backend desplegado en
Render) — ver `frontend/.env.local.example` y `admin/.env.local.example`.

`CORS_ALLOW_ORIGINS` en el backend tiene que incluir el origen de **los dos**
frontends (formulario público + panel de admin), separados por coma, ya que vas a
tener dos dominios distintos hablándole a la misma API.

## Correr en local

No hace falta Docker ni ninguna base de datos - solo Python y `ffmpeg` instalado.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La moderación y el envío a Salesforce corren en el mismo proceso (vía
`BackgroundTasks`), así que no hace falta levantar nada aparte.

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

`render.yaml` en la raíz define un único servicio `web` (plan `free` por ahora - ver
el comentario TEMP al principio del archivo). Usa `backend/Dockerfile` porque
`ffmpeg` no está disponible en el buildpack nativo de Python de Render. Al importar
el blueprint, Render va a pedir completar las variables marcadas `sync: false`
(credenciales de R2, secretos, `CORS_ALLOW_ORIGINS`, credenciales de Salesforce).

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

Estos requieren acceso a las consolas de Cloudflare/Render/Vercel — no hay
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
3. **Generar los secretos y el hash de la contraseña de admin** (scripts en
   `backend/scripts/`) y cargarlos como variables de entorno en Render — nunca en el
   repo.
4. **Importar `render.yaml` como Blueprint en Render** y completar las variables
   `sync: false`.
5. **Conectar el repo a Vercel dos veces** (dos proyectos, uno con Root Directory
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
- Moderación 100% manual: todo video que pasa la validación server-side
  (formato/duración/tamaño) cae en `needs_review` y espera aprobación desde el panel
  de admin. No hay moderación automática de contenido.
- Retención de datos: los registros (aprobados, rechazados o lo que sea) quedan
  indefinidamente en la Data Extension de Salesforce — no hay borrado automático. No
  hay ninguna otra copia en ningún lado (ver "Arquitectura" más arriba).
- Selección y notificación del ganador del sorteo es 100% manual, por fuera de este
  proyecto (celular/correo) — no hay nada construido para eso, a propósito.
- El destino en Salesforce ya existe: la Data Extension **Formulario_Video_Nino**
  (carpeta Audiencias Segmentadas > Dia del Nino, external key
  `7CCD02A7-AA66-48EB-94A0-EA93BC09914D`), con `Cedula_Nino` como Primary Key.
  `app/salesforce.py` (`build_row_fields`) mapea cada submission a sus columnas reales
  (`Nombre_Adulto`, `Apellido_Adulto`, `EmailAddress`, `Celular`, `Cedula`,
  `Nombre_nino`, `Apellido_nino`, `Cedula_Nino`, `Term_Cond`, más `Status`, `VideoKey`,
  `ModerationResult`, `AdminNotes`, `AdminReviewedBy` para el estado de revisión) — si
  la DE cambia de esquema, ese es el único lugar que hay que tocar.
- Para habilitar el envío a Salesforce: crear el "Installed Package" en Marketing Cloud
  (Setup → Apps → Installed Packages → componente API Integration, tipo
  Server-to-Server, con permiso Read/Write sobre Data Extensions), cargar las
  credenciales (`SFMC_SUBDOMAIN`, `SFMC_CLIENT_ID`, `SFMC_CLIENT_SECRET`,
  `SFMC_DATA_EXTENSION_KEY` con el external key de arriba), y poner
  `SFMC_ENABLED=true`. Para confirmar que tus propias credenciales funcionan antes de
  activarlo en el flujo real, corré `python scripts/test_salesforce_sync.py` desde
  `backend/` (deja una fila obviamente falsa en la DE, con `Cedula_Nino=99999999` -
  borrala a mano después de confirmar que llegó bien).
- Etapa 2 (votación): existe una segunda Data Extension, **de adultos/votación**
  (sendable, external key `803D4CD2-10A3-4A48-93CC-6D095FE705D5`), con `Cedula_Adulto`
  como Primary Key. Cualquiera puede votar (no hace falta haber inscripto un chico en
  la etapa 1) vía `POST /api/votes` (`app/routers/votes.py`); una segunda votación con
  la misma cédula se rechaza con 409 (`HaVotado=true`). Al confirmar una inscripción de
  etapa 1, `routers/submissions.py` también sincroniza (best-effort) los datos de
  contacto del adulto en esta DE, sin tocar el estado de voto — ver el comentario al
  principio de `app/salesforce.py` para el detalle de por qué eso es seguro (upsert
  parcial, no overwrite de fila completa). Variable de entorno:
  `SFMC_ADULTS_DATA_EXTENSION_KEY`. Para validar contra el tenant real antes de confiar
  en esta DE, corré `python scripts/test_adults_sync.py` desde `backend/` (deja una fila
  de prueba con `Cedula_Adulto=88888888` - borrala a mano después). **Falta construir
  la UI de votación en `frontend/`** - el endpoint existe pero todavía no lo llama nadie
  desde el formulario público.
