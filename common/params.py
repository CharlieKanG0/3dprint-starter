"""Make a part parameter overridable from the environment, for sweeps.

    V_DEPTH = param("V_DEPTH", 110.0)

    PARAM_V_DEPTH=130 ./venv/bin/python parts/<name>/<name>.py

The default stays the real value in the script. Use this only for the few
parameters worth sweeping (a depth, a pitch you haven't measured yet); every
other dimension stays a plain literal. The override takes its type from the
default, so a float default parses the env value as float.
"""

import os


def param(name: str, default):
    raw = os.environ.get(f"PARAM_{name}")
    return default if raw is None else type(default)(raw)
