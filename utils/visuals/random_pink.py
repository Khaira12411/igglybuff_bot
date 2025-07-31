import random

import discord


def get_random_pink() -> discord.Colour:
    pink_hexes = [
        "#F4C2C2",  # Baby Pink         | 0xF4C2C2 = 16040642
        "#FFD1DC",  # Pastel Pink       | 0xFFD1DC = 16765660
        "#FFBCD9",  # Cotton Candy      | 0xFFBCD9 = 16760537
        "#F9AFAE",  # Blush Pink        | 0xF9AFAE = 16372078
        "#FFE4E1",  # Misty Rose        | 0xFFE4E1 = 16770273
        "#DA70D6",  # Orchid            | 0xDA70D6 = 14315798
        "#FF69B4",  # Hot Pink          | 0xFF69B4 = 16738740
        "#FF1493",  # Deep Pink         | 0xFF1493 = 16716947
        "#FFA6C9",  # Carnation Pink    | 0xFFA6C9 = 16755273
        "#FFC1CC",  # Bubblegum Pink    | 0xFFC1CC = 16761036
        "#FF00FF",  # Fuchsia           | 0xFF00FF = 16711935
        "#FFB7C5",  # Cherry Blossom    | 0xFFB7C5 = 16757957
        "#FFB6C1",  # Light Pink        | 0xFFB6C1 = 16758465
        "#DE6FA1",  # Thulian Pink      | 0xDE6FA1 = 14596257
        "#FC89AC",  # Tickle Me Pink    | 0xFC89AC = 16551020
        "#FC8EAC",  # Flamingo Pink     | 0xFC8EAC = 16552364
        "#FFDDF4",  # Pink Lace         | 0xFFDDF4 = 16766452
        "#FC0FC0",  # Shocking Pink     | 0xFC0FC0 = 16515840
        "#F19CBB",  # Amaranth Pink     | 0xF19CBB = 15894203
        "#FDDDE6",  # Piggy Pink        | 0xFDDDE6 = 16698086
        "#C54B8C",  # Mulberry          | 0xC54B8C = 12968716
        "#F2C1D1",  # Fairy Tale        | 0xF2C1D1 = 15981201
        "#EFBBCC",  # Cameo Pink        | 0xEFBBCC = 15784652
        "#F88379",  # Tea Rose          | 0xF88379 = 16286585
        "#AA98A9",  # Rose Quartz       | 0xAA98A9 = 11180201
        "#FF6FFF",  # Ultra Pink        | 0xFF6FFF = 16742655
        "#CF6BA9",  # Super Pink        | 0xCF6BA9 = 13572905
        "#FD6C9E",  # French Pink       | 0xFD6C9E = 16549854
        "#D470A2",  # Wild Orchid       | 0xD470A2 = 13911266
        "#FFF0F5",  # Lavender Blush    | 0xFFF0F5 = 16773365
        "#E25098",  # Raspberry Pink    | 0xE25098 = 14811480
        "#E75480",  # Dark Pink         | 0xE75480 = 15132352
        "#FF77FF",  # Shocking Pink Lt  | 0xFF77FF = 16745343
        "#FF69B4",  # Hot Pink (again)  | 0xFF69B4 = 16738740
        "#FF5CCD",  # Pink Flamingo     | 0xFF5CCD = 16735117
        "#FFA07A",  # Light Salmon      | 0xFFA07A = 16752762
        "#FF91AF",  # Brilliant Pink    | 0xFF91AF = 16749615
    ]

    # Convert hex string to int and return discord.Colour
    color_ints = [int(c.lstrip("#"), 16) for c in pink_hexes]
    return discord.Colour(random.choice(color_ints))
