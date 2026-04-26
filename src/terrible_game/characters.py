"""Playable character definitions — each starts with one weapon at level 1."""
from .weapons import PencilWand, CoffeeBomb, TextbookOrbit

CHARACTERS = (
    {
        "id": "studious",
        "name": "The Studious",
        "tagline": "Steady aim through every deadline.",
        "weapon_class": PencilWand,
    },
    {
        "id": "wired",
        "name": "The Wired",
        "tagline": "When the room spins, the bombs don’t care.",
        "weapon_class": CoffeeBomb,
    },
    {
        "id": "scholar",
        "name": "The Scholar",
        "tagline": "Let the books do the shoving for you.",
        "weapon_class": TextbookOrbit,
    },
)


def starting_weapon_class(index: int):
    if not CHARACTERS:
        return PencilWand
    i = int(index) % len(CHARACTERS)
    return CHARACTERS[i]["weapon_class"]
