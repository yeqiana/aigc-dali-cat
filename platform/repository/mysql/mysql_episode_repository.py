from __future__ import annotations


_UPSERT_SQL = """
INSERT INTO TB_EPISODE (
    EPISODE_ID, BUSINESS_EPISODE_ID, EPISODE_NAMESPACE, SERIES_ID,
    TITLE, TOOL_VERSION, DISPOSITION
) VALUES (%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    BUSINESS_EPISODE_ID=VALUES(BUSINESS_EPISODE_ID),
    EPISODE_NAMESPACE=VALUES(EPISODE_NAMESPACE),
    SERIES_ID=VALUES(SERIES_ID),
    TITLE=VALUES(TITLE),
    TOOL_VERSION=VALUES(TOOL_VERSION),
    DISPOSITION=VALUES(DISPOSITION)
""".strip()

_GET_SQL = """
SELECT EPISODE_ID, BUSINESS_EPISODE_ID, EPISODE_NAMESPACE, SERIES_ID,
       TITLE, TOOL_VERSION, DISPOSITION
FROM TB_EPISODE
WHERE EPISODE_ID=%s
""".strip()


class MySqlEpisodeRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> None:
        required = ("episode_id", "business_episode_id", "episode_namespace", "title")
        missing = [key for key in required if record.get(key) in (None, "")]
        if missing:
            raise ValueError("episode row missing required fields: " + ", ".join(missing))
        self.connection.execute(
            _UPSERT_SQL,
            (
                record["episode_id"],
                record["business_episode_id"],
                record["episode_namespace"],
                record.get("series_id"),
                record["title"],
                record.get("tool_version"),
                record.get("disposition") or "ACTIVE",
            ),
        )

    def get(self, episode_id: str) -> dict | None:
        row = self.connection.query_one(_GET_SQL, (episode_id,))
        if not row:
            return None
        return {
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "business_episode_id": row.get("BUSINESS_EPISODE_ID") or row.get("business_episode_id"),
            "episode_namespace": row.get("EPISODE_NAMESPACE") or row.get("episode_namespace"),
            "series_id": row.get("SERIES_ID") or row.get("series_id"),
            "title": row.get("TITLE") or row.get("title"),
            "tool_version": row.get("TOOL_VERSION") or row.get("tool_version"),
            "disposition": row.get("DISPOSITION") or row.get("disposition"),
        }
