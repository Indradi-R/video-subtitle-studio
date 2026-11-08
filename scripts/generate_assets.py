import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_app_assets():
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    size = 512
    # 1. Base image with transparency
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 2. Rounded square background with modern dark gradient
    padding = 24
    radius = 110
    
    # Draw gradient-like rounded background
    for i in range(size - padding * 2):
        ratio = i / (size - padding * 2)
        r = int(24 + (38 - 24) * ratio)
        g = int(28 + (46 - 28) * ratio)
        b = int(37 + (65 - 37) * ratio)
        # horizontal slice
        # for a clean look, draw the rounded rectangle first
    
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=radius,
        fill=(22, 27, 34, 255),
        outline=(56, 139, 253, 200),
        width=6
    )

    # Inner subtle glow border
    draw.rounded_rectangle(
        [padding + 8, padding + 8, size - padding - 8, size - padding - 8],
        radius=radius - 6,
        outline=(30, 41, 59, 255),
        width=3
    )

    # 3. Stylized Film Strip / Video Clapper on Top
    # Top clapper bar (angled or horizontal)
    clapper_y = 95
    clapper_h = 44
    draw.rounded_rectangle(
        [80, clapper_y, size - 80, clapper_y + clapper_h],
        radius=12,
        fill=(33, 38, 45, 255),
        outline=(75, 85, 99, 255),
        width=3
    )

    # Diagonal stripes on clapper
    stripe_w = 26
    for x in range(95, size - 95, stripe_w * 2):
        draw.polygon(
            [
                (x, clapper_y + clapper_h - 4),
                (x + 16, clapper_y + clapper_h - 4),
                (x + 30, clapper_y + 4),
                (x + 14, clapper_y + 4)
            ],
            fill=(59, 130, 246, 255)
        )

    # 4. Main Video Display Frame (Screen)
    screen_top = 155
    screen_bottom = 410
    draw.rounded_rectangle(
        [80, screen_top, size - 80, screen_bottom],
        radius=18,
        fill=(13, 17, 23, 255),
        outline=(59, 130, 246, 220),
        width=4
    )

    # Play button in center
    play_cx, play_cy = size // 2, (screen_top + screen_bottom) // 2 - 25
    play_size = 32
    draw.polygon(
        [
            (play_cx - 16, play_cy - play_size),
            (play_cx - 16, play_cy + play_size),
            (play_cx + 28, play_cy)
        ],
        fill=(56, 189, 248, 230)
    )

    # 5. Subtitle Banner / CC Pill at bottom of screen
    sub_w = 280
    sub_h = 60
    sub_x0 = (size - sub_w) // 2
    sub_y0 = screen_bottom - sub_h - 18
    draw.rounded_rectangle(
        [sub_x0, sub_y0, sub_x0 + sub_w, sub_y0 + sub_h],
        radius=14,
        fill=(31, 111, 235, 240),
        outline=(96, 165, 250, 255),
        width=2
    )

    # Draw [CC] and translation arrows inside subtitle pill
    # Draw stylized text lines or "SUB" & "ID"
    # Line 1: Audio waves / original language bar
    draw.rounded_rectangle([sub_x0 + 20, sub_y0 + 16, sub_x0 + 110, sub_y0 + 26], radius=4, fill=(255, 255, 255, 240))
    draw.rounded_rectangle([sub_x0 + 20, sub_y0 + 34, sub_x0 + 90, sub_y0 + 44], radius=4, fill=(203, 213, 225, 200))

    # Arrow ➔
    arrow_x = sub_x0 + 135
    arrow_y = sub_y0 + 30
    draw.line([(arrow_x - 12, arrow_y), (arrow_x + 10, arrow_y)], fill=(255, 255, 255, 255), width=4)
    draw.polygon([(arrow_x + 10, arrow_y - 8), (arrow_x + 20, arrow_y), (arrow_x + 10, arrow_y + 8)], fill=(255, 255, 255, 255))

    # Line 2: Translated target text bars (emerald/gold)
    draw.rounded_rectangle([sub_x0 + 165, sub_y0 + 16, sub_x0 + 260, sub_y0 + 26], radius=4, fill=(52, 211, 153, 255))
    draw.rounded_rectangle([sub_x0 + 165, sub_y0 + 34, sub_x0 + 240, sub_y0 + 44], radius=4, fill=(110, 231, 183, 220))

    # Save logo PNG
    logo_path = assets_dir / "logo.png"
    img.save(str(logo_path), "PNG")
    print(f"[+] Saved logo to {logo_path}")

    # Save small logo
    small_path = assets_dir / "logo_small.png"
    img.resize((128, 128), Image.Resampling.LANCZOS).save(str(small_path), "PNG")
    print(f"[+] Saved small logo to {small_path}")

    # Save multi-resolution Windows ICO
    ico_path = assets_dir / "icon.ico"
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(str(ico_path), format="ICO", sizes=icon_sizes)
    print(f"[+] Saved Windows ICO to {ico_path}")

if __name__ == "__main__":
    create_app_assets()
