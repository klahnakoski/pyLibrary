import datetime
import unittest
from util.cnv import CNV
from util.logs import Log


class TestJSON(unittest.TestCase):
    def test_date(self):
        output = CNV.object2JSON({"test": datetime.date(2013, 11, 13)})
        Log.note("JSON = {{json}}", {"json": output})

if __name__ == '__main__':
    unittest.main()
