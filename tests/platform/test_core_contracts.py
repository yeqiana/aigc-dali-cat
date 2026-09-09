from dataclasses import FrozenInstanceError
from datetime import datetime
import unittest

from platform.core.contracts import ArtifactContract, EventContract, TraceContract
from platform.core.enums import ArtifactType, EntityType, EventType, TraceStatus


class CoreContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 9, 9, 16, 0, 0)

    def test_event_contract_records_fact_without_shared_payload(self) -> None:
        first = EventContract(
            event_id="evt_001",
            event_type=EventType.TASK_STARTED,
            aggregate_type=EntityType.TASK,
            aggregate_id="task_001",
            occurred_at=self.now,
            trace_id="trace_001",
            task_id="task_001",
        )
        second = EventContract(
            event_id="evt_002",
            event_type=EventType.TASK_COMPLETED,
            aggregate_type=EntityType.TASK,
            aggregate_id="task_002",
            occurred_at=self.now,
        )

        first.payload["frame"] = "01"

        self.assertEqual(first.payload, {"frame": "01"})
        self.assertEqual(second.payload, {})
        self.assertEqual(first.event_type, EventType.TASK_STARTED)

    def test_trace_contract_describes_one_execution_span(self) -> None:
        trace = TraceContract(
            trace_id="trace_001",
            span_id="span_001",
            operation="image_generation",
            status=TraceStatus.SUCCESS,
            started_at=self.now,
            request_id="req_001",
            episode_id="ep_001",
            task_id="task_001",
            duration_ms=1200,
            outputs={"artifact_id": "artifact_001"},
        )

        self.assertEqual(trace.status, TraceStatus.SUCCESS)
        self.assertEqual(trace.duration_ms, 1200)
        self.assertEqual(trace.outputs["artifact_id"], "artifact_001")

    def test_artifact_contract_indexes_file_without_owning_storage(self) -> None:
        artifact = ArtifactContract(
            artifact_id="artifact_001",
            artifact_type=ArtifactType.IMAGE,
            path="episodes/example/media/01.png",
            sha256="abc123",
            owner_type=EntityType.EPISODE,
            owner_id="ep_001",
            created_by="image_generation",
            created_at=self.now,
            trace_id="trace_001",
            task_id="task_001",
        )

        self.assertEqual(artifact.artifact_type, ArtifactType.IMAGE)
        self.assertEqual(artifact.owner_type, EntityType.EPISODE)
        self.assertEqual(artifact.path, "episodes/example/media/01.png")

    def test_contract_identity_fields_are_immutable(self) -> None:
        event = EventContract(
            event_id="evt_001",
            event_type=EventType.EPISODE_CREATED,
            aggregate_type=EntityType.EPISODE,
            aggregate_id="ep_001",
            occurred_at=self.now,
        )

        with self.assertRaises(FrozenInstanceError):
            event.event_id = "evt_changed"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
