import json
import os
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import boto3


s3 = boto3.client("s3")
notification_bucket = os.environ["NOTIFICATION_BUCKET"]
property_service_url = os.environ["PROPERTY_SERVICE_URL"].rstrip("/")


def get_assigned_agent_id(property_id: int) -> int:
    request = Request(
        f"{property_service_url}/properties/{property_id}",
        headers={"Accept": "application/json"},
    )

    with urlopen(request, timeout=5) as response:
        property_record = json.load(response)

    assigned_agent_id = property_record.get("assigned_agent_id")
    if assigned_agent_id is None:
        raise ValueError(f"Property {property_id} has no assigned agent")

    return int(assigned_agent_id)


def lambda_handler(event, context):
    timestamp = datetime.now(timezone.utc)
    property_id = int(event["property_id"])
    total_enquiries = int(event["enquiry_count"])
    assigned_agent_id = get_assigned_agent_id(property_id)

    notification = {
        "type": "HIGH_PROPERTY_INTEREST",
        "property_id": property_id,
        "assigned_agent_id": assigned_agent_id,
        "total_enquiries": total_enquiries,
        "message": "Property enquiry count exceeded ten.",
        "created_at": timestamp.isoformat(),
    }

    object_key = (
        f"notifications/property-{property_id}/"
        f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    )

    s3.put_object(
        Bucket=notification_bucket,
        Key=object_key,
        Body=json.dumps(notification),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )

    return {
        "statusCode": 200,
        "body": json.dumps(notification),
    }
