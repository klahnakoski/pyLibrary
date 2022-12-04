import mo_json_config

config = mo_json_config.get("https://raw.githubusercontent.com/klahnakoski/mo-json-config/dev/tests/resources/simple.json")
assert config.test_key == "test_value"
