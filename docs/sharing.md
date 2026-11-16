# Updates and sharing

Your designs stay yours: on your computer, and (once you make one) in your
own **private** GitHub repository. This page covers backing up your work,
getting toolbox improvements, and suggesting a fix. You can ask Claude
to do any of it: *"get the latest toolbox updates"*, *"back up my designs"*.

## What's yours, and what's shared

- **Yours:** everything in `parts/` (except the example), `things/`,
  `PROJECT.md`, `common/printer.py` and `parts/BACKLOG.md`. These go only to
  your private backup, never to the shared toolbox.
- **Shared toolbox:** everything else: the drawing, checking and viewing tools,
  Claude's instructions, these guides. It improves over time.

## Three places your work lives

| Where | What goes there | When |
| --- | --- | --- |
| This folder, on your computer | everything | as you work |
| Your **private** GitHub repo (`origin`) | everything: designs, settings, unfinished work | after each finished change: *"back up my designs"* |
| The shared toolbox (`upstream`) | toolbox improvements only | when you choose to share one, as a pull request |

How a change travels:

```text
          YOUR COMPUTER                               GITHUB

  1. work on a branch
     (a design, or a toolbox fix)
              │
              │ merge when finished
              ▼                   2. backup            ┌────────────────────────┐
         your main  ─────────────────────────────────▶ │ origin                 │
          │     ▲                 everything           │ your PRIVATE repo      │
          │     │                                      └────────────────────────┘
          │     │                                      ┌────────────────────────┐
          │     │                 5. pull              │ upstream               │
          │     └───────────────────────────────────── │ the PUBLIC toolbox     │
          │                                            │                        │
          │                       3. push              │  "share" branch        │
          └──────────────────────────────────────────▶ │    │ pull request      │
                                  toolbox files only   │    ▼ 4. owner merges   │
                                                       │  main                  │
                                                       └────────────────────────┘
  6. backup again: the pull added to your main
```

Steps 3 to 5 happen only when a toolbox improvement is worth sharing; a new
design goes 1 → 2 and stops there.

## Backing up your designs

Until you make a backup, your designs live in one folder on one computer.
Ask Claude: *"Back up my designs to a private GitHub repo."* Once, it creates
the repository (private, free) and connects it:

```sh
./venv/bin/python scripts/upstream.py private          # makes github.com/<you>/3dprint, private
```

From then on, backing up is one command, and Claude runs it each time a
finished change lands on your `main`:

```sh
./venv/bin/python scripts/upstream.py backup           # main, every branch, nothing left behind
```

`./venv/bin/python scripts/upstream.py status` says what isn't backed up yet.
Both commands refuse a repository GitHub says is public. They need the GitHub
CLI (`brew install gh`, then `gh auth login`); without it, make a private
repository on github.com yourself and pass its address:
`upstream.py private https://github.com/<you>/3dprint.git`.

**On a second computer:** clone your private repo (not the toolbox), run
`./setup.sh`, then connect the toolbox once:
`./venv/bin/python scripts/upstream.py setup https://github.com/CharlieKanG0/3dprint-starter.git`.

## Getting updates

Ask Claude: *"Get the latest toolbox updates."* Updates never overwrite
your designs, your saved measurements or your settings. Before you have a
private repo, that is `git pull`; after, `git pull` fetches your own backup and
toolbox updates come with:

```sh
./venv/bin/python scripts/upstream.py pull      # then `backup`
```

## Suggesting an improvement

Found a better way of doing something, or did Claude fix a toolbox problem
while designing? Improvements to the toolbox (never your designs) can go back
to everyone:

- **Not the repo's owner?** Open a pull request on GitHub, or tell the owner.
- **The owner, or set up to share?**
  finish the change on its branch, merge it into your `main` and back it
  up: only what is on `main` is shared. Then
  `./venv/bin/python scripts/upstream.py status` shows what's ready to share,
  and `push` opens a **pull request** on the shared toolbox. Nothing reaches
  its `main` until you merge that pull request on GitHub (choose "Create a
  merge commit" or "Rebase and merge", not "Squash"); then `pull` brings it
  back here. Only toolbox files are ever sent. If a change mixes toolbox
  files with a design, the design part is left out. A safety check blocks
  any push that would include your own files.

Claude keeps toolbox improvements and designs separate as it works, and asks
before sharing anything. A second safety check refuses to save (commit) a
change that mixes the two, so they always land as separate steps.

## Your own files inside the toolbox folders

Made a helper of your own inside a toolbox folder (say a file in `common/`
about your own hardware)? List its path in a file called `.upstream-private`,
one per line, and it counts as yours too.
