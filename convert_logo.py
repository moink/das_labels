from PIL import Image

from main import LOGO_COLOUR_MODE

WHITE = (255, 255, 255)
ORIGINAL_FILE = "cropped-Das-25-BW-Pink-Splash.png"


def main():
    logo = Image.open(ORIGINAL_FILE).convert(LOGO_COLOUR_MODE)
    r, g, b, a = logo.split()
    rgb_logo = Image.merge("RGB", (r, g, b))
    bw_logo = rgb_logo.convert("L").point(lambda p: 0 if p < 255 else 255, mode='1')
    final_logo = Image.new("RGB", bw_logo.size, "white")
    final_logo.paste(bw_logo, mask=logo.split()[3])
    final_logo.save("logo_bw.png")


if __name__ == "__main__":
    main()