"""Rewrite README.md into a long description PyPI can render correctly.

PyPI's README renderer neither executes GitHub's live Mermaid code fences nor
resolves links relative to the repo tree, so the "How it works" diagram and
every ``docs/*.md`` link would show up broken on pypi.org. This script
produces a copy with the Mermaid block swapped for the static image built
from it (``docs/images/how-it-works.svg``) and every relative repo link
rewritten to an absolute GitHub URL. It never touches the git-tracked
README.md, so GitHub keeps the live, editable diagram and the working
relative links.

The publish workflow runs this against the CI checkout right before
``uv build``, so only the packaged long description is rewritten:

    uv run python scripts/render_pypi_readme.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_BLOB = "https://github.com/adanmauri/liveduino/blob/main/"

DIAGRAM_IMAGE = """<p align="center">
  <img src="https://raw.githubusercontent.com/adanmauri/liveduino/main/docs/images/how-it-works.svg"
       alt="Host Python (Board API, FirmataProtocol, Driver: serial/TCP/Bluetooth) talks to the Microcontroller (StandardFirmata, GPIO/ADC/PWM) and back"
       width="100%">
</p>"""

MERMAID_BLOCK = re.compile(r"```mermaid\n.*?\n```", re.DOTALL)
RELATIVE_LINK = re.compile(
    r"\]\((docs/[\w./-]+\.md|firmware/arduino/README\.md|AGENTS\.md|LICENSE)\)"
)


def render(text: str) -> str:
    """Return `text` with the Mermaid diagram and relative links made PyPI-safe."""
    text = MERMAID_BLOCK.sub(DIAGRAM_IMAGE, text)
    text = RELATIVE_LINK.sub(lambda m: f"]({REPO_BLOB}{m.group(1)})", text)
    return text


def main() -> None:
    readme = Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else readme)
    out.write_text(render(readme.read_text()))


if __name__ == "__main__":
    main()
