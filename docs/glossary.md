# Glossary

Words you'll see in the agent's messages and in these guides, in plain terms.

**3D viewer.** The window where your model appears. You can spin, zoom, and hide
pieces. It opens on its own each time a design is built.

**Assembly.** Several parts shown together, sometimes with the thing they attach
to, so the agent can check they fit each other.

**ASSUMED.** A number the agent had to guess (from a photo, a diagram, or
"assume 3 cm"). Fine for a first print, but measure it before the final one.
Ask *"what's still assumed?"* for a list.

**Bed / print bed.** The flat plate your printer prints on. Every piece must fit
on it, and the agent checks this for your printer.

**Calipers.** A measuring tool for small sizes, accurate to a tenth of a millimetre.
The best $20 you'll spend on 3D printing.

**CF (as in PETG-CF, ASA-CF).** Plastic with carbon fibre mixed in. Stiffer and
more precise, but more brittle. Good for brackets; not for clips that flex.

**Chamfer.** A small angled edge. The agent adds one to the bottom edges of
parts so they don't curl up off the bed while printing.

**Clearance / fit.** The small gap between two things that go together, like a
bolt in a hole or a bar in a sleeve. Too small and it won't go in; too big and
it rattles. The agent starts with typical gaps and adjusts after your test
print.

**Heat-set insert.** A small brass nut you push into a printed hole with a hot
soldering iron, giving a strong metal thread in plastic.

**Layout / sketch.** The flat, labelled diagram the agent draws before
modelling, showing where the part sits and how it works. Options are lettered
A, B, C.

**M5, M6, M8...** Metric bolt sizes: the number is the thread diameter in
millimetres. M6 is about the thickness of a pencil.

**Mesh.** How a downloaded model is stored: a skin made of thousands of tiny
triangles. Unlike a CAD design it has no "hole" or "wall" you can change by
number, so the agent adds or cuts things on top of it. See
[Changing a model you downloaded](modifying.md).

**Nyloc nut.** A nut with a nylon ring inside, so it doesn't shake loose. Common on
moving joints.

**Overhang / supports.** Plastic printed over thin air sags. The agent designs
and orients parts so they print without support material wherever it can.

**PETG, ASA, PLA.** Common printing plastics. PLA: easy, but softens in heat and
sun. PETG: tougher, a good general choice. ASA: handles sun and heat, the pick
for cars and outdoors (best in an enclosed printer).

**Repo.** Short for repository: this project folder, with its full history. It
lives on your computer.

**3MF file (`.3mf`).** A 3D file that MakerWorld and Bambu Studio use. It holds
the shape and, often, the creator's print settings. The agent reads both, and
writes a shape-only `.3mf` for models it modifies.

**Slicer.** The app that turns a 3D file into printer instructions: Bambu Studio,
OrcaSlicer, PrusaSlicer, Cura...

**STEP file (`.step`).** The 3D shape file the agent makes for each piece. Drag
it into your slicer. More precise than STL, and every modern slicer opens it.

**Watertight.** A mesh whose skin is fully closed, with no gaps, so it is a true
solid. Needed before the agent can add or cut anything on a downloaded model.

**T-channel / T-slot.** The slotted rail on roof racks and aluminium frames, into
which special nuts slide so you can bolt things on anywhere along it.

**Things (`things/`).** Your saved measurements of real objects your parts
attach to, so the agent never has to ask twice.

**Tolerance.** How far off a printed size can be from the design. Printers are
usually within a few tenths of a millimetre, which is why fits get tested.
