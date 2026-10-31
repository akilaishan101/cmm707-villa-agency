import json
import logging
import os

import boto3


logger = logging.getLogger(__name__)


def invoke_notification(property_id: int, enquiry_count: int) -> bool:
    function_name = os.getenv("NOTIFICATION_FUNCTION_NAME")

    if not function_name:
        logger.info(
            "Lambda not configured: property=%s enquiries=%s",
            property_id,
            enquiry_count,
        )
        return False

    lambda_client = boto3.client("lambda")

    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(
            {
                "property_id": property_id,
                "enquiry_count": enquiry_count,
            }
        ).encode("utf-8"),
    )

    return True
