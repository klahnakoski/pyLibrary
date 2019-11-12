
# read_alternate_settings
import os

import mo_json_config

from mo_logs import constants, Log
from tests import test_jx
from tests.test_sqlite import SQLiteUtils

try:
    filename = os.environ.get("TEST_CONFIG")
    if filename:
        test_jx.global_settings = mo_json_config.get("file://"+filename)
        constants.set(test_jx.global_settings.constants)
    else:
        Log.alert("No TEST_CONFIG environment variable to point to config file.  Using ./tests/config/sqlite.json")
        test_jx.global_settings = mo_json_config.get("file://tests/config/sqlite.json")
        constants.set(test_jx.global_settings.constants)

    if not test_jx.global_settings.use:
        Log.error('Must have a {"use": type} set in the config file')

    Log.start(test_jx.global_settings.debug)
    test_jx.utils = SQLiteUtils(test_jx.global_settings)
except Exception as e:
    Log.warning("problem", e)

