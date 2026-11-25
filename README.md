# Measured AI: companion files

Workbench programs for the *Measured AI* book series by Jack Salameh:

- Volume I, *Beginner's Journey Into AI*
- Volume II, *Intermediate Mastery* (forthcoming)
- Volume III, *Professional Strategies* (forthcoming)

## Download

Download everything as one zip file:
<https://github.com/JackSalameh/measured-ai-companion/archive/refs/heads/main.zip>

Unzip it in a folder you back up. Each chapter has its own folder, for example
`book1/ch01/workbench`.

## Run a program

You need Python 3.10 or later and nothing else; the programs use only the standard library.
Open a terminal in the chapter's `workbench` folder and type:

```text
python wb1_1_a_rules_or_learning.py        (Windows)
python3 wb1_1_a_rules_or_learning.py       (macOS, Linux)
```

The `expected` folder holds the exact output each program must print, with its SHA-256
checksum. If your output differs, the book's Workbench Setup Guide explains what to check.

Optional: with `pytest` installed (`python -m pip install pytest`), run `python -m pytest`
in a `workbench` folder to check every program against its expected output.

## Contents

| Folder | Chapter |
|---|---|
| `book1/ch01/workbench` | 1. What AI is, and what it is not |

More chapters are added as they are released.

## Licence

The programs are released under the MIT licence (see `LICENSE`). The book text is not part
of this repository and remains © 2026 Jack Salameh, all rights reserved.
