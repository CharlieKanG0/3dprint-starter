# Updates and sharing

Your designs stay on your computer. This page covers getting toolbox
improvements, backing up your work, and suggesting a fix. You can ask Claude
to do any of it: *"get the latest toolbox updates"*, *"back up my designs"*.

## What's yours, and what's shared

- **Yours:** everything in `parts/` (except the example), `things/`,
  `PROJECT.md`, `common/printer.py` and `parts/BACKLOG.md`. These never leave
  your computer unless you put them somewhere yourself.
- **Shared toolbox:** everything else: the drawing, checking and viewing tools,
  Claude's instructions, these guides. It improves over time.

## Getting updates

If you set up with the copy-paste command from the README, getting the
latest toolbox is:

```sh
cd ~/3dprint && git pull
```

Or ask Claude: *"Get the latest toolbox updates."* Updates never overwrite
your designs, your saved measurements or your settings.

## Backing up your designs

Your designs live in one folder on one computer. To keep a copy safe, make a
**private** repository on GitHub (free) and point this folder at it. Ask
Claude: *"Help me back up my designs to a private GitHub repo."* It does
something like this:

```sh
git remote rename origin upstream          # the shared toolbox becomes "upstream"
git remote add origin https://github.com/<you>/my-3dprint.git
git config cad.upstream upstream
git push -u origin main                    # your designs + the toolbox, backed up
```

From then on, `./venv/bin/python scripts/upstream.py pull` brings in toolbox
updates instead of `git pull`.

## Suggesting an improvement

Found a better way of doing something, or did Claude fix a toolbox problem
while designing? Improvements to the toolbox (never your designs) can go back
to everyone:

- **Not the repo's owner?** Open a pull request on GitHub, or tell the owner.
- **The owner, or set up to share?**
  `./venv/bin/python scripts/upstream.py status` shows what's ready to share,
  and `push` publishes it. Only toolbox files are ever sent. If a change mixes
  toolbox files with a design, the design part is left out. A safety check
  blocks any push that would include your own files.

Claude keeps toolbox improvements and designs separate as it works, and asks
before sharing anything.

## Your own files inside the toolbox folders

Made a helper of your own inside a toolbox folder (say a file in `common/`
about your own hardware)? List its path in a file called `.upstream-private`,
one per line, and it counts as yours too.
