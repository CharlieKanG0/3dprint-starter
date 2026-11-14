# Getting started

From nothing to your first printed part. No coding needed. Where you see a
grey box, copy the text, paste it into Terminal, and press Enter.

## 1. Install Claude Code

Claude Code is the AI that does the designing. You need a Claude account
(a paid plan such as Pro or Max). Install it by following the steps at
**[claude.com/claude-code](https://claude.com/claude-code)**.

How do you want to talk to it? Pick one:

- **Orca (recommended).** An app that shows Claude, your sketches and the 3D
  model side by side, so you see everything without switching windows.
- **Terminal.** Works fine. Sketches and 3D models open in your web browser.
- **VS Code.** If you already use it. Setup adds the 3D viewer panel for you.

You can change your mind later. Claude asks which you use on your first day.

## 2. Get this repo and set it up

Open the **Terminal** app (press Cmd+Space, type "Terminal", press Enter),
paste this, and press Enter:

```sh
git clone https://github.com/CharlieKanG0/3dprint-starter.git ~/3dprint && cd ~/3dprint && ./setup.sh
```

This creates a folder called `3dprint` in your home folder and installs
everything it needs inside it: a few minutes, mostly downloading. It finishes
by building the example design and printing **All set**.

- **A popup asks to install "command line developer tools"?** Click
  **Install**, wait for it to finish, then paste the command again.
- **Something else went wrong?** Run `cd ~/3dprint && ./setup.sh` again. It's
  safe to repeat, and it only redoes what's missing. If it still fails, copy
  the error into Claude and ask.

## 3. Open the folder in Claude Code

- **Orca:** add the `3dprint` folder to Orca as a project, then start a
  **Claude** agent in it.
- **Terminal:** `cd ~/3dprint && claude`
- **VS Code:** File → Open Folder → `3dprint`, then start Claude Code from the
  sidebar or the terminal panel.

## 4. Say hello, and let Claude set itself up

Type something like *"Hi, I'm new. Let's get set up."*

Claude asks a few quick questions: what printer you have, which materials you
like (PETG, ASA, PLA...), what kind of things you want to make, and how you're
running Claude. It writes your answers into `PROJECT.md` and
`common/printer.py`, so it remembers them in every future session. You don't
need to edit any files yourself.

## 5. Design your first part

Pick something small and useful for a first go: a hook, a clip, a holder.
Describe it, and include anything you know:

> *"I need a wall hook for my bike helmet. It screws into a wooden stud with
> two screws, and the helmet strap is about 25 mm wide. PETG. Here's a photo
> of the spot."*

What happens next:

1. **Claude asks what it still needs.** A size you didn't give, which way it
   faces, how it's used. Answer in plain words; "about 3 cm" is fine.
2. **Claude sketches two or three options** (A, B, C), shows them, and says
   which it recommends and why. Reply with a letter, plus any changes:
   *"A, but make the hook deeper."*
3. **Claude builds the 3D model** and opens it in the viewer. Drag to spin,
   scroll to zoom. Look at it from all sides.
4. **Claude reports back:** what it made, what it checked, which numbers are
   guesses you should measure, what screws or bolts to buy, and what to print
   first.

Want to see a finished example first? Ask Claude: *"Walk me through the
shower mount example."*

## 6. Print it

Your print files are in `parts/<your part>/`, ending in **`.step`**:

1. Open your slicer (Bambu Studio, OrcaSlicer, PrusaSlicer...).
2. Drag the `.step` file in. It's already the right way up for printing.
3. Choose your material and print as you normally would. Claude's summary
   says if a piece needs anything special.

If a design has several pieces, print the small critical one first (the clip,
the joint) to check the fit before printing everything.

## 7. Tell Claude how it fit

Measure if you can, and say what you saw:

> *"The clip is too loose on the handle, about 1 mm of play. The rest fits."*

Claude adjusts the design and builds it again. If your printer always prints
holes a little small or loose, Claude records that for every future part too.

## Next

- **[Designing a part](designing.md)**: good requests, photos, measuring,
  choosing options, fixing fits.
- **[Glossary](glossary.md)**: what STEP, slicer, tolerance and friends mean.
- **[Updates and sharing](sharing.md)**: getting toolbox improvements, keeping
  your designs private.
