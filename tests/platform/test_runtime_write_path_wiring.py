from dataclasses import replace

from platform.adapter.runtime_adapter import RuntimeAdapter
from platform.agent.runtime import (
    AgentContext,
    AgentExecutionPlan,
    AgentRuntime,
    SkillExecutionStep,
)
from platform.core.clock import utc_now
from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.contracts.event_contract import EventContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.core.enums.trace_status import TraceStatus
from platform.observer.artifact_observer import ArtifactObserver
from platform.observer.event_observer import EventObserver
from platform.observer.trace_observer import TraceObserver
from platform.repository.runtime_repository_provider import RuntimeRepositoryProvider


class RecordingRepository:
    """内存仓库：只记录保存过的契约，验证接线是否真的调用 save()。"""

    def __init__(self):
        self.saved = []

    def save(self, entity):
        self.saved.append(entity)


def _event() -> EventContract:
    return EventContract(
        event_id='evt_wiring',
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id='task1',
        occurred_at=utc_now(),
    )


def _artifact() -> ArtifactContract:
    return ArtifactContract(
        artifact_id='artifact_wiring',
        artifact_type=ArtifactType.IMAGE,
        path='images/a.png',
        sha256='c' * 64,
        owner_type=EntityType.TASK,
        owner_id='task1',
        created_by='tester',
        created_at=utc_now(),
    )


def test_event_observer_record_persists_through_repository():
    repository = RecordingRepository()
    observer = EventObserver(repository)

    event = observer.record(EventType.TASK_STARTED, EntityType.TASK, 'task1', payload={'k': 1})

    assert repository.saved == [event]
    assert event.occurred_at.tzinfo is None
    assert observer.save(event) is None
    assert len(repository.saved) == 2


def test_event_observer_without_repository_is_observe_only():
    observer = EventObserver()
    event = observer.record(EventType.TASK_STARTED, EntityType.TASK, 'task1')

    assert observer.repository is None
    assert event.event_id.startswith('evt_')


def test_trace_observer_persists_running_then_finished_span():
    repository = RecordingRepository()
    observer = TraceObserver(repository)

    running = observer.start('agent.execute', task_id='task1')
    finished = replace(
        running,
        status=TraceStatus.SUCCESS,
        ended_at=utc_now(),
        duration_ms=12,
    )
    observer.save(finished)

    assert [item.status for item in repository.saved] == [TraceStatus.RUNNING, TraceStatus.SUCCESS]
    assert repository.saved[0].trace_id == repository.saved[1].trace_id
    assert repository.saved[0].span_id == repository.saved[1].span_id
    assert repository.saved[1].duration_ms == 12


def test_artifact_observer_register_persists_through_repository():
    repository = RecordingRepository()
    observer = ArtifactObserver(repository)

    artifact = observer.register(
        ArtifactType.IMAGE, 'images/a.png', 'd' * 64, EntityType.TASK, 'task1', 'tester'
    )

    assert repository.saved == [artifact]
    assert artifact.created_at.tzinfo is None


def test_runtime_adapter_persists_when_repositories_injected(tmp_path):
    provider = RuntimeRepositoryProvider(jsonl_root=str(tmp_path))
    adapter = RuntimeAdapter(repositories=provider.repositories())

    adapter.record_event(_event())
    adapter.record_trace(TraceObserver().start('adapter.trace'))
    adapter.register_artifact(_artifact())

    assert (tmp_path / 'events.jsonl').exists()
    assert (tmp_path / 'traces.jsonl').exists()
    assert (tmp_path / 'artifacts.jsonl').exists()


def test_runtime_adapter_without_repositories_stays_observe_only():
    adapter = RuntimeAdapter()

    assert adapter.event_observer is None
    assert adapter.trace_observer is None
    assert adapter.artifact_observer is None
    adapter.record_event(_event())
    adapter.record_trace(TraceObserver().start('adapter.trace'))
    adapter.register_artifact(_artifact())


def test_runtime_adapter_from_env_wires_jsonl_root(tmp_path, monkeypatch):
    monkeypatch.setenv('STORYOS_RUNTIME_JSONL_ROOT', str(tmp_path))
    monkeypatch.delenv('STORYOS_RUNTIME_STORE_MODE', raising=False)

    adapter = RuntimeAdapter.from_env()
    adapter.record_event(_event())

    assert (tmp_path / 'events.jsonl').exists()
    adapter.close()
    assert adapter.provider is None


def test_agent_runtime_trace_sink_persists_completed_span():
    repository = RecordingRepository()
    observer = TraceObserver(repository)
    runtime = AgentRuntime(trace_observer=observer, trace_sink=observer.save)
    runtime.skill_adapter.register(
        'text.upper',
        lambda input_data, context, invoke_tool: {'text': input_data['text'].upper()},
    )
    plan = AgentExecutionPlan(
        agent_code='story-agent',
        agent_version='v1',
        context=AgentContext(
            task_id='task-1',
            workflow_run_id='run-1',
            workflow_step_id='step-1',
            memory_context={},
        ),
        steps=(
            SkillExecutionStep(
                skill_code='text.upper',
                skill_version='v1',
                input_data={'text': 'hello'},
            ),
        ),
    )

    result = runtime.execute(plan)

    assert result.status == 'SUCCESS'
    assert [item.status for item in repository.saved] == [TraceStatus.RUNNING, TraceStatus.SUCCESS]
    finished = repository.saved[1]
    assert finished.trace_id == result.trace_id
    assert finished.ended_at is not None
    assert finished.duration_ms is not None
