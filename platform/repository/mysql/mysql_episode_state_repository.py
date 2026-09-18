from __future__ import annotations


_INSERT_STATE_SQL = """
INSERT INTO TB_EPISODE_STATE (
    EPISODE_ID, CURRENT_STATE, STATE_VERSION, SOURCE
) VALUES (%s,%s,%s,%s)
""".strip()

_GET_STATE_SQL = """
SELECT EPISODE_ID, CURRENT_STATE, STATE_VERSION, SOURCE, UPDATE_TIME
FROM TB_EPISODE_STATE
WHERE EPISODE_ID=%s
LIMIT 1
""".strip()

_INSERT_HISTORY_SQL = """
INSERT INTO TB_EPISODE_STATE_HIS (
    EPISODE_ID, FROM_STATE, TO_STATE, STATE_VERSION, SOURCE, REASON, CREATE_TIME
) VALUES (%s,%s,%s,%s,%s,%s,%s)
""".strip()

_HISTORY_SQL = """
SELECT HISTORY_ID, EPISODE_ID, FROM_STATE, TO_STATE, STATE_VERSION,
       SOURCE, REASON, CREATE_TIME
FROM TB_EPISODE_STATE_HIS
WHERE EPISODE_ID=%s
ORDER BY STATE_VERSION ASC, HISTORY_ID ASC
""".strip()

_TRANSITION_SQL = """
UPDATE TB_EPISODE_STATE
SET CURRENT_STATE=%s, STATE_VERSION=%s, SOURCE=%s
WHERE EPISODE_ID=%s AND CURRENT_STATE=%s AND STATE_VERSION=%s
""".strip()


class MySqlEpisodeStateRepository:
    """Typed durable authority for canonical Episode stage + stage history."""

    def __init__(self, connection):
        self.connection = connection

    def get(self, episode_id: str) -> dict | None:
        return self._decode_state(
            self.connection.query_one(_GET_STATE_SQL, (str(episode_id),))
        )

    def history(self, episode_id: str) -> list[dict]:
        rows = self.connection.query_all(_HISTORY_SQL, (str(episode_id),))
        return [self._decode_history(row) for row in rows]

    def initialize(
        self,
        episode_id: str,
        current_state: str,
        history: list[dict],
        *,
        source: str,
    ) -> dict:
        if not history:
            raise ValueError("episode state initialization requires non-empty history")
        version = len(history)
        self.connection.execute(
            _INSERT_STATE_SQL,
            (str(episode_id), str(current_state), version, str(source)[:64]),
        )
        previous = None
        for index, entry in enumerate(history, 1):
            state = str(entry.get("state") or "")
            if not state:
                raise ValueError("episode state history entry missing state")
            self.connection.execute(
                _INSERT_HISTORY_SQL,
                (
                    str(episode_id),
                    previous,
                    state,
                    index,
                    str(entry.get("source") or source)[:64],
                    str(entry.get("note") or "")[:500],
                    entry.get("at"),
                ),
            )
            previous = state
        return {
            "episode_id": str(episode_id),
            "current_state": str(current_state),
            "state_version": version,
            "source": str(source)[:64],
        }

    def transition(
        self,
        episode_id: str,
        *,
        expected_state: str,
        expected_version: int,
        target_state: str,
        source: str,
        reason: str,
        at,
    ) -> dict:
        next_version = int(expected_version) + 1
        affected = self.connection.execute(
            _TRANSITION_SQL,
            (
                str(target_state),
                next_version,
                str(source)[:64],
                str(episode_id),
                str(expected_state),
                int(expected_version),
            ),
        )
        if affected != 1:
            raise RuntimeError(
                "EPISODE_STATE_CONFLICT: "
                f"episode={episode_id}; state={expected_state}; version={expected_version}"
            )
        self.connection.execute(
            _INSERT_HISTORY_SQL,
            (
                str(episode_id),
                str(expected_state),
                str(target_state),
                next_version,
                str(source)[:64],
                str(reason or "")[:500],
                at,
            ),
        )
        return {
            "episode_id": str(episode_id),
            "current_state": str(target_state),
            "state_version": next_version,
            "source": str(source)[:64],
        }

    @staticmethod
    def _decode_state(row: dict | None) -> dict | None:
        if not row:
            return None
        return {
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "current_state": row.get("CURRENT_STATE") or row.get("current_state"),
            "state_version": row.get("STATE_VERSION") or row.get("state_version"),
            "source": row.get("SOURCE") or row.get("source"),
            "update_time": row.get("UPDATE_TIME") or row.get("update_time"),
        }

    @staticmethod
    def _decode_history(row: dict) -> dict:
        return {
            "history_id": row.get("HISTORY_ID") or row.get("history_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "from_state": row.get("FROM_STATE") if "FROM_STATE" in row else row.get("from_state"),
            "to_state": row.get("TO_STATE") or row.get("to_state"),
            "state_version": row.get("STATE_VERSION") or row.get("state_version"),
            "source": row.get("SOURCE") or row.get("source"),
            "reason": row.get("REASON") if "REASON" in row else row.get("reason"),
            "create_time": row.get("CREATE_TIME") or row.get("create_time"),
        }
