from platform.repository.mysql.json_column_policy import unexpected_json_columns


def test_generation_attempt_context_is_an_approved_bounded_json_extension():
    rows = [{"TABLE_NAME": "tb_generation_attempt", "COLUMN_NAME": "context"}]
    assert unexpected_json_columns(rows) == set()
