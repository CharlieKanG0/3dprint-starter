"""Shared clearance allowances for FDM-printed mating features.

Starting points for the printer in common/printer.py (0.4mm nozzle unless
a part says otherwise) in PETG / ASA / their CF blends. These are not measured
for your specific filament spool/printer combo -- validate empirically and
update the values here (not inline in a part script) when you learn better
ones.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FitClearance:
    radial: float  # add to a hole/socket radius, or split across both sides of a slot


# Radial clearance to add to a nominal mating radius, by fit class.
FIT: dict[str, FitClearance] = {
    "press": FitClearance(radial=0.05),  # light interference-free press fit
    "slip": FitClearance(radial=0.15),  # hand-assembled, no perceptible play
    "loose": FitClearance(radial=0.30),  # free-running, e.g. a shaft/rod cradle
}
