import json
import os
import re
import boto3
import uuid
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            # Devuelve como int si es entero, float si no
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self).default(o)

# Inicializar recurso DynamoDB y tabla
dynamodb = boto3.resource("dynamodb")
COURSES_TABLE = dynamodb.Table(os.environ["COURSES_TABLE_NAME"])
ALLOWED_ORIGIN = os.environ["ALLOWED_ORIGIN"]


# Función para respuesta estándar
def make_response(status_code: int, content: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key"
        },
        "body": json.dumps(content, cls=DecimalEncoder)
    }

# Normalizar curso
def parse_course(item):
    return {
        "name": item.get("name"),
        "students": item.get("students")
    }

def parse_courses(items):
    return [parse_course(item) for item in items]


def handler(event, context):
    method = event["httpMethod"]
    path = event["path"]

    try:
        # POST /course
        if method == "POST" and path == "/course":
            body = json.loads(event["body"])

            course_id = str(uuid.uuid4())
            body["id"] = course_id

            COURSES_TABLE.put_item(Item=body)
            return make_response(200, parse_course(body))

        # GET /course/all
        elif method == "GET" and path == "/course/all":
            response = COURSES_TABLE.scan()
            items = response.get("Items", [])
            return make_response(200, parse_courses(items))

        # GET /course/{id}
        elif method == "GET" and re.match(r"^/course/[^/]+$", path):
            course_id = path.split("/")[-1]
            response = COURSES_TABLE.get_item(Key={"id": course_id})
            item = response.get("Item")
            if not item:
                return make_response(404, {"error": "Course not found"})
            return make_response(200, parse_course(item))

        # DELETE /course/{id}
        elif method == "DELETE" and re.match(r"^/course/[^/]+$", path):
            course_id = path.split("/")[-1]
            COURSES_TABLE.delete_item(Key={"id": course_id})
            return make_response(200, {"message": "Course deleted"})

        # Ruta no encontrada
        else:
            return make_response(404, {"error": "Route not found"})

    except Exception as e:
        return make_response(500, {"error": str(e)})
