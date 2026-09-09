from platform.validation.ep_runtime_probe import EpRuntimeObservationProbe


EP002 = "episodes/10_彼此的天上/02_玻璃另一边的手"


def test_ep002_observation_is_read_only():
    result = EpRuntimeObservationProbe().inspect(EP002)

    assert result["read_only"] is True
    assert result["facts"]["episode_state"] is not None
    assert result["facts"]["runtime_request"] is not None
