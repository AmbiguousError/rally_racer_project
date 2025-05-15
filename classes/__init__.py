# classes/__init__.py
# This file makes the 'classes' directory a Python package.
# It can also be used to make imports from the package cleaner by exposing selected classes.

# Import the main classes from each module within the 'classes' directory
# so they can be imported directly from the 'classes' package.
# For example, `from classes import Car` instead of `from classes.car import Car`.

from .car import Car
from .particle import Particle, DustParticle, MudParticle
from .track_elements import Ramp, MudPatch, Checkpoint

# You can list all classes you want to be easily accessible when importing from 'classes'
# This helps to create a cleaner API for your package.
__all__ = [
    "Car",
    "Particle", "DustParticle", "MudParticle",
    "Ramp", "MudPatch", "Checkpoint"
]
