from platform.operations.learning_calibration_pipeline import (
    LearningCalibrationPipeline,
)


def test_learning_calibration_pipeline_loads_episode_feedback(tmp_path):
    file = tmp_path / "EP001.json"
    file.write_text(
        '{"episode_id":"EP001","platform":"douyin",'
        '"publish_time":"2026-09-01",'
        '"view_count":33000,"like_count":2000,'
        '"comment_count":100,"share_count":50,'
        '"favorite_count":80,"completion_rate":0.7,'
        '"follower_growth":100}',
        encoding="utf-8",
    )

    result = LearningCalibrationPipeline().load_feedback(str(tmp_path))

    assert len(result) == 1
    assert result[0].episode_id == "EP001"
    assert result[0].view_count == 33000
