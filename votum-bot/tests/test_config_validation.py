from bot.src.utils.jsonschema import validate_config_value


def test_validate_always_true():
    assert validate_config_value("any_key", {"foo": "bar"}) is True