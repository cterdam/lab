"""check: one aggregate test target per file type.

`check()` emits a single `py_test` that runs the shared driver over *all* of
`srcs` with the given `rules` (rules and their formatter libraries load once,
then the driver loops files x rules). Editing any file re-runs the one test;
that scan is a fast in-process loop, so it stays cheap into the tens of
thousands of files. (Sharding into N targets for finer caching/parallelism can
be layered on later without touching the driver.)
"""

load("@labpip//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_test")

def rule(label, files = {}, deps = [], **args):
    """A rule plus the config a package gives it, e.g.

        rule("//check:schema", files = {"schema": "schema.json"})
        rule("//check:date", not_future = ["create"], ordered = [["create", "update"]])

    Rules are generic; the package supplies the field names / files. Config,
    all injected into the rule's `check(path, **config)` by parameter name (a rule
    ignores keys it doesn't declare):

      - files: {param: label} — a file the rule reads; rootpath-resolved and added
        to runfiles.
      - deps: [label] — extra libraries the rule imports at runtime (e.g. a
        registry of other lists), added to the test's deps.
      - **args: {param: value} — literal config (a field name, or a list of field
        names, or a list of [a, b] pairs); encoded as a delimited string.
    """
    return struct(label = label, files = files, deps = deps, args = args)

def _encode(value):
    # str -> itself; [str] -> "a,b"; [[a, b], ...] -> "a-b,c-d". Field names are
    # [a-z0-9_] so "," and "-" are safe, shell-token-safe delimiters.
    if type(value) == "string":
        return value
    parts = []
    for item in value:
        parts.append(item if type(item) == "string" else "-".join(item))
    return ",".join(parts)

def check(name, srcs, rules, data = []):
    """Emit one aggregate check test that runs every rule over every src.

    Args:
        name: the test target name (e.g. "check"); `bazel test //pkg:name`.
        srcs: the files owned by this type; all checked by the one test.
        rules: a list of rule(label, ...); each runs on every file. Call check()
            once per file group to apply different rules/config to file types.
        data: shared runtime inputs the rules read (shared schemas, tables).
    """
    rule_args = []
    file_values = []
    for r in rules:
        if type(r) != "struct":
            fail("check(): wrap every rule in rule(...), e.g. rule(\"//check:date\"); got %r" % (r,))
        rule_args.append("--rule")
        rule_args.append("$(rootpath %s)" % r.label)
        stem = r.label.split(":")[-1]
        for key in r.files:
            rule_args.append("--rule_file")
            rule_args.append("%s:%s=$(rootpath %s)" % (stem, key, r.files[key]))
            file_values.append(r.files[key])
        for key in r.args:
            rule_args.append("--rule_arg")
            rule_args.append("%s:%s=%s" % (stem, key, _encode(r.args[key])))
    file_data = {v: None for v in file_values}.keys()

    file_args = []
    for src in srcs:
        file_args.append("--file")
        file_args.append("$(rootpath %s)" % src)

    # The test is wrapped in a same-named test_suite so the public label stays
    # `//pkg:name`; the py_test itself takes a distinct name so it never path-
    # collides with a `check/` source directory in the same package (a file
    # `bin/pkg/check` can't coexist with `bin/pkg/check/__pycache__/...`).
    test_name = name + ".driver"
    dep_labels = [r.label for r in rules] + [requirement("absl-py")]
    for r in rules:
        dep_labels = dep_labels + r.deps

    py_test(
        name = test_name,
        srcs = ["//check:src/main.py"],
        main = "//check:src/main.py",
        args = file_args + rule_args,
        data = srcs + file_data + data,
        deps = {d: None for d in dep_labels}.keys(),
        size = "medium",
    )
    native.test_suite(name = name, tests = [":" + test_name])

# Formatting suites, one per language. Each globs only its extensions in the
# calling package and runs the matching rule, so a suite pulls only its deps.
_FMT = [
    ("py", ["**/*.py"], "//check:fmt_py", {}),
    ("md", ["**/*.md"], "//check:fmt_md", {}),
    ("json", ["**/*.json"], "//check:fmt_json", {}),
    ("bzl", ["*.bazel", "**/*.bzl"], "//check:fmt_bzl", {"buildifier": "@buildifier_prebuilt//:buildifier"}),
]

def fmt(name = "fmt"):
    """Emit per-language fmt/<lang> suites for the calling package's files.

    Suites are named with "/" (fmt/py, fmt/bzl, ...) so they never collide with a
    rule library's target name (fmt_py, ...) — which matters in //check, the one
    package that both defines the fmt_* rules and formats its own files.
    """
    for lang, patterns, label, files in _FMT:
        # Exclude the bazel-* convenience symlinks: a recursive glob at the
        # workspace root would otherwise descend them into the output tree.
        srcs = native.glob(patterns, exclude = ["bazel-*/**"], allow_empty = True)
        if srcs:
            check(name = name + "/" + lang, srcs = srcs, rules = [rule(label, files = files)])
