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
       TITLE, TOOL_VERSION, DISPOSITION, UPDATE_TIME
FROM TB_EPISODE
WHERE EPISODE_ID=%s
""".strip()

_BY_NAMESPACE_SQL = """
SELECT EPISODE_ID, BUSINESS_EPISODE_ID, EPISODE_NAMESPACE, SERIES_ID,
       TITLE, TOOL_VERSION, DISPOSITION, UPDATE_TIME
FROM TB_EPISODE
WHERE EPISODE_NAMESPACE=%s
ORDER BY UPDATE_TIME DESC, EPISODE_ID DESC
LIMIT 1
""".strip()

_ALL_NAMESPACES_SQL = """
SELECT EPISODE_NAMESPACE
FROM TB_EPISODE
WHERE EPISODE_NAMESPACE <> ''
ORDER BY EPISODE_NAMESPACE ASC
""".strip()

_UPDATE_DISPOSITION_SQL = """
UPDATE TB_EPISODE
SET DISPOSITION=%s
WHERE EPISODE_ID=%s AND DISPOSITION=%s
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
        return self._decode(self.connection.query_one(_GET_SQL, (episode_id,)))

    def get_by_namespace(self, episode_namespace: str) -> dict | None:
        return self._decode(
            self.connection.query_one(_BY_NAMESPACE_SQL, (str(episode_namespace),))
        )

    def list_namespaces(self) -> list[str]:
        rows = self.connection.query_all(_ALL_NAMESPACES_SQL)
        result = []
        for row in rows:
            value = row.get("EPISODE_NAMESPACE") or row.get("episode_namespace")
            if value:
                result.append(str(value))
        return result

    def update_disposition(
        self, episode_id: str, target: str, *, expected: str = "ACTIVE"
    ) -> None:
        affected = self.connection.execute(
            _UPDATE_DISPOSITION_SQL,
            (str(target), str(episode_id), str(expected)),
        )
        if affected != 1:
            raise RuntimeError(
                f"EPISODE_DISPOSITION_CONFLICT: episode={episode_id}; expected={expected}"
            )

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
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
            "update_time": row.get("UPDATE_TIME") or row.get("update_time"),
        }
