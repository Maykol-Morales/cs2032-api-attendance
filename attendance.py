import json
import os
import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from haversine import Unit, haversine

# DynamoDB
dynamodb = boto3.resource("dynamodb")
SESSIONS_TABLE = dynamodb.Table(os.environ["SESSIONS_TABLE_NAME"])
ALLOWED_ORIGIN = os.environ["ALLOWED_ORIGIN"]

# JSON encoder para Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 else int(o)
        return super().default(o)

# 🔵 Distancia (usando haversine)
UTEC_LOCATION = (-12.135230309407161, -77.02216698004771)

def calculate_distance(latitude, longitude):
    student_location = (latitude, longitude)
    distance = haversine(UTEC_LOCATION, student_location, unit=Unit.METERS)
    return distance <= 500

# 🔵 Expiración UTC
def is_expired(expire_at: datetime) -> bool:
    now = datetime.now(timezone.utc)
    expire_at_utc = expire_at.astimezone(timezone.utc)
    return now >= expire_at_utc

# 🔵 Respuesta JSON
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

# 🔵 Parse de input
def parse_attendance(body):
    return {
        "student_email": body["student_email"],
        "student_latitude": float(body.get("student_latitude", 0)),
        "student_longitude": float(body.get("student_longitude", 0)),
        "course_id": body["course_id"],
        "session_id": body["session_id"]
    }

# 🔵 Lambda handler
def handler(event, context):
    method = event["httpMethod"]
    path = event["path"]

    try:
        if method == "POST" and path == "/attendance":
            body = json.loads(event["body"])
            data = parse_attendance(body)

            if not data["student_email"].endswith("@utec.edu.pe"):
                return make_response(400, "Missing UTEC")

            response = SESSIONS_TABLE.get_item(
                Key={"course_id": data["course_id"], "id": data["session_id"]}
            )

            session = response.get("Item")
            if not session:
                return make_response(401, "Missing Session")

            if data["student_email"] in session.get("attendees", []):
                return make_response(402, "Already Marked")

            expire_at = datetime.fromisoformat(session["expire_at"])
            if is_expired(expire_at):
                return make_response(403, "Session expired")

            if session.get("in_campus", False):
                if not calculate_distance(
                    data["student_latitude"],
                    data["student_longitude"]
                ):
                    return make_response(404, "Invalid Location")

            # Agregar estudiante de forma atómica: la condición evita duplicados
            # y que dos registros simultáneos se sobrescriban
            try:
                SESSIONS_TABLE.update_item(
                    Key={"course_id": data["course_id"], "id": data["session_id"]},
                    UpdateExpression="SET attendees = list_append(if_not_exists(attendees, :empty), :student)",
                    ConditionExpression="attribute_not_exists(attendees) OR NOT contains(attendees, :email)",
                    ExpressionAttributeValues={
                        ":empty": [],
                        ":student": [data["student_email"]],
                        ":email": data["student_email"]
                    }
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    return make_response(402, "Already Marked")
                raise

            return make_response(200, "Attendance Marked")

        return make_response(404, {"error": "Route not found"})

    except Exception as e:
        return make_response(500, {"error": str(e)})

