"""<Thing name> -- <one line: what it is and what your parts do with it>.

Copy to things/<name>.py (`./venv/bin/python scripts/new.py thing <name>` does it). Parts
import from here (`from things.<name> import WIDTH`), so each number lives in one place:
correct it here and every part that uses it rebuilds against the new value.

Photos: things/photos/<name>_*.jpg (installed-state photos settle orientation).

Every constant gets a source tag as the first word of its comment, then where it came from:
  MEASURED   you measured it (say how, and the date)
  DATASHEET  a maker's spec page, drawing or manual (name it, or the URL)
  GIVEN      the owner stated it
  ASSUMED    a guess or a scale-off -- `scripts/things.py` lists these as "still to measure"
"""

# WIDTH = 70.0  # MEASURED 2026-01-31, calipers across the top face
# HEIGHT = 40.0  # ASSUMED -- read off the photo, measure it


# Optional: reference geometry for sketches and assemblies, built from the numbers above.
# def profile():
#     from build123d import Rectangle
#     return Rectangle(WIDTH, HEIGHT)
