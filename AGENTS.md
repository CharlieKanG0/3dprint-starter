# Instructions for coding agents

The workflow for this repo is in `CLAUDE.md`, and who it belongs to is in
`PROJECT.md`. Read both before doing anything. The rule that matters most:
a design request starts with questions and lettered layout sketches
(`parts/<name>/layout.py`), never with geometry -- part scripts refuse to
build until `layout.py` records the user's confirmed choice.
