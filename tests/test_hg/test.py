# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from mo_dots import Null, wrap, coalesce
from mo_files import File
from mo_hg.hg_mozilla_org import HgMozillaOrg
from mo_hg.parse import diff_to_json, diff_to_moves
from mo_logs import constants, Log, startup
from mo_testing.fuzzytestcase import FuzzyTestCase
from mo_threads import Till
from pyLibrary.env import http


class TestHg(FuzzyTestCase):
    config = Null

    @classmethod
    def setUpClass(cls):
        try:
            cls.config = startup.read_settings(filename="tests/config.json")
            constants.set(cls.config.constants)
            Log.start(cls.config.debug)
        except Exception as e:
            Log.error("Problem with etl", e)

    @classmethod
    def tearDownClass(cls):
        Log.stop()

    def setUp(self):
        self.hg = HgMozillaOrg(TestHg.config)

    def test_get_push1(self):
        central = [b for b in self.hg.branches if b.name == "mozilla-central" and b.locale == "en-US"][0]
        test = self.hg._get_push(central, "b6b8e616de32")
        expected = {"date": 1503659542, "user": "archaeopteryx@coole-files.de", "id": 32390}
        self.assertEqual(test, expected)
        while len(self.hg.todo.queue):
            Till(seconds=1).wait()

    def test_get_rev_with_backout(self):
        central = [b for b in self.hg.branches if b.name == "mozilla-central" and b.locale == "en-US"][0]
        test = self.hg.get_revision(wrap({"branch":central, "changeset":{"id":"de7aa6b08234"}}))
        expected = {"changeset": {"backedoutby": "f384789a29dcfd514d25d4a16a97ec5309612d78"}}
        self.assertEqual(test, expected)
        while len(self.hg.todo.queue):
            Till(seconds=1).wait()

    def test_get_prefix_space(self):
        central = [b for b in self.hg.branches if b.name == "mozilla-central" and b.locale == "en-US"][0]
        test = self.hg.get_revision(wrap({"branch": central, "changeset": {"id": "de7aa6b08234"}}), None, True)

        self.assertTrue(test.changeset.diff[1].changes[0].new.content.startswith("    "))

    def test_diff_to_json(self):
        j1 = diff_to_json(File("tests/resources/diff1.patch").read())
        j2 = diff_to_json(File("tests/resources/diff2.patch").read())

        e1 = File("tests/resources/diff1.json").read_json(flexible=False, leaves=False)
        e2 = File("tests/resources/diff2.json").read_json(flexible=False, leaves=False)
        self.assertEqual(j1, e1)
        self.assertEqual(j2, e2)

    def test_big_changeset_to_json(self):
        big_patch_file = File("tests/resources/big.patch")
        # big_patch_file.write_bytes(http.get("https://hg.mozilla.org/mozilla-central/raw-rev/e5693cea1ec944ca077c7a46c5f127c828a90f1b").content)
        self.assertEqual(b'\r'.decode('utf8', 'replace'), u'\r')

        j1 = diff_to_json(big_patch_file.read_bytes().decode("utf8", "replace"))
        expected = File("tests/resources/big.json").read_json(flexible=False, leaves=False)
        self.assertEqual(j1, expected)

    def test_small_changeset_to_json(self):
        small_patch_file = File("tests/resources/small.patch")


        j1 = diff_to_json(small_patch_file.read_bytes().decode("utf8", "replace"))
        expected = File("tests/resources/small.json").read_json(flexible=False, leaves=False)
        self.assertEqual(j1, expected)

    def test_changeset_to_json(self):
        j1 = self.hg.get_revision(
            wrap({
                "branch": {"name": "mozilla-central", "url": "https://hg.mozilla.org/mozilla-central"},
                "changeset": {"id": "e5693cea1ec944ca0"}
            }),
            None,  # Locale
            True   # get_diff
        )
        expected = File("tests/resources/big.json").read_json(flexible=False, leaves=False)
        self.assertEqual(j1.changeset.diff, expected)

    def test_coverage_parser(self):
        diff = http.get('https://hg.mozilla.org/mozilla-central/raw-rev/14dc6342ec5').content.decode('utf8')
        moves = diff_to_moves(diff)
        Log.note("{{files}}", files=[m.old.name if m.new.name=='dev/null' else m.new.name for m in moves])
