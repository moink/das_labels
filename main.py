import os

import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from brother_ql.backends import guess_backend, backend_factory
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
from slugify import slugify

# Operation mode
PREVIEW_MODE = False # Set to False to actually print labels
PREVIEW_METHOD = "matplotlib"  # Options: "pil" (basic), "matplotlib" (grid view)
SAVE_PREVIEWS = False  # Set to True to also save preview images to files
PREVIEW_SAVE_PATH = "label_previews"  # Folder to save preview images if SAVE_PREVIEWS is True
PREVIEW_COLUMNS = 10

# Font settings
LARGE_FONT = ImageFont.truetype("Inter-Bold.ttf", 75) # Name
SMALL_FONT = ImageFont.truetype("Inter-Regular.ttf", 50) # Category and t-shirt size

# Constants for layout
LABEL_SIZE = (991, 413)  # 38x90mm die-cut label, rotated to landscape
PRINTER_LABEL_SIZE = (LABEL_SIZE[1], LABEL_SIZE[0])
PADDING = 5  # Padding from edges
LOGO_COLOUR_MODE = "RGBA"
BACKGROUND_COLOUR = "white"
PRINT_COLOUR = "black"
LABEL_COLOUR_MODE = "RGB"
NAME_VERTICAL_POSITION = 200
_, DESCENT = SMALL_FONT.getmetrics()
BOTTOM_PADDING = PADDING + DESCENT

# File and device settings
# INPUT_DATA_PATH = "names.csv"  # Columns: Name, T-shirt size, Category
INPUT_DATA_PATH = "test.csv"  # Columns: Name, T-shirt size, Category
LOGO_IMAGE_PATH = "logo_bw.png"
PRINTER_MODEL = "QL-500"
PRINTER_ID = "usb://0x04f9:0x2015"  # QL-500 USB ID
LABEL_PAPER_SPEC = "39x90"  # Die-cut label specification

# Printer conversion settings
PRINT_THRESHOLD = 70  # B&W conversion threshold (0-255): lower = more black
PRINT_ROTATION = '0'  # Label rotation (0, 90, 180, 270 degrees)
PRINT_DITHER = False  # Use dithering for image conversion
PRINT_COMPRESSION = False  # Use compression in printer data
PRINT_RED = False  # Use red printing (for compatible printers)
PRINT_HIGH_DPI = False  # Use 600 DPI (instead of 300)
PRINT_CUT = True  # Cut the label after printing
selected_backend = guess_backend(PRINTER_ID)
BACKEND_CLASS = backend_factory(selected_backend)['backend_class']


def main():
    participants = pd.read_csv(INPUT_DATA_PATH)
    participants.fillna("", inplace=True)
    participants.sort_values("T-shirt size", inplace=True)
    qlr = BrotherQLRaster(PRINTER_MODEL)
    prep_preview_dir()
    preview_images = []
    blank_label_template = Image.new(LABEL_COLOUR_MODE, LABEL_SIZE, BACKGROUND_COLOUR)
    logo = get_resized_logo()
    for _, participant in participants.iterrows():
        draw, label_img = make_label_with_logo(blank_label_template, logo)
        add_name(draw, participant["Name"])
        add_participant_category(draw, participant["Category"])
        add_t_shirt_size(draw, participant["T-shirt size"])
        if PREVIEW_MODE:
            preview_image(label_img, participant["Name"])
            preview_images.append(label_img)
        else:
            print_label(label_img, participant["Name"], qlr)
    preview_grid(participants, preview_images)


def prep_preview_dir():
    if PREVIEW_MODE and SAVE_PREVIEWS and PREVIEW_SAVE_PATH:
        os.makedirs(PREVIEW_SAVE_PATH, exist_ok=True)


def get_resized_logo():
    logo_print_size = (LABEL_SIZE[0] - 2 * PADDING, LABEL_SIZE[1] - 2 * PADDING)
    logo_original = Image.open(LOGO_IMAGE_PATH).convert(LOGO_COLOUR_MODE)
    logo_original.thumbnail(logo_print_size)  # resize to fit
    return logo_original


def make_label_with_logo(blank_label_template, logo):
    logo_top_left_corner_coords = (PADDING, PADDING)
    label_img = blank_label_template.copy()
    draw = ImageDraw.Draw(label_img)
    label_img.paste(logo, logo_top_left_corner_coords, logo)
    return draw, label_img

def add_name(draw, name):
    width, _ = get_textsize(draw, name, LARGE_FONT)
    name_x = (LABEL_SIZE[0] - width) // 2
    draw.text(
        (name_x, NAME_VERTICAL_POSITION),
        name,
        fill=PRINT_COLOUR,
        font=LARGE_FONT
    )


def get_textsize(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def add_participant_category(draw, category_text):
    _, height = get_textsize(draw, category_text, SMALL_FONT)
    draw.text((PADDING, LABEL_SIZE[1] - height - BOTTOM_PADDING), category_text,
              fill=PRINT_COLOUR, font=SMALL_FONT)


def add_t_shirt_size(draw, tshirt_size):
    width, height = get_textsize(draw, tshirt_size, SMALL_FONT)
    draw.text(
        (LABEL_SIZE[0] - width - PADDING, LABEL_SIZE[1] - height - BOTTOM_PADDING),
        tshirt_size,
        fill=PRINT_COLOUR,
        font=SMALL_FONT
    )


def print_label(label_img, name, qlr):
    label_img = label_img.rotate(90, expand=True)
    instructions = convert(
        qlr,
        [label_img],
        label=LABEL_PAPER_SPEC,
        rotate=PRINT_ROTATION,
        threshold=PRINT_THRESHOLD,
        dither=PRINT_DITHER,
        compress=PRINT_COMPRESSION,
        red=PRINT_RED,
        dpi_600=PRINT_HIGH_DPI,
        cut=PRINT_CUT
    )
    send(instructions, PRINTER_ID, backend_identifier="pyusb")
    # be = BACKEND_CLASS(PRINTER_ID)
    # be.write(qlr.data)
    # be.dispose()
    # label = create_label(qlr, label_img, PRINTER_LABEL_SIZE, cut=False)
    print(f"Label printed: {name}")


def preview_image(label_img, name):
    if SAVE_PREVIEWS and PREVIEW_SAVE_PATH:
        save_preview(label_img, name)
    if PREVIEW_METHOD == "pil":
        label_img.show(title=f"Label Preview: {name}")


def save_preview(label_img, name):
    name_slug = slugify(name)
    preview_filename = os.path.join(PREVIEW_SAVE_PATH, f"{name_slug}.png")
    label_img.save(preview_filename)


def preview_grid(participants, preview_images):
    if PREVIEW_MODE and PREVIEW_METHOD == "matplotlib" and preview_images:
        # Calculate grid dimensions based on number of images
        num_images = len(preview_images)
        cols = min(PREVIEW_COLUMNS, num_images)
        rows = (num_images + cols - 1) // cols  # Ceiling division
        plt.figure(figsize=(15, 5 * rows))
        for i, img in enumerate(preview_images):
            plt.subplot(rows, cols, i + 1)
            plt.imshow(img)
            plt.axis('off')
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()