from json import load
from random import sample
import os

# imports for inky
from PIL import Image, ImageFont, ImageDraw
from inky.auto import auto
inky_display = auto()

PATH = os.path.dirname(__file__)
fontpath = os.path.join(PATH, "04B03.TTF")
title_font = ImageFont.truetype(fontpath, 16)
subtitle_font = ImageFont.truetype(fontpath, 8)

# Card names for the Major Arcana in their specific order (0-21)
CARD_NAMES = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
]

with open(os.path.join(PATH, "tarot-text.json"), "r") as f:
    data = load(f)

cards = sample(range(22), 2)  # Randomly select two different numbers that represent cards from the Major Arcana
cards.sort()  # Sort to match the JSON key format
card1, card2 = cards[0], cards[1]
combo_key = f"{card1}-{card2}"
arcana = data[combo_key]  # lookup combination text, which contains a title, subtitle, and classification

# set up image and draw background
img = Image.open(os.path.join(PATH, "black.png"))
draw = ImageDraw.Draw(img)

def load_card_image(card_number):
    """Load a card image. Expects images named like '00_the_fool.png' in a folder called 'cards'."""
    card_path = os.path.join(PATH, "cards", f"{card_number:02d}_{CARD_NAMES[card_number].lower().replace(' ', '_')}.png")
    return Image.open(card_path)

card1_img = load_card_image(card1)
card2_img = load_card_image(card2)

# Position cards
card1_x = 1
card2_x = 231
card_y = 19

img.paste(card1_img, (card1_x, card_y))
img.paste(card2_img, (card2_x, card_y))

# Draw "subtitle" text - actually this is the biggest text at the top of the display
draw.text((200, 2), arcana["subtitle"], inky_display.WHITE, title_font, anchor="mt")

# Draw "headline" text, which is actually the smaller text below the title
draw.text(
    (200, 20),
    arcana["headline"],
    inky_display.WHITE,
    subtitle_font,
    anchor="ma",
    stroke_width=2,
    stroke_fill="black",
)

# Draw the card numbers either side of each card
draw.text(
    (5, 20),
    str(card1),
    inky_display.RED,
    subtitle_font,
    anchor="lt"
)
draw.text(
    (395, 20),
    str(card2),
    inky_display.RED,
    subtitle_font,
    anchor="rt"
)

# Draw classification (vertically, letter by letter)
char_height = 16  # Gap between characters
start_y = 50

for i, char in enumerate(arcana["classification"]):
    draw.text(
        (200, start_y + i * char_height), char, inky_display.YELLOW, title_font, anchor="mt"
    )

inky_display.set_image(img)
inky_display.show()