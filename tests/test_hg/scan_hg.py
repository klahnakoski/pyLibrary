# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import division
from __future__ import unicode_literals

from mo_collections.queue import Queue
from mo_dots import listwrap, wrap
from mo_logs import Log, constants, startup
from mo_times import Date

from mo_hg import hg_mozilla_org
from mo_hg.hg_mozilla_org import HgMozillaOrg


MIN_FILES = 30
BRANCH = "mozilla-central"


hg_mozilla_org.MAX_DIFF_SIZE = 10000000
hg_mozilla_org.DAEMON_HG_INTERVAL = 0

_ = Date

def main():

    try:
        settings = startup.read_settings()
        constants.set(settings.constants)
        Log.start(settings.debug)

        hg = HgMozillaOrg(settings)
        todo = Queue()
        todo.add("97160a734959")
        least = 100000

        while todo:
            next_ = todo.pop()
            curr = hg.get_revision(wrap({"changeset": {"id": next_}, "branch": {"name": BRANCH}}))
            if len(curr.changeset.files) > MIN_FILES:
                diff = hg._get_json_diff_from_hg(curr)
                num_changes = sum(len(d.changes) for d in diff)
                score =  num_changes / len(diff)
                if score < least:
                    least = score
                    Log.note("smallest = {{rev}}, num_lines={{num}}, num_files={{files}}", rev=curr.changeset.id, num=num_changes, files=len(diff))
            todo.extend(listwrap(curr.parents))

    except Exception as e:
        Log.error("Problem with scna", e)
    finally:
        Log.stop()


if __name__ == "__main__":
    main()
