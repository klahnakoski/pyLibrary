from mo_logs import Log

from mo_testing.fuzzytestcase import FuzzyTestCase


class Tests(FuzzyTestCase):

    def test_raises_w_nothing(self):
        with self.assertRaises():
            raise Exception("problem")

    def test_raises_w_string(self):
        with self.assertRaises("example1"):
            Log.error("example1")

    def test_not_raises(self):
        with self.assertRaises(Exception):
            with self.assertRaises("example2"):
                Log.error("example1")  # DOES NOT MATCH EXPECTED

    def test_raises_w_array1(self):
        with self.assertRaises(["example1", "example2"]):
            Log.error("example1")

    def test_raises_w_array2(self):
        with self.assertRaises(["example1", "example2"]):
            Log.error("example2")


