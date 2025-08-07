import json
import os
import re
import boto3
import uuid
import base64
from io import BytesIO
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import qrcode

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)

# Inicializar recurso DynamoDB y tabla
dynamodb = boto3.resource("dynamodb")
SESSIONS_TABLE = dynamodb.Table(os.environ["SESSIONS_TABLE_NAME"])
FRONT_END_URL = os.environ.get("FRONT_END_URL")

# Función para respuesta estándar
def make_response(status_code, content):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(content, cls=DecimalEncoder)
    }

# Función para generar QR en base64
def generate_qr_code(url):
    qr = qrcode.make(url)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Normalizar sesión
def parse_session(item):
    return {
        "course_id": item.get("course_id"),
        "course_name": item.get("course_name"),
        "id": item.get("id"),
        "in_campus": item.get("in_campus"),
        "expire_at": item.get("expire_at"),
        "qr_code": item.get("qr_code")
    }

def parse_sessions(items):
    return [parse_session(item) for item in items]


def handler(event, context):
    method = event["httpMethod"]
    path = event["path"]

    try:
        # POST /session
        if method == "POST" and path == "/session":
            body = json.loads(event["body"])

            session_id = str(uuid.uuid4())
            course_id = body.get("course_id")

            if not course_id:
                return make_response(400, {"error": "Missing course_id"})

            body["id"] = session_id
            qr_url = f"{FRONT_END_URL}?course={course_id}&session={session_id}"
            body["qr_code"] = generate_qr_code(qr_url)

            SESSIONS_TABLE.put_item(Item=body)
            return make_response(200, parse_session(body))

        # GET /session/all?course=...
        elif method == "GET" and path == "/session/all":
            params = event.get("queryStringParameters") or {}
            course_id = params.get("course")

            if not course_id:
                return make_response(400, {"error": "Missing course query parameter"})

            response = SESSIONS_TABLE.query(
                KeyConditionExpression=Key("course_id").eq(course_id)
            )
            items = response.get("Items", [])
            return make_response(200, parse_sessions(items))

        # DELETE /session/{id}?course=...
        elif method == "DELETE" and re.match(r"^/session/[^/]+$", path):
            session_id = path.split("/")[-1]
            params = event.get("queryStringParameters") or {}
            course_id = params.get("course")

            if not course_id:
                return make_response(400, {"error": "Missing course query parameter"})

            SESSIONS_TABLE.delete_item(Key={"course_id": course_id, "id": session_id})
            return make_response(200, {"message": "Session deleted"})

        # Ruta no encontrada
        else:
            return make_response(404, {"error": "Route not found"})

    except Exception as e:
        return make_response(500, {"error": str(e)})
