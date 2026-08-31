"""Copy the evidence Berkas is allowed to draw on into corpus/.

Only Dani's own writing about his own career, plus his voice profile. Run before
deploying; corpus/ is gitignored and deliberately not published.

    uv run python scripts/sync_corpus.py
"""

import shutil
from pathlib import Path

HOME = Path.home()
CAREER = HOME / "Documents" / "Career"
VOICE = HOME / "Documents" / "Obsidian Vault" / "Voice" / "My Writing Voice.md"
DEST = Path(__file__).resolve().parent.parent / "corpus"

# What the drafting agent may quote from: answers he has given, letters he has
# written, and the CVs those were built from. Nothing about anyone else.
WANTED = ("application_answers.md", "cover_letter.md")


def main() -> None:
    if DEST.exists():
        shutil.rmtree(DEST)
    (DEST / "voice").mkdir(parents=True)

    copied = 0
    for kit in sorted((CAREER / "active").glob("*")):
        if not kit.is_dir():
            continue
        for name in WANTED:
            src = kit / name
            if src.exists():
                out = DEST / "kits" / kit.name / name
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, out)
                copied += 1
        for cv in kit.glob("Muhammad_Dani_CV_*.md"):
            out = DEST / "kits" / kit.name / cv.name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cv, out)
            copied += 1

    if VOICE.exists():
        shutil.copy2(VOICE, DEST / "voice" / VOICE.name)
        copied += 1

    print(f"corpus/: {copied} files from {CAREER} and the voice profile")


if __name__ == "__main__":
    main()
