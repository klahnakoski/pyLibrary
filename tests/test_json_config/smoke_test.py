import mo_json_config
from mo_json_config import configuration

config = mo_json_config.get("https://raw.githubusercontent.com/klahnakoski/mo-json-config/dev/tests/resources/simple.json")
assert config.test_key == "test_value"

configuration |= config
assert configuration.test.key == "test_value"
