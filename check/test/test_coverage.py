"""Structural test coverage: every logic module has a matching test file.

For every python source under a src/ directory, a test file named
test_<stem>.py must exist in the sibling test/ directory — untested modules
surface as a red build the day they appear. Exemptions are explicit and
justified below; shrinking the list is welcome, growing it needs a reason.
"""

import os
import re
import unittest

_SRC = re.compile(r"^(?P<pkg>check|core/[a-z]+)/src(/rule)?/(?P<stem>[a-z_0-9]+)\.py$")

# Justified exemptions:
_EXEMPT = {
    "check/src/main.py",  # the driver: exercised by every check target in //...
    "core/date/src/cli.py",  # thin composer over the tested atomic date utils
}


class CoverageTest(unittest.TestCase):
    def test_every_module_has_a_test(self):
        sources, tests = [], set()
        for dirpath, dirnames, filenames in os.walk("."):
            dirnames[:] = [d for d in dirnames if not d.startswith((".", "bazel-"))]
            for name in filenames:
                path = os.path.relpath(os.path.join(dirpath, name), ".")
                if name.startswith("test_") and name.endswith(".py"):
                    tests.add(path)
                else:
                    m = _SRC.match(path)
                    if m:
                        sources.append((path, m["pkg"], m["stem"]))
        self.assertTrue(sources, "no sources found — data wiring broken?")
        missing = []
        for path, pkg, stem in sources:
            if path in _EXEMPT:
                continue
            if f"{pkg}/test/test_{stem}.py" not in tests:
                missing.append(f"{path} has no {pkg}/test/test_{stem}.py")
        self.assertEqual(missing, [], "untested modules:\n" + "\n".join(missing))


if __name__ == "__main__":
    unittest.main()
