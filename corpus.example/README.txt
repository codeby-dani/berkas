A fictional applicant, so that a clone of this repository runs.

Everyone here is invented: the person, the university, the employers, the
scholarship. The names were composed rather than copied, and no file here is
drawn from a real applicant. Any resemblance to an existing organisation is
coincidental and unintended.

Your own corpus goes in corpus/, which .gitignore excludes on purpose. When that
directory has files, Berkas reads it instead. To point somewhere else entirely:

    BERKAS_CORPUS=/path/to/your/corpus uv run pytest -q

This file is .txt, not .md, so evidence._from_disk() does not ingest it as
background.
