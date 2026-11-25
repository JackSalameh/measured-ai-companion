# Measured AI: companion files

Workbench programs and data for the *Measured AI* book series by Jack Salameh:

- Volume I, *Beginner's Journey Into AI*
- Volume II, *Intermediate Mastery* (forthcoming)
- Volume III, *Professional Strategies* (forthcoming)

## Download

Download everything as one zip file:
<https://github.com/JackSalameh/measured-ai-companion/archive/refs/heads/main.zip>

Unzip it in a folder you back up and keep the folder structure as it is: several programs
read the shared data in `workbench/data`, and some chapters reuse a program from an earlier
chapter. If you use Git, `git clone https://github.com/JackSalameh/measured-ai-companion`
instead, and `git pull` later to receive corrections.

## Folder structure

```text
measured-ai-companion/
  book1/
    ch01/workbench/    one folder per chapter: the programs, their test file,
    ch02/workbench/    any input files, and expected/ (the exact output each
    ...                program must print, with its SHA-256 checksum)
    ch16/workbench/
  workbench/
    data/              the series datasets shared by several chapters:
                       generators, DATA_CARD.md, and out/ (tickets, ledger,
                       signal features, with checksums)
```

## Run a program

You need Python 3.10 or later. Open a terminal in a chapter's `workbench` folder and type,
for example:

```text
cd book1/ch05/workbench
python wb1_5_a_gradient.py         (Windows)
python3 wb1_5_a_gradient.py        (macOS, Linux)
```

Compare what the program prints with the file of the same name in `expected/`. The book's
Workbench Setup Guide explains what to check if they differ.

- **No network and no API key are needed.** The chapters on language models (9, 10, 13 and
  14) replay recorded model answers from the files in their folder. Each chapter explains
  how to switch to a live model of your choice.
- **Extra tools, only where a chapter says so:** `pytest` to run the tests
  (`python -m pip install pytest`); Git for chapter 13; the package `mistral-common`
  for the optional tokenizer example `ex9_tokens.py` in chapter 9.

## Check everything at once

With `pytest` installed, run this in the top folder:

```text
python -m pytest book1 workbench
```

Or run the capstone's portfolio runner, which runs every chapter's checks and prints a table:

```text
cd book1/ch16/workbench
python wb1_16_a_portfolio_runner.py
```

## Contents of Volume I

| Folder | Chapter |
|---|---|
| `book1/ch01/workbench` | 1. What AI is, and what it is not |
| `book1/ch02/workbench` | 2. Lineage: how the ideas evolved |
| `book1/ch03/workbench` | 3. Data and representation |
| `book1/ch04/workbench` | 4. Numbers, probability and uncertainty |
| `book1/ch05/workbench` | 5. How machines learn |
| `book1/ch06/workbench` | 6. Neural networks |
| `book1/ch07/workbench` | 7. Seeing, hearing and sensing |
| `book1/ch08/workbench` | 8. How language models work |
| `book1/ch09/workbench` | 9. The provider landscape and choosing a tool |
| `book1/ch10/workbench` | 10. Prompting as a skill |
| `book1/ch11/workbench` | 11. Verifying AI output |
| `book1/ch12/workbench` | 12. Research and learning with AI |
| `book1/ch13/workbench` | 13. AI for code and tooling |
| `book1/ch14/workbench` | 14. AI for documents and data |
| `book1/ch15/workbench` | 15. Using AI responsibly |
| `book1/ch16/workbench` | 16. Capstone and roadmap |
| `workbench/data` | Series datasets used from chapter 3 onward |

All data are synthetic or fictional; the data card in `workbench/data/DATA_CARD.md`
describes each dataset.

## Licence

The programs are released under the MIT licence (see `LICENSE`). The book text is not part
of this repository and remains © 2026 Jack Salameh, all rights reserved.
