"""newmap01 programmatic loader removed.

This module used to provide an in-repo programmatic map called `newmap01`.
The map was removed from the project; the loader now raises an explicit
RuntimeError so calling code fails fast and can be updated.
"""

def load_newmap(*args, **kwargs):
    raise RuntimeError('load_newmap: newmap01 has been removed from the project')
