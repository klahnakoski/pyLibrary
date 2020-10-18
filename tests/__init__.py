import os

from mo_dots import Data, Null
from tests import test_jx

test_jx.global_settings = Data(use="nothing")
test_jx.utils = Null

IS_WINDOWS = os.name == "nt"
