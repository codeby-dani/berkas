"""Generate a deliberately awkward call for applications, as a PDF.

A stress test for perception. Every trap here is one that real call documents
actually contain, and each has a known right answer, so the extraction can be
scored rather than admired. See samples/EXPECTED.md for the answer key.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

OUT = Path(__file__).resolve().parent.parent / "samples" / "hard-call-for-applications.pdf"

s = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=s["Title"], fontSize=15, spaceAfter=2)
H2 = ParagraphStyle("H2", parent=s["Heading2"], fontSize=10.5, spaceBefore=11, spaceAfter=4)
BODY = ParagraphStyle("BODY", parent=s["BodyText"], fontSize=8.6, leading=12, alignment=TA_JUSTIFY)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.4, textColor=colors.HexColor("#444444"))
FOOT = ParagraphStyle("FOOT", parent=SMALL, fontSize=7.0, textColor=colors.HexColor("#8a1c1c"))


def p(t, style=BODY): return Paragraph(t, style)


story = [
    p("BEASISWA MOBILITAS INTERNASIONAL 2026", H1),
    p("Call for Applications &mdash; Undergraduate and Vocational Schemes<br/>"
      "Direktorat Jenderal Pendidikan Tinggi &middot; Cycle 2026/2027 &middot; Document v2.3", SMALL),
    Spacer(1, 7),

    p("1. SUBMISSION DEADLINES", H2),
    p("The application portal closes on <b>14 September 2026 at 23:59 WIB</b>. Applications received "
      "after this time are not reviewed and no extension is granted under any circumstance.", BODY),
    p("<b>1.1 Exception.</b> Applicants under the <b>Vocational (D3/D4) scheme</b> are assessed by a "
      "separate panel that convenes earlier. Vocational applicants must submit by "
      "<b>7 September 2026 at 23:59 WIB</b>. The later date above does not apply to them.", BODY),
    p("1.2 Referee letters may arrive up to 21 September 2026, after the applicant's own deadline.", BODY),

    p("2. ELIGIBILITY", H2),
    p("Applicants must be actively enrolled, having completed a minimum of 30 credits, and be in "
      "semester 4 or 6 at the time of application. A minimum cumulative GPA of 3.00 on a 4.00 scale "
      "is required; the Vocational scheme requires 3.25. Applicants must be no older than 24 years "
      "on 1 January 2027, must hold a passport valid for at least 18 months, and must not previously "
      "have received a government-funded overseas mobility award.", BODY),

    p("3. WRITTEN COMPONENTS", H2),
    p("All components are submitted through the portal as plain text. Formatting is stripped.", SMALL),
    Spacer(1, 3),
    Table(
        [["#", "Component", "Limit", "Status"],
         ["A", "Statement of Motivation", "500 words", "Mandatory"],
         ["B", "Contribution Plan", "maximum 2 pages\n(approximately 800 words)", "Mandatory"],
         ["C", "Short Biography", "750 characters\nincluding spaces", "Mandatory"],
         ["D", "Leadership Experience", "250 words", "Optional"],
         ["E", "Statement of Financial Need", "no prescribed limit", "Mandatory"],
         ["F", "Research Proposal", "1,500 words", "Withdrawn — see 3.4"]],
        colWidths=[9*mm, 58*mm, 46*mm, 34*mm],
        style=TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7.6),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TEXTCOLOR", (0, 6), (-1, 6), colors.HexColor("#999999")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]),
    ),
    Spacer(1, 4),
    p("<b>ERRATUM (issued 1 August 2026, supersedes the table above).</b> Following panel review, the "
      "limit for <b>Component A, Statement of Motivation, is reduced from 500 words to 350 words</b>. "
      "Submissions exceeding 350 words are rejected without review. The table in section 3 has not "
      "been reprinted in this revision of the document.", FOOT),
    Spacer(1, 4),
    p("3.4 Component F (Research Proposal) is <b>withdrawn for the 2026 cycle</b> and must not be "
      "submitted. Portal fields for it have been disabled. It is listed above only so that applicants "
      "working from the 2025 guidance do not submit it in error.", BODY),
    p("3.5 Component B is limited by <b>page count, not word count</b>. The parenthetical word figure "
      "in the table is indicative only and is not enforced; a submission of 2 pages is compliant "
      "regardless of its word count.", BODY),

    PageBreak(),

    p("4. KOMPONEN TAMBAHAN (WAJIB)", H2),
    p("Selain komponen di atas, setiap pelamar wajib melampirkan <b>Surat Pernyataan Komitmen "
      "Kembali ke Indonesia</b>, ditulis dalam Bahasa Indonesia, <b>maksimal 300 kata</b>. Surat ini "
      "dinilai terpisah dari Component A sampai E dan tidak dapat digantikan oleh terjemahan.", BODY),
    p("(Mandatory Additional Component: a Commitment to Return statement, written in Indonesian, "
      "maximum 300 words. Assessed separately.)", SMALL),

    p("5. REGISTER AND AUTHORSHIP", H2),
    p("All written components must be composed in <b>formal English in the first person</b>, except "
      "the Surat Pernyataan, which is written in formal Indonesian. Components must be the "
      "applicant's own work. The use of a third party to write on the applicant's behalf is grounds "
      "for disqualification at any stage, including after an award is made.", BODY),

    p("6. SUPPORTING DOCUMENTS", H2),
    p("Upload separately as PDF, each not exceeding 2 MB: (a) Kartu Tanda Mahasiswa; (b) an official "
      "academic transcript covering all completed semesters; (c) one letter of recommendation from "
      "the home faculty, on letterhead, signed; (d) a passport biodata page. Scanned documents must "
      "be at least 200 dpi. Combined uploads exceeding 10 MB are rejected by the portal.", BODY),

    p("7. ASSESSMENT", H2),
    p("Components are weighted: Motivation 30%, Contribution Plan 30%, Financial Need 20%, "
      "Biography 10%, Surat Pernyataan 10%. The optional Leadership Experience component carries no "
      "weight and is read only where the panel is otherwise unable to separate two applicants.", BODY),
]

SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=17*mm, rightMargin=17*mm, topMargin=15*mm, bottomMargin=15*mm,
    title="Beasiswa Mobilitas Internasional 2026 - Call for Applications",
).build(story)

print(f"{OUT}  ({OUT.stat().st_size:,} bytes)")
