# NotchMask

Generate a macOS wallpaper whose top menu-bar/notch area is black.

## Usage

Install dependencies and run:

```bash
uv run notchmask input.jpg
```

By default, the output is written next to the input image as
`input.notchmask.png`. PNG is used by default so the black mask edge stays
clean and does not pick up JPEG compression artifacts.

Useful options:

```bash
uv run notchmask input.jpg -o output.jpg
uv run notchmask input.jpg --set-wallpaper
uv run notchmask input.jpg --bar-height 88 --corner-radius 24
uv run notchmask input.jpg --screen 2940x1912
uv run notchmask input.jpg --fit contain --background black
```

Defaults:

- screen size: current main macOS screen in physical pixels
- fit mode: `cover`, which fills the screen and crops excess image area
- top black bar height: current macOS menu-bar/notch height
- corner radius: `24` physical pixels; pass `--corner-radius 0` to disable it
- output format: PNG by default; JPEG output uses quality `100`

If the automatic screen size is not what you expect, run:

```bash
uv run notchmask input.jpg --print-screen
```

Then pass the exact wallpaper pixel size with `--screen`. If you pass `--screen`,
the automatic bar height is scaled to the output size. You can still override it
with `--bar-height`.
