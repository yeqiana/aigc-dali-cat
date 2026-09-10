from platform.operations.experience_store import (
    ExperienceStore,
    RuntimeExperience,
)


def test_experience_store_append_and_query():
    store = ExperienceStore()

    store.append(
        RuntimeExperience(
            experience_id="exp-001",
            runtime="v3-runtime",
            agent="story-agent",
            workflow="episode-production",
            outcome="SUCCESS",
            pattern="stable_generation",
            evidence_ref="trace-001",
            confidence=0.95,
        )
    )

    assert store.count() == 1
    assert len(store.find_by_pattern("stable_generation")) == 1


def test_experience_store_empty():
    store = ExperienceStore()

    assert store.count() == 0
    assert store.list_all() == ()
