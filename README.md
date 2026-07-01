# NotchMask

Generate a macOS wallpaper whose top menu-bar/notch area is black.

NotchMask is a small command-line tool for notched MacBook displays. It takes an
input image, fits it to the current screen, paints the menu-bar/notch area black,
and optionally sets the result as the current wallpaper.

## Install

This project uses `uv`.

```bash
uv sync
```

## Quick Start

Generate a wallpaper:

```bash
uv run notchmask input.jpg
```

Generate and set it as the current main-screen wallpaper:

```bash
uv run notchmask input.jpg --set-wallpaper
```

By default, the output is written next to the input image as
`input.notchmask.png`. PNG is used by default so the black mask edge stays clean
and does not pick up JPEG compression artifacts.

## Defaults

| Setting | Default |
| --- | --- |
| Output size | Current main macOS screen in physical pixels |
| Image fitting | `cover` |
| Top black bar height | Current macOS menu-bar/notch height |
| Corner radius | `20` physical pixels |
| Bottom corner radius | `20` physical pixels |
| Output format | PNG |
| JPEG quality | `100` |

## Options

| Option | Meaning | Default |
| --- | --- | --- |
| `input` | Input image path. | Required unless `--print-screen` is used |
| `-o, --output PATH` | Output image path. Supported extensions are `.png`, `.jpg`, and `.jpeg`. | `input.notchmask.png` |
| `--screen WIDTHxHEIGHT` | Output wallpaper size in pixels, for example `2940x1912`. | Auto-detected main screen size |
| `--bar-height PX` | Height of the black top mask in output pixels. | Auto-detected menu-bar/notch height |
| `--corner-radius PX` | Top corner radius of the visible wallpaper area. Use `0` to disable rounded corners. | `20` |
| `--bottom-corner-radius PX` | Bottom corner radius of the visible wallpaper area. Use `0` to disable bottom rounded corners. | `20` |
| `--bar-color COLOR` | Color of the top mask. Supports `black`, `white`, or hex like `#000000`. | `black` |
| `--fit cover` | Fill the whole output size and crop overflow from the center. | Default fit mode |
| `--fit contain` | Keep the full input image visible and fill empty space with `--background`. | Off |
| `--background COLOR` | Background color used by `--fit contain`. Supports names or hex. | `black` |
| `--quality N` | JPEG quality. Only used when output ends with `.jpg` or `.jpeg`. PNG ignores it. | `100` |
| `--set-wallpaper` | Set the generated image as the current main-screen wallpaper. | Off |
| `--print-screen` | Print the detected output size and bar height, then exit. | Off |

## Examples

Use the recommended defaults:

```bash
uv run notchmask input.jpg
```

Generate and set the wallpaper:

```bash
uv run notchmask input.jpg --set-wallpaper
```

Write to a specific file:

```bash
uv run notchmask input.jpg -o output.png
```

Disable rounded corners:

```bash
uv run notchmask input.jpg --corner-radius 0
```

Disable bottom rounded corners:

```bash
uv run notchmask input.jpg --bottom-corner-radius 0
```

Use a custom output size:

```bash
uv run notchmask input.jpg --screen 2560x1664
```

Keep the whole image visible instead of cropping:

```bash
uv run notchmask input.jpg --fit contain --background black
```

Output JPEG at maximum quality:

```bash
uv run notchmask input.jpg -o output.jpg
```

## Screen Detection

Check what NotchMask detects:

```bash
uv run notchmask --print-screen
```

Example output:

```text
screen=2940x1912
bar_height=76
```

If you pass `--screen`, the automatic bar height is scaled to the requested
output size. You can still override it with `--bar-height`.
