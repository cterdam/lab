"""Aggregate check driver.

Usage:
    main.py --file <doc> [--file <doc> ...] --rule <module.py> [--rule ...] \\
            [--rule_file <rule>:<key>=<path>] [--rule_arg <rule>:<key>=<value>]

Runs every --rule against every --file in a single process: rule modules (and
the formatter libraries they import) load once, then the driver loops files x
rules. Each rule module exposes `rule(path, **config)` and raises AssertionError
on a violation. Per-rule config (declared in BUILD via rule(label, ...)) is
injected by parameter name: a rule gets a config key only if its `rule`
signature names it. --rule_file carries file paths the rule reads; --rule_arg
carries literal config strings.

The driver exits non-zero if any (file, rule) fails or a rule is missing its
`rule` function, printing one `FAIL <file> [<rule>] <msg>` line per violation.

Paths arrive as repo-relative `$(rootpath ...)` values; the working directory is
the runfiles root, so they open directly.
"""

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path

from absl import app, flags

FLAGS = flags.FLAGS

flags.DEFINE_multi_string("file", [], "a file under test; repeatable")
flags.DEFINE_multi_string("rule", [], "a rule module exposing rule(path); repeatable")
flags.DEFINE_multi_string(
    "rule_file", [], "per-rule file path as <rule>:<key>=<path>; repeatable"
)
flags.DEFINE_multi_string(
    "rule_arg", [], "per-rule literal config as <rule>:<key>=<value>; repeatable"
)


def _load_rules(config):
    """Import each --rule module once, returning [(label, rule_fn, kwargs)]."""
    loaded, errors = [], []
    for rf in FLAGS.rule:
        label = Path(rf).stem
        try:
            spec = importlib.util.spec_from_file_location("rule__" + label, rf)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
        except Exception:  # noqa: BLE001
            errors.append(f"[{label}] import error:\n{traceback.format_exc()}")
            continue
        fn = getattr(mod, "rule", None)
        if fn is None:
            errors.append(f"[{label}] module defines no rule(path) function")
            continue
        params = inspect.signature(fn).parameters
        kwargs = {k: v for k, v in config.get(label, {}).items() if k in params}
        loaded.append((label, fn, kwargs))
    return loaded, errors


def main(argv):
    del argv  # absl handles flag parsing

    # Per-rule config, keyed by rule module stem: {rule: {key: value}}.
    config: dict[str, dict[str, str]] = {}
    for entry in FLAGS.rule_file + FLAGS.rule_arg:
        rule_name, kv = entry.split(":", 1)
        key, value = kv.split("=", 1)
        config.setdefault(rule_name, {})[key] = value

    loaded, failures = _load_rules(config)  # a rule that won't load fails the run

    failed_files: set[str] = set()
    for f in FLAGS.file:
        path = Path(f)
        for label, fn, kwargs in loaded:
            try:
                fn(path, **kwargs)
            except AssertionError as e:
                failures.append(f"{f} [{label}] {str(e).strip()}")
                failed_files.add(f)
            except Exception:  # noqa: BLE001
                failures.append(f"{f} [{label}] error:\n{traceback.format_exc()}")
                failed_files.add(f)

    if failures:
        for msg in failures:
            sys.stderr.write("FAIL " + msg.replace("\n", "\n     ") + "\n")
        sys.stderr.write(
            f"\n{len(failed_files)} of {len(FLAGS.file)} files failed "
            f"({len(loaded)} rules)\n"
        )
        sys.exit(1)
    sys.stdout.write(f"PASS: {len(FLAGS.file)} files x {len(loaded)} rules\n")


if __name__ == "__main__":
    app.run(main)
