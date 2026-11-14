# Designing a part

How to get the best out of designing with Claude. If you haven't set up yet,
start with **[Getting started](getting-started.md)**.

## Describe what you need

The more Claude knows up front, the fewer questions it asks. A good request says:

- **What it's for.** *"Hold a shower head on the side of my roof rack."*
- **What it attaches to,** and how: screws, bolts, clips, a slot or rail.
- **What it holds** or does: sizes, weight, how often it moves.
- **What matters to you.** *"Must fold away when driving"*, *"no visible
  screws"*, *"quick to remove"*.
- **Material,** if you know: PETG for general use, ASA for outdoors and in
  the sun, the "CF" versions for stiff, precise parts.

Don't worry about getting it all: Claude asks for what's missing. You can
also say *"assume the rest"*, and Claude picks sensible values and lists
every guess so you can check them later.

## Photos help more than words

- **Where it goes:** the spot it attaches to, from a little way back.
- **Up close:** the rail, slot, pipe or edge it clamps onto.
- **What it holds,** next to something for scale (your hand, a ruler, a coin).
- **The existing part,** if you're replacing or improving one.

**Product links work too.** Paste the link to something you bought (a shower
head, recovery boards, a bike light) and Claude reads the spec sheet and
photos itself before asking you anything.

## Measuring

Digital calipers make this easy. Measure in millimetres:

- **Round things** (handles, pipes, tubes): measure across, where the part
  will grip. Measure twice, in different directions.
- **Slots and rails:** the opening width, the width inside, and the depth.
- **Holes:** the inside diameter, and the distance between hole centres.
- **Distances:** a tape measure is fine for big things. Say "about".

Don't have calipers? A ruler and "about" works for a first try, and Claude
will design in a little extra room for adjustment.

## Choosing between options

Before modelling anything, Claude draws two or three **sketches**, labelled
A, B and C. They're flat diagrams with real sizes, showing where the part
sits and how it works. Claude recommends one and explains the trade-offs.

- **Reply with a letter.** *"B."*
- **Or a letter plus changes.** *"B, but put the knob on the other side."*
- **Or ask for something else.** *"None of these, can it clip on instead of bolting?"*

"Yes" isn't an answer to "A or B?". Claude will ask which one you mean.
If you add a new feature halfway through ("make it fold", "make it
telescopic"), Claude sketches options for that too before building it.

## Checking the 3D model

The model opens in a viewer (an Orca tab, VS Code, or your browser):

- **Drag** to spin, **scroll** to zoom. Press **5** for an angled view and **r** to fit it to the window.
- The list on the left shows each piece. Click the eye icon to hide one and
  see inside.
- Look for anything that doesn't match the real world: a knob that would hit
  the wall, a hole facing the wrong way, a part that looks too thin.

Say what you see in plain words: *"the knob is on the wrong side"*, *"can the
arm be thicker?"*

## Printing and testing the fit

- **Print the critical piece first,** the one that has to fit something
  (a clip, a joint, a pocket for a nut). It's quicker than printing the whole
  thing and finding one bit doesn't fit.
- Claude's summary lists **hardware to buy** (screws, bolts, nuts, springs,
  brass inserts) with sizes.
- **Report fits with numbers when you can:** *"loose by about 1 mm"*, *"the
  bolt won't go through"*, *"snaps on but too tight to remove"*.
- When something fits, say so. Claude marks the part as done.

## Measurements Claude remembers

When you describe something you'll design for again (your roof rack, your
desk, a rail), Claude offers to save its measurements in the **`things/`**
folder. After that, future parts use the saved numbers and Claude doesn't
ask again. Numbers that were guesses are marked, and Claude can list them:
ask *"what do I still need to measure?"* and it gives you a checklist for
your next go with the calipers.

## Tips

- **One part per conversation** keeps things clear. Claude remembers your
  printer, materials and saved measurements between conversations.
- **Ideas for later?** Ask Claude to *"add it to the backlog"*.
- **Start small.** A hook or clip teaches you the loop in one evening.
- **Ask why.** *"Why option B?"*, *"why is this part split in two?"* Claude
  explains its reasoning.
