# cs2032-api-attendance

> Proyecto del curso **CS2032 – Cloud Computing** · UTEC

API **serverless** del sistema de asistencia del curso. Gestiona instructores, cursos y sesiones, genera el QR de cada sesión y valida el registro de asistencia de los alumnos (correo UTEC, vigencia de la sesión y ubicación dentro del campus).

La consumen:

- [cs2032-web-admin](https://github.com/Maykol-Morales/cs2032-web-admin) — panel de instructores · https://admin.cs2032.com
- [cs2032-web-attendance](https://github.com/Maykol-Morales/cs2032-web-attendance) — registro de asistencia · https://attendance.cs2032.com

## Arquitectura

```
admin.cs2032.com ──┐                       ┌─ λ instructor ─┐
                   ├─► API Gateway ────────┼─ λ course ─────┼─► DynamoDB
attendance.cs2032 ─┘   (API key + plan)    ├─ λ session ────┤   (instructors, courses, sessions)
                                           └─ λ attendance ─┘
```

- **AWS Lambda** (Python 3.13): una función por recurso
- **API Gateway**: todos los endpoints son privados (header `x-api-key`), con usage plan (5 req/s, ráfaga de 10, 500 req/mes)
- **DynamoDB** (on-demand): tablas `instructors`, `courses` y `sessions`
- **Serverless Framework** + `serverless-python-requirements`
- `qrcode` + `pillow` para el QR · `haversine` para validar la distancia al campus

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/instructor` | Registra un instructor (`{ "email": ... }`) |
| `GET` | `/instructor/all` | Lista instructores |
| `GET` | `/instructor/{email}` | Verifica si un correo es instructor (`404` si no) |
| `DELETE` | `/instructor/{email}` | Elimina un instructor |
| `POST` | `/course` | Crea un curso |
| `GET` | `/course/all` | Lista cursos |
| `GET` | `/course/{id}` | Obtiene un curso |
| `DELETE` | `/course/{id}` | Elimina un curso |
| `POST` | `/session` | Crea una sesión y devuelve su QR (PNG en base64) |
| `GET` | `/session/all?course={course_id}` | Lista las sesiones de un curso |
| `DELETE` | `/session/{id}?course={course_id}` | Elimina una sesión |
| `POST` | `/attendance` | Registra la asistencia de un alumno |

### Respuestas de `POST /attendance`

| Código | Significado |
|---|---|
| `200` | Asistencia registrada |
| `400` | El correo no es `@utec.edu.pe` |
| `401` | Sesión no encontrada |
| `402` | Asistencia ya registrada |
| `403` | Sesión expirada |
| `404` | Ubicación fuera del campus (sesiones presenciales, radio de 500 m) |

El QR de cada sesión apunta a `FRONT_END_URL?course={course_id}&session={session_id}`.

## Despliegue

Requisitos: Node.js 18+, Serverless Framework, Docker (para empaquetar dependencias de Python) y credenciales de AWS.

```bash
npm install          # plugin serverless-python-requirements
sls deploy           # crea Lambdas, tablas DynamoDB, API Gateway y API key
sls info --verbose   # muestra la URL base y la API key
sls remove           # elimina todos los recursos
```

La URL base y la API key son las que usan los frontends en `PUBLIC_BACK_END_URL` y `PUBLIC_BACK_END_KEY`.

Los orígenes CORS (`admin.cs2032.com` y `attendance.cs2032.com`) y la URL del QR (`FRONT_END_URL`) se configuran en `serverless.yml` y en `make_response` de cada handler.

## Estructura

```
├── instructor.py    # λ instructores
├── course.py        # λ cursos
├── session.py       # λ sesiones + generación de QR
├── attendance.py    # λ registro de asistencia (correo, expiración, ubicación)
├── serverless.yml   # funciones, rutas, tablas, API key y usage plan
├── requirements.txt
└── package.json     # plugin de Serverless
```

## Autores

Sebastián Urbina y Maykol Morales

## Licencia

[Apache 2.0](LICENSE)
