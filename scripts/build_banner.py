"""Render the README banner from assets/logo.png, dark and light.

    uv run python scripts/build_banner.py

Writes assets/banner-dark.png and assets/banner-light.png at 2560x1120 (2x).
Text is rasterised by headless Chrome, so the wordmark looks the same for
everyone regardless of the fonts they have. Edit WORDMARK or LINES below and
re-run; README.md picks the variant up through its <picture> element.
"""

import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "logo.png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

WORDMARK = "Berkas"
# (text, which colour role) — "l2" is the deterministic beat, and it is the one
# that gets the accent, because compliance.py is the claim this project makes.
LINES = [("The model perceives.", "l1"), ("Code decides.", "l2"), ("You confirm.", "l3")]

THEMES = {
    "dark": dict(BG="#0A0E16", GLOW="rgba(48,142,252,0.20)", SHADOW="rgba(0,0,0,0.55)",
                 WORD="#EAF0F8", L1="#C2D0E2", L2="#3FCF8E", L3="#59697F"),
    "light": dict(BG="#F6F8FC", GLOW="rgba(48,142,252,0.14)", SHADOW="rgba(15,35,70,0.18)",
                  WORD="#0F1721", L1="#33415A", L2="#0E8F58", L3="#8A98AB"),
}

TEMPLATE = """<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { width:1280px; height:560px; background:{BG}; overflow:hidden;
         font-family:"Avenir Next","Avenir",-apple-system,sans-serif;
         -webkit-font-smoothing:antialiased; }
  .glow { position:absolute; left:150px; top:80px; width:400px; height:400px;
          background:radial-gradient(circle, {GLOW} 0%, transparent 68%); }
  .wrap { position:relative; height:100%; display:flex; align-items:center;
          justify-content:center; gap:92px; }
  .logo { width:296px; height:296px; filter:drop-shadow(0 24px 48px {SHADOW}); }
  .word { font-size:98px; font-weight:700; letter-spacing:-2.5px; color:{WORD};
          line-height:1; margin-bottom:26px; }
  .tag  { font-size:39px; font-weight:500; line-height:1.44; letter-spacing:-0.4px; }
  .l1 { color:{L1}; } .l2 { color:{L2}; } .l3 { color:{L3}; }
</style>
<div class="glow"></div>
<div class="wrap">
  <img class="logo" src="data:image/png;base64,{B64}">
  <div><div class="word">{WORDMARK}</div>{TAGLINES}</div>
</div>"""


def main() -> None:
    b64 = base64.b64encode(LOGO.read_bytes()).decode()
    taglines = "".join(f'<div class="tag {role}">{text}</div>' for text, role in LINES)

    for name, colours in THEMES.items():
        html = TEMPLATE
        for key, value in colours.items():
            html = html.replace("{%s}" % key, value)
        html = html.replace("{WORDMARK}", WORDMARK).replace("{TAGLINES}", taglines)
        html = html.replace("{B64}", b64)

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
            fh.write(html)
            source = fh.name

        out = ROOT / "assets" / f"banner-{name}.png"
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--screenshot={out}", "--window-size=1280,560",
             "--force-device-scale-factor=2", f"file://{source}"],
            check=True, capture_output=True,
        )
        Path(source).unlink()
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
