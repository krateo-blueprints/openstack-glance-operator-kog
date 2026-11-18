#!/usr/bin/env python3
"""Run ImageImport's notFoundBody predicate against every image state Glance can leave behind.

The predicate decides when rest-dynamic-controller sends POST /v2/images/{id}/import. "true" means
"absent", so the import fires; "false" means it exists, so nothing fires. Getting it wrong either
way is costly:
  - true on a failed import re-sends the import on every reconcile, forever (a bad URI is
    permanent);
  - true on an active image sends an import Glance refuses with 409;
  - false on a fresh image means the import never happens.

The fixtures are the image representations Glance stable/2026.1 produces at each step, read from
glance/api/v2/images.py (the import lock) and glance/async_/flows/api_image_import.py (get_flow,
merge_store_list, the revert paths). The predicate is read out of the rendered RestDefinition, so
this tests the bytes that ship.

The detector is proven first: with the "an import ran" clauses removed, the failed-import fixture
must flip to true. A test whose fixtures cannot tell the two predicates apart would pass vacuously.

Needs `helm` and `jq` (rest-dynamic-controller evaluates with gojq; the subset used here -- ==,
and, not, //, has -- behaves the same in both).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

CHART = sys.argv[1] if len(sys.argv) > 1 else "chart"
RD_SUFFIX = "-image-import"

# (label, image as Glance returns it, expected predicate result)
FIXTURES = [
    ("never imported (fresh queued image)",
     {"id": "i", "status": "queued"}, True),
    ("import accepted, flow not started yet (lock taken before the 202)",
     {"id": "i", "status": "queued", "os_glance_import_task": "t1"}, False),
    ("importing (flow started: status, lock, store bookkeeping keys)",
     {"id": "i", "status": "importing", "os_glance_import_task": "t1",
      "os_glance_importing_to_stores": "", "os_glance_failed_import": ""}, False),
    ("active after a successful import (lock dropped, keys left behind)",
     {"id": "i", "status": "active",
      "os_glance_importing_to_stores": "", "os_glance_failed_import": ""}, False),
    ("FAILED import, single store: reverted to queued, lock dropped, keys left behind",
     {"id": "i", "status": "queued",
      "os_glance_importing_to_stores": "", "os_glance_failed_import": ""}, False),
    ("FAILED import, multi-store: the failed store recorded",
     {"id": "i", "status": "queued",
      "os_glance_importing_to_stores": "", "os_glance_failed_import": "file1"}, False),
    ("task failed before the flow was built: lock never dropped",
     {"id": "i", "status": "queued", "os_glance_import_task": "t1"}, False),
    ("lock present but empty string (treated as no lock), never imported",
     {"id": "i", "status": "queued", "os_glance_import_task": ""}, True),
]
DISCRIMINATING = "FAILED import, single store: reverted to queued, lock dropped, keys left behind"


def predicate_from_chart():
    tmp = tempfile.mkdtemp()
    try:
        dst = os.path.join(tmp, "chart")
        shutil.copytree(CHART, dst)
        cy = os.path.join(dst, "Chart.yaml")
        with open(cy) as f:
            text = f.read().replace("CHART_VERSION", "0.0.0-ci")
        with open(cy, "w") as f:
            f.write(text)
        out = subprocess.run(["helm", "template", "release", dst], check=True,
                             capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for d in yaml.safe_load_all(out):
        if d and d.get("kind") == "RestDefinition" and d["metadata"]["name"].endswith(RD_SUFFIX):
            for v in d["spec"]["resource"]["verbsDescription"]:
                if v["action"] == "get" and v.get("notFoundBody"):
                    return v["notFoundBody"]["inline"]
    raise SystemExit("FAIL: no get verb with a notFoundBody in the %s RestDefinition" % RD_SUFFIX)


def evaluate(prog, doc):
    p = subprocess.run(["jq", "-c", prog], input=json.dumps(doc), capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("FAIL: jq could not run the predicate: %s" % p.stderr.strip())
    return p.stdout.strip() == "true"


def run(prog, quiet=False):
    failures = 0
    for label, doc, want in FIXTURES:
        got = evaluate(prog, doc)
        ok = got == want
        failures += not ok
        if not quiet:
            print("%s  %-80s -> %-5s (want %s)" % ("ok  " if ok else "FAIL", label, got, want))
    return failures


def main():
    prog = predicate_from_chart()
    print("predicate: " + " ".join(prog.split()))

    # Prove the fixtures discriminate: without the "an import ran" clauses, the failed import must
    # read as absent (i.e. would be re-fired).
    weakened = '.status == "queued" and ((.os_glance_import_task // "") == "")'
    failed_doc = next(doc for label, doc, _ in FIXTURES if label == DISCRIMINATING)
    if not evaluate(weakened, failed_doc):
        raise SystemExit("FAIL: self-test: the weakened predicate does not re-fire a failed import, so "
                         "the fixtures cannot detect the loop this test exists for")
    print("self-test: a status+lock-only predicate would re-fire the failed import (detected)")

    failures = run(prog)
    print("%d fixture(s), %d failure(s)" % (len(FIXTURES), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
