#!/usr/bin/env python3
"""WB1.13-a  Git in a sandbox.

Builds a throwaway repository in a temporary folder, makes five commits on two branches,
merges them, prints the history graph and one diff, then deletes the folder.
Names, e-mail and dates are fixed, and your own Git settings are ignored, so the commit
IDs are the same on every computer.  Needs Git installed (git --version).

Run:  python wb1_13_a_git_sandbox.py
"""
import os
import pathlib
import shutil
import subprocess
import tempfile

ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="Reader", GIT_AUTHOR_EMAIL="reader@example.org",
           GIT_COMMITTER_NAME="Reader", GIT_COMMITTER_EMAIL="reader@example.org")


def git(repo, *args, date=None):
    env = dict(ENV)
    if date:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{date}T09:00:00+00:00"
    out = subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=repo, env=env,
                         capture_output=True, text=True, check=True)
    return out.stdout


def write(repo, name, text):
    p = repo / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def build(repo):
    git(repo, "init", "-q", "-b", "main")
    write(repo, "triage.py", 'def team(text):\n    if "invoice" in text.lower():\n        return "billing"\n    return "general"\n')
    git(repo, "add", "triage.py")
    git(repo, "commit", "-q", "-m", "Add first triage rule", date="2026-01-05")
    write(repo, "test_triage.py", 'from triage import team\n\n\ndef test_invoice():\n    assert team("Invoice 2041 is wrong") == "billing"\n')
    git(repo, "add", "test_triage.py")
    git(repo, "commit", "-q", "-m", "Add a test for the rule", date="2026-01-06")
    git(repo, "switch", "-q", "-c", "password-rule")
    write(repo, "triage.py", 'def team(text):\n    if "invoice" in text.lower():\n        return "billing"\n'
          '    if "password" in text.lower():\n        return "accounts"\n    return "general"\n')
    git(repo, "commit", "-q", "-am", "Route password questions to accounts", date="2026-01-07")
    git(repo, "switch", "-q", "main")
    write(repo, "README.md", "# Helpdesk triage\n\nRoutes each ticket to a team.\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "Add README", date="2026-01-08")
    git(repo, "merge", "-q", "--no-ff", "-m", "Merge branch password-rule", "password-rule", date="2026-01-09")


def main():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="wb1_13_a_"))
    try:
        build(tmp)
        graph = git(tmp, "log", "--graph", "--format=%h %ad %s", "--date=short", "--all")
        diff = git(tmp, "show", "--format=commit %h %s", "--unified=1", "password-rule", "--", "triage.py")
        print("WB1.13-a  Git in a sandbox: 5 commits, 2 branches, 1 merge")
        print("history (newest first):")
        for line in graph.rstrip("\n").split("\n"):
            print(("  " + line).rstrip())
        print("diff of the branch commit:")
        keep = [l for l in diff.rstrip("\n").split("\n") if not l.startswith(("diff --git", "index "))]
        for line in keep:
            print(("  " + line).rstrip())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
