import json
import os
from contextlib import asynccontextmanager
from datetime import timezone
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.clickhouse import create_events_table, get_clickhouse_client
from app.schemas import AnalyticsEvent, AnalyticsEventResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_events_table()
    yield


app = FastAPI(
    title="Villa Agency Analytics Service",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8080,http://localhost:8100",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health_check():
    client = get_clickhouse_client()

    try:
        client.command("SELECT 1")
    finally:
        client.close()

    return {
        "status": "healthy",
        "clickhouse": "connected",
    }


@app.post(
    "/events",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(event: AnalyticsEvent, request: Request):
    event_id = uuid4()
    client = get_clickhouse_client()

    try:
        client.insert(
            "frontend_events",
            [
                [
                    event_id,
                    event.event_type,
                    event.page,
                    event.property_id,
                    event.session_id,
                    event.occurred_at.astimezone(timezone.utc),
                    request.headers.get("user-agent", ""),
                    json.dumps(event.metadata),
                ]
            ],
            column_names=[
                "event_id",
                "event_type",
                "page",
                "property_id",
                "session_id",
                "occurred_at",
                "user_agent",
                "metadata_json",
            ],
        )
    finally:
        client.close()

    return {
        "event_id": event_id,
        "status": "stored",
    }


@app.get("/metrics/summary")
def get_metrics_summary():
    client = get_clickhouse_client()

    try:
        result = client.query(
            """
            SELECT event_type, count() AS event_count
            FROM frontend_events
            GROUP BY event_type
            ORDER BY event_count DESC
            """
        )
    finally:
        client.close()

    return [
        {
            "event_type": row[0],
            "event_count": row[1],
        }
        for row in result.result_rows
    ]
