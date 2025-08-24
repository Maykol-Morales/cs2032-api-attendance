import json
import re
import os
import boto3
from boto3.dynamodb.conditions import Key

# Inicializa DynamoDB y la tabla
dynamodb = boto3.resource("dynamodb")
INSTRUCTORS_TABLE = dynamodb.Table(os.environ["INSTRUCTORS_TABLE_NAME"])


# Función para responder con formato API Gateway
def make_response(status_code: int, content: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://admin.cs2032.com",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key"
        },
        "body": json.dumps(content)
    }

# Normaliza el instructor (puedes ajustar si quieres más validaciones)
def parse_instructor(item):
    return {
        "email": item.get("email")
    }

def parse_instructors(items):
    return [parse_instructor(item) for item in items]


def handler(event, context):
    method = event["httpMethod"]
    path = event["path"]

    try:
        # POST /instructor
        if method == "POST" and path == "/instructor":
            body = json.loads(event["body"])
            INSTRUCTORS_TABLE.put_item(Item=body)
            return make_response(200, parse_instructor(body))

        # GET /instructor/all
        elif method == "GET" and path == "/instructor/all":
            response = INSTRUCTORS_TABLE.scan()
            items = response.get("Items", [])
            return make_response(200, parse_instructors(items))

        # GET /instructor/{email}
        elif method == "GET" and re.match(r"^/instructor/[^/]+$", path):
            email = path.split("/")[-1]
            response = INSTRUCTORS_TABLE.get_item(Key={"email": email})
            item = response.get("Item")

            if not item:
                return make_response(404, {"error": "Instructor not found"})
            return make_response(200, parse_instructor(item))

        # DELETE /instructor/{email}
        elif method == "DELETE" and re.match(r"^/instructor/[^/]+$", path):
            email = path.split("/")[-1]
            INSTRUCTORS_TABLE.delete_item(Key={"email": email})
            return make_response(200, {"message": "Instructor deleted"})

        else:
            return make_response(404, {"error": "Route not found"})

    except Exception as e:
        return make_response(500, {"error": str(e)})
