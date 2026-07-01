from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw


Size = tuple[int, int]
Color = tuple[int, int, int]
SUPPORTED_OUTPUT_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parse_size(value: str) -> Size:
    normalized = value.lower().replace(" ", "")
    if "x" not in normalized:
        raise argparse.ArgumentTypeError("screen size must look like 2940x1912")

    width_text, height_text = normalized.split("x", 1)
    try:
        width = int(width_text)
        height = int(height_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("screen width and height must be integers") from exc

    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("screen width and height must be positive")

    return width, height


def parse_color(value: str) -> Color:
    named = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
    }
    if value.lower() in named:
        return named[value.lower()]

    text = value.strip()
    if text.startswith("#"):
        text = text[1:]

    if len(text) != 6:
        raise argparse.ArgumentTypeError("color must be a name or hex value like #000000")

    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("color must be a name or hex value like #000000") from exc


def main_screen_metrics() -> tuple[Size, int]:
    try:
        from AppKit import NSScreen
    except ImportError as exc:
        raise RuntimeError(
            "Could not import AppKit. On macOS, install dependencies with `uv sync`."
        ) from exc

    screen = NSScreen.mainScreen()
    if screen is None:
        raise RuntimeError("Could not read the main screen.")

    frame = screen.frame()
    visible_frame = screen.visibleFrame()
    scale = screen.backingScaleFactor()
    width = round(frame.size.width * scale)
    height = round(frame.size.height * scale)

    frame_top = frame.origin.y + frame.size.height
    visible_top = visible_frame.origin.y + visible_frame.size.height
    top_bar_height = round(max(0, frame_top - visible_top) * scale)

    return (int(width), int(height)), int(top_bar_height)


def scaled_bar_height(native_size: Size, output_size: Size, native_bar_height: int) -> int:
    if native_bar_height <= 0:
        return 0

    _, native_height = native_size
    _, output_height = output_size
    scale = output_height / native_height
    return max(1, round(native_bar_height * scale))


def default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.notchmask.png")


def cover_image(image: Image.Image, size: Size) -> Image.Image:
    target_width, target_height = size
    source_width, source_height = image.size
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_width = round(source_height * target_ratio)
        left = (source_width - crop_width) // 2
        box = (left, 0, left + crop_width, source_height)
    else:
        crop_height = round(source_width / target_ratio)
        top = (source_height - crop_height) // 2
        box = (0, top, source_width, top + crop_height)

    return image.crop(box).resize(size, Image.Resampling.LANCZOS)


def contain_image(image: Image.Image, size: Size, background: Color) -> Image.Image:
    target = Image.new("RGB", size, background)
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    left = (size[0] - fitted.size[0]) // 2
    top = (size[1] - fitted.size[1]) // 2
    target.paste(fitted, (left, top))
    return target


def draw_notch_mask(
    image: Image.Image,
    bar_height: int,
    bar_color: Color,
    corner_radius: int,
) -> Image.Image:
    if bar_height <= 0:
        return image

    width, height = image.size
    bar_height = min(bar_height, height)
    radius = min(max(0, corner_radius), width // 2, bar_height)

    if radius == 0:
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, bar_height), fill=bar_color)
        return image

    # Build the visible wallpaper area as one continuous shape, then invert it
    # into the black overlay mask. Restrict antialiasing work to the top strip.
    antialias_scale = 8
    antialias_padding = 4
    strip_height = min(height, bar_height + radius + antialias_padding)
    content_mask = Image.new(
        "L",
        (width * antialias_scale, strip_height * antialias_scale),
        0,
    )
    mask_draw = ImageDraw.Draw(content_mask)
    scaled_radius = radius * antialias_scale
    scaled_width = width * antialias_scale
    scaled_strip_height = strip_height * antialias_scale
    scaled_bar_height = bar_height * antialias_scale

    mask_draw.rectangle(
        (scaled_radius, scaled_bar_height, scaled_width - scaled_radius, scaled_strip_height),
        fill=255,
    )
    mask_draw.rectangle(
        (0, scaled_bar_height + scaled_radius, scaled_width, scaled_strip_height),
        fill=255,
    )
    mask_draw.pieslice(
        (0, scaled_bar_height, scaled_radius * 2, scaled_bar_height + scaled_radius * 2),
        180,
        270,
        fill=255,
    )
    mask_draw.pieslice(
        (
            scaled_width - scaled_radius * 2,
            scaled_bar_height,
            scaled_width,
            scaled_bar_height + scaled_radius * 2,
        ),
        270,
        360,
        fill=255,
    )

    content_mask = content_mask.resize((width, strip_height), Image.Resampling.LANCZOS)
    top_mask = content_mask.point(lambda value: 255 - value)
    mask = Image.new("L", image.size, 0)
    mask.paste(top_mask, (0, 0))
    overlay = Image.new("RGB", image.size, bar_color)
    return Image.composite(overlay, image, mask)


def save_image(image: Image.Image, output_path: Path, quality: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()

    if suffix not in SUPPORTED_OUTPUT_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_OUTPUT_SUFFIXES))
        raise ValueError(f"Unsupported output format '{suffix or '(none)'}'. Use one of: {supported}")

    if suffix in {".jpg", ".jpeg"}:
        image.save(output_path, quality=quality, subsampling=0, optimize=True)
    else:
        image.save(output_path)


def set_wallpaper(image_path: Path) -> None:
    try:
        from AppKit import NSScreen, NSURL, NSWorkspace
    except ImportError as exc:
        raise RuntimeError(
            "Could not import AppKit. On macOS, install dependencies with `uv sync`."
        ) from exc

    screen = NSScreen.mainScreen()
    if screen is None:
        raise RuntimeError("Could not read the main screen.")

    url = NSURL.fileURLWithPath_(str(image_path.resolve()))
    # Empty options asks macOS to use its default desktop image placement.
    ok, error = NSWorkspace.sharedWorkspace().setDesktopImageURL_forScreen_options_error_(
        url,
        screen,
        {},
        None,
    )
    if not ok:
        raise RuntimeError(f"Could not set wallpaper: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notchmask",
        description="Generate a macOS wallpaper with a black top notch/menu-bar mask.",
    )
    parser.add_argument("input", type=Path, nargs="?", help="input image")
    parser.add_argument("-o", "--output", type=Path, help="output image path")
    parser.add_argument("--screen", type=parse_size, help="output size in pixels, like 2940x1912")
    parser.add_argument(
        "--bar-height",
        type=int,
        help="top black bar height in pixels; defaults to the macOS menu-bar/notch height",
    )
    parser.add_argument(
        "--corner-radius",
        type=int,
        default=20,
        help="top corner radius of the visible wallpaper area",
    )
    parser.add_argument("--bar-color", type=parse_color, default=(0, 0, 0), help="bar color name or hex")
    parser.add_argument("--background", type=parse_color, default=(0, 0, 0), help="contain mode background")
    parser.add_argument("--fit", choices=["cover", "contain"], default="cover", help="image fitting mode")
    parser.add_argument(
        "--quality",
        type=int,
        default=100,
        help="JPEG output quality; only used for .jpg/.jpeg output",
    )
    parser.add_argument("--set-wallpaper", action="store_true", help="set output as the main screen wallpaper")
    parser.add_argument("--print-screen", action="store_true", help="print detected main screen size and exit")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        native_screen_size, native_bar_height = main_screen_metrics()
        screen_size = args.screen or native_screen_size
        bar_height = (
            args.bar_height
            if args.bar_height is not None
            else scaled_bar_height(native_screen_size, screen_size, native_bar_height)
        )

        if args.print_screen:
            print(f"screen={screen_size[0]}x{screen_size[1]}")
            print(f"bar_height={bar_height}")
            return 0

        if args.input is None:
            parser.error("input image is required unless --print-screen is used")

        input_path = args.input.expanduser()
        if not input_path.exists():
            raise FileNotFoundError(f"Input image does not exist: {input_path}")

        output_path = (args.output or default_output_path(input_path)).expanduser()

        source = Image.open(input_path).convert("RGB")
        if args.fit == "cover":
            wallpaper = cover_image(source, screen_size)
        else:
            wallpaper = contain_image(source, screen_size, args.background)

        wallpaper = draw_notch_mask(
            wallpaper,
            bar_height=bar_height,
            bar_color=args.bar_color,
            corner_radius=max(0, args.corner_radius),
        )

        save_image(wallpaper, output_path, args.quality)

        if args.set_wallpaper:
            set_wallpaper(output_path)

        print(output_path)
        return 0
    except Exception as exc:
        print(f"notchmask: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(run())
