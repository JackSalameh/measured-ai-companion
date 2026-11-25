#!/usr/bin/env python3
"""WB1.13-c  Edit-test loop on replay.

A coding agent in miniature.  Each round the "model" proposes a new parse_amount; the
harness applies the edit inside a scratch project folder, checks every proposed command
against an approval policy, runs the tests of WB1.13-b, and feeds the failures back.  The
loop stops when the tests pass (the check decides "done", chapter 11) or the budget runs out.

Demo (no key, no network):  python wb1_13_c_edit_test_loop.py
Live (your own model):      python wb1_13_c_edit_test_loop.py run config.json
  config.json: {"backend": {...as in WB1.9-b...}, "budget": 5}
"""
import importlib.util
import inspect
import json
import pathlib
import re
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "ch09" / "workbench"))
import wb1_9_b_adapter as ad  # noqa: E402
import spec_parse_amount as spec  # noqa: E402
from wb1_13_b_test_first import run  # noqa: E402

ALLOWED = ["run tests"]          # commands the harness may run without asking
ASK_ANSWER = "no"                # demo: the reader's recorded answer to every approval request


class ReplaySteps:
    """Replay back end that returns step1, step2, ... in order."""
    def __init__(self):
        self.b, self.n, self.label = ad.Replay(HERE / "replay_agent.jsonl", "demo-agent"), 0, "replay demo-agent"

    def complete(self, prompt, settings):
        self.n += 1
        return self.b.complete(prompt, settings, f"step{self.n}").text


class Live:
    def __init__(self, cfg):
        self.b = ad.make_backend(cfg)
        self.label = cfg.get("label", "live")

    def complete(self, prompt, settings):
        text = self.b.complete(prompt, settings).text
        m = re.search(r"```(?:python)?\n(.*?)```", text, flags=re.S)
        return m.group(1) if m else text


def prompt_for(failures):
    p = "Write a Python function parse_amount(text) that passes these tests:\n\n" + inspect.getsource(spec)
    if failures:
        p += "\nYour last version failed:\n" + "\n".join(f"- {n}: {w}" for n, w in failures)
    return p + "\nReturn only the code. Put any shell command you need on a line '# action: <command>'."


def load(path):
    s = importlib.util.spec_from_file_location("candidate", path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.parse_amount


def loop(model, budget, ask):
    work = pathlib.Path(tempfile.mkdtemp(prefix="wb1_13_c_"))
    failures = []
    print(f"WB1.13-c  edit-test loop ({model.label}), budget {budget}, {len(spec.TESTS)} tests")
    try:
        for r in range(1, budget + 1):
            code = model.complete(prompt_for(failures), {})
            (work / "parse_amount.py").write_text(code, encoding="utf-8")
            print(f"  round {r}  edit parse_amount.py (inside the project): allowed")
            for cmd in re.findall(r"^# action: (.+)$", code, flags=re.M):
                verdict = "allowed" if cmd in ALLOWED else f"ask the reader -> {ask(cmd)}"
                print(f"           '{cmd}': {verdict}")
            print("           'run tests': allowed")
            try:
                results = run(load(work / "parse_amount.py"))
            except Exception as e:  # the edit does not even load
                results = [("load", False, type(e).__name__)]
            failures = [(n, w) for n, ok, w in results if not ok]
            print(f"           {len(results) - len(failures)} of {len(results)} pass"
                  + ("; failing: " + ", ".join(n.removeprefix("test_") for n, _ in failures) if failures else ""))
            if not failures:
                print(f"done after {r} rounds: the tests pass")
                return r
        print(f"stopped: budget of {budget} rounds used, {len(failures)} tests still fail")
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        cfg = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
        loop(Live(cfg["backend"]), cfg.get("budget", 5), lambda c: input(f"allow '{c}'? [y/N] ") or "no")
    else:
        loop(ReplaySteps(), 5, lambda c: ASK_ANSWER)


if __name__ == "__main__":
    main()
