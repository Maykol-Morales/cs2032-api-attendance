# 📡 UTEC Attendance Backend

Este proyecto implementa un backend serverless en AWS para el sistema de asistencia de la Universidad de Ingeniería y Tecnología (UTEC). Utiliza Python, FastAPI, DynamoDB y API Gateway.

---

## 📦 Requisitos

- Python 3.13+
- Node.js 18+
- [Serverless Framework](https://www.serverless.com/framework/docs/getting-started)
- Docker (para empaquetar dependencias Python)
- Cuenta de AWS con IAM Role configurado

---

## 🧪 Instalación local

1. **Clona el repositorio**

```bash
git clone https://github.com/tu-usuario/ServerlessAttendanceBackend.git
cd ServerlessAttendanceBackend
```

2. **Crea y activa el entorno virtual de Python**

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. **Instala las dependencias de Python**

```bash
pip install -r requirements.txt
```

4. **Instala las dependencias de Serverless**

```bash
npm install
```

---

## 🚀 Despliegue en AWS

1. **Configura tus credenciales de AWS**

```bash
aws configure
```

2. **Despliega el backend**

```bash
sls deploy
```

Este comando:

- Creará las funciones Lambda.
- Configurará las tablas DynamoDB.
- Generará las rutas HTTP en API Gateway.

---

## 🧪 Endpoints disponibles

Todos los endpoints están protegidos con API Key.

- `POST /instructor`
- `GET /instructor/all`
- `POST /course`
- `GET /course/all`
- `POST /session`
- `GET /session/all?course={course_id}`
- `DELETE /session/{id}`
- `POST /attendance`

---

## 🌐 CORS

Este backend solo permite solicitudes desde:

- `https://attendance.cs2032.com`
- `https://admin.cs2032.com`

Los subdominios específicos se configuran en `serverless.yml`.

---

## 🧼 Limpieza

Para eliminar todos los recursos creados en AWS:

```bash
sls remove
```

---

## 🧩 Estructura del proyecto

```
├── attendance.py       # Lambda para marcar asistencia
├── course.py           # Lambda para registrar cursos
├── instructor.py       # Lambda para gestionar instructores
├── session.py          # Lambda para crear sesiones
├── serverless.yml      # Configuración principal de Serverless Framework
├── requirements.txt    # Dependencias Python
├── package.json        # Dependencias de Serverless
├── .gitignore          # Archivos ignorados por Git
└── README.md           # Este archivo
```

---

## 🧑‍💻 Autor

Desarrollado por **Sebastián Urbina** y **Maykol Morales**  
📧 sebastian.urbina@utec.edu.pe
📧 maykol.morales@utec.edu.pe
