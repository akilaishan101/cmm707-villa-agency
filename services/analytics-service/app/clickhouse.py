import os

import clickhouse_connect
from dotenv import load_dotenv


load_dotenv()


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        database=os.getenv("CLICKHOUSE_DB", "default"),
        secure=os.getenv("CLICKHOUSE_SECURE", "false").lower() == "true",
    )


def create_events_table() -> None:
    client = get_clickhouse_client()

    try:
        client.command(
            """
            CREATE TABLE IF NOT EXISTS frontend_events
            (
                event_id UUID,
                event_type LowCardinality(String),
                page String,
                property_id Nullable(UInt32),
                session_id String,
                occurred_at DateTime64(3, 'UTC'),
                user_agent String,
                metadata_json String,
                received_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            PARTITION BY toYYYYMM(occurred_at)
            ORDER BY (event_type, occurred_at, event_id)
            """
        )
    finally:
        client.close()
