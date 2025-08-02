import random

import discord


def get_random_pink() -> discord.Colour:
    pastel_pink_hexes = [
        "#F4C2C2",  # Baby Pink
        "#FFD1DC",  # Pastel Pink
        "#FFBCD9",  # Cotton Candy
        "#F9AFAE",  # Blush Pink
        "#FFE4E1",  # Misty Rose
        "#FFA6C9",  # Carnation Pink
        "#FFC1CC",  # Bubblegum Pink
        "#FFB7C5",  # Cherry Blossom
        "#FFB6C1",  # Light Pink
        "#FFDDF4",  # Pink Lace
        "#F19CBB",  # Amaranth Pink
        "#FDDDE6",  # Piggy Pink
        "#F2C1D1",  # Fairy Tale
        "#EFBBCC",  # Cameo Pink
        "#FFF0F5",  # Lavender Blush
        "#FFE6EB",  # Light Blush
        "#FFEEF2",  # Cotton Flower
        "#FFF3F8",  # Shell Pink
        "#FFF1F3",  # Petal Pink
        "#FFDEE9",  # Dreamy Rose
        "#FCDDEC",  # Angel Pink
        "#FFE9EC",  # Cloud Pink
        "#F6D1D1",  # Soft Rose
        "#FEEEF4",  # Sugar Blossom
        "#FFECF5",  # Rosewater Mist
        "#F7C6D9",  # Ballet Slipper
        "#FBC8D9",  # Peach Pink
        "#FADADD",  # Pale Blush
        "#FFD6E8",  # Rose Milk
        "#FFE5EC",  # Blushed Petal
    ]

    color_ints = [int(c.lstrip("#"), 16) for c in pastel_pink_hexes]
    return discord.Colour(random.choice(color_ints))
