"""Score perception against samples/hard-call-for-applications.pdf.

Ten traps with known right answers. This is not a unit test -- it calls a real
model and costs money, so it is a script you run deliberately. But the answer key
is machine-checked rather than eyeballed, because "the extraction looked good" is
not a result.

    uv run python scripts/stress_test.py
"""

import asyncio
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

for line in (ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line and "API_KEY" not in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from berkas.perception import extract  # noqa: E402

PDF = ROOT / "samples" / "hard-call-for-applications.pdf"


def find(spec, needle):
    for s in spec.sections:
        if needle.lower() in s.name.lower():
            return s
    return None


def extras(spec):
    return " ".join(spec.extra_requirements).lower()


CHECKS = [
    ("erratum supersedes the table",
     lambda sp: (find(sp, "motivation") or 0) and find(sp, "motivation").word_cap == 350,
     "Component A must be 350 (erratum), not the table's 500"),
    ("page limit is not a word limit",
     lambda sp: find(sp, "contribution") and find(sp, "contribution").word_cap is None
                and "2 page" in extras(sp),
     "Component B is capped in pages; the ~800 words is indicative"),
    ("character limit is not a word limit",
     lambda sp: find(sp, "bio") and find(sp, "bio").word_cap is None and "750 char" in extras(sp),
     "Component C is 750 characters"),
    ("optional stays optional",
     lambda sp: find(sp, "leadership") and find(sp, "leadership").required is False
                and find(sp, "leadership").word_cap == 250,
     "Component D is optional, 250 words"),
    ("no stated limit means unbounded",
     lambda sp: find(sp, "financial") and find(sp, "financial").word_cap is None,
     "Component E states no limit; null, not a guess"),
    ("withdrawn component is not a section",
     lambda sp: find(sp, "research proposal") is None,
     "Component F is withdrawn and must not appear"),
    ("both deadlines survive",
     lambda sp: sp.deadline == "2026-09-14" and "7 september" in extras(sp),
     "portal closes 14 Sep; Vocational must file by 7 Sep"),
    ("the Indonesian section is found",
     lambda sp: find(sp, "surat pernyataan") and find(sp, "surat pernyataan").word_cap == 300,
     "Surat Pernyataan, mandatory, 300 kata"),
    ("mixed register captured",
     lambda sp: "english" in sp.voice_register.lower() and "indonesia" in sp.voice_register.lower(),
     "formal English, except the Surat Pernyataan in Indonesian"),
    ("no distractor became a word cap",
     lambda sp: not ({s.word_cap for s in sp.sections} & {30, 24, 18, 200, 1500, 2, 10, 800, 750, 500}),
     "credits, GPA, ages, MB, dpi and the withdrawn 1,500 are not word caps"),
]


def main() -> None:
    spec = asyncio.run(extract(PDF.read_bytes(), "application/pdf"))
    print(f"deadline: {spec.deadline}   sections: {len(spec.sections)}\n")

    failed = 0
    for name, check, why in CHECKS:
        try:
            ok = bool(check(spec))
        except Exception:
            ok = False
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            print(f"        expected: {why}")

    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} traps handled")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
