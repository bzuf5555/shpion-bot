"""Har bir kategoriya uchun rasm yaratadi va images/ papkasiga saqlaydi."""
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("images", exist_ok=True)

W, H = 800, 500

CATEGORIES = [
    {
        "file":    "cars.jpg",
        "label":   "CARS",
        "emoji":   "🚗",
        "bg":      (18, 18, 28),
        "accent":  (220, 50, 50),
        "lines":   ["Fast cars", "Speed & Style", "Who knows them best?"],
        "shapes":  "car",
    },
    {
        "file":    "watches.jpg",
        "label":   "WATCHES",
        "emoji":   "⌚",
        "bg":      (20, 15, 10),
        "accent":  (212, 175, 55),
        "lines":   ["Luxury Timepieces", "Elegance & Precision", "Time is money"],
        "shapes":  "watch",
    },
    {
        "file":    "jobs.jpg",
        "label":   "JOBS",
        "emoji":   "💼",
        "bg":      (10, 20, 40),
        "accent":  (0, 150, 255),
        "lines":   ["Professions & Careers", "Work & Expertise", "What do you do?"],
        "shapes":  "job",
    },
    {
        "file":    "bloggers.jpg",
        "label":   "BLOGGERS",
        "emoji":   "📱",
        "bg":      (25, 10, 35),
        "accent":  (180, 0, 255),
        "lines":   ["Social Media Stars", "Content Creators", "Followers & Fame"],
        "shapes":  "blog",
    },
    {
        "file":    "actress.jpg",
        "label":   "18+ ACTRESS",
        "emoji":   "🎬",
        "bg":      (30, 5, 5),
        "accent":  (220, 20, 60),
        "lines":   ["Film Industry", "Actresses & Stars", "Lights, Camera, Action!"],
        "shapes":  "actress",
    },
]


def hex_to_rgba(color, alpha=255):
    r, g, b = color
    return (r, g, b, alpha)


def draw_gradient(draw, w, h, bg, accent):
    for y in range(h):
        t = y / h
        r = int(bg[0] + (accent[0] - bg[0]) * t * 0.3)
        g = int(bg[1] + (accent[1] - bg[1]) * t * 0.3)
        b = int(bg[2] + (accent[2] - bg[2]) * t * 0.3)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_decorations(draw, shape, w, h, accent):
    a = accent
    dim = tuple(max(0, c - 80) for c in a)

    if shape == "car":
        # Simplified car silhouette using rectangles/ellipses
        draw.rounded_rectangle([80, 280, 450, 360], radius=20, fill=dim)
        draw.rounded_rectangle([140, 240, 400, 290], radius=30, fill=dim)
        draw.ellipse([100, 345, 165, 390], fill=a)
        draw.ellipse([360, 345, 425, 390], fill=a)
        draw.ellipse([115, 355, 150, 380], fill=(30, 30, 30))
        draw.ellipse([375, 355, 410, 380], fill=(30, 30, 30))
        # Speed lines
        for i, y in enumerate(range(200, 420, 35)):
            draw.line([(500, y), (750, y - i * 2)], fill=(*a, 80), width=2)

    elif shape == "watch":
        cx, cy, r = 200, 310, 100
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=a, width=8)
        draw.ellipse([cx-r+15, cy-r+15, cx+r-15, cy+r-15], fill=dim, outline=a, width=4)
        draw.line([cx, cy, cx, cy - 60], fill=a, width=5)   # hour
        draw.line([cx, cy, cx + 50, cy], fill=(255,255,255), width=3)  # minute
        draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill=a)
        # Strap
        draw.rounded_rectangle([cx-25, cy-r-40, cx+25, cy-r], radius=8, fill=dim)
        draw.rounded_rectangle([cx-25, cy+r, cx+25, cy+r+40], radius=8, fill=dim)

    elif shape == "job":
        # Briefcase
        bx, by = 130, 230
        draw.rounded_rectangle([bx, by+30, bx+220, by+160], radius=10, fill=dim, outline=a, width=4)
        draw.rounded_rectangle([bx+60, by, bx+160, by+50], radius=8, outline=a, width=4)
        draw.line([bx, by+95, bx+220, by+95], fill=a, width=4)
        draw.rectangle([bx+95, by+80, bx+125, by+110], fill=a)
        # Bar chart
        for i, val in enumerate([80, 130, 60, 110, 90]):
            x = 470 + i * 50
            draw.rectangle([x, 400 - val, x + 30, 400], fill=a if i == 1 else dim)

    elif shape == "blog":
        # Phone
        px, py = 130, 200
        draw.rounded_rectangle([px, py, px+130, py+220], radius=18, fill=dim, outline=a, width=5)
        draw.rounded_rectangle([px+10, py+20, px+120, py+200], radius=6, fill=(10, 10, 20))
        draw.ellipse([px+55, py+205, px+75, py+215], fill=a)
        # Like / heart icons
        for ox, oy, sz in [(380, 240, 40), (460, 290, 28), (420, 350, 35)]:
            draw.ellipse([ox, oy, ox+sz, oy+sz], outline=a, width=3)
        # Signal waves
        for r2 in [30, 55, 80]:
            draw.arc([580-r2, 260-r2, 580+r2, 260+r2], -60, 60, fill=a, width=3)

    elif shape == "actress":
        # Film strip
        for fx in range(80, 650, 110):
            draw.rectangle([fx, 220, fx+90, 400], outline=a, width=3)
            draw.rectangle([fx+8, 230, fx+82, 390], fill=dim)
            for fy in [225, 385]:
                for hx in range(fx+10, fx+85, 20):
                    draw.rectangle([hx, fy-5, hx+12, fy+5], fill=a)
        # Star
        import math
        cx2, cy2 = 680, 310
        pts = []
        for i in range(10):
            angle = math.pi / 2 + i * 2 * math.pi / 10
            r2 = 60 if i % 2 == 0 else 28
            pts.append((cx2 + r2 * math.cos(angle), cy2 - r2 * math.sin(angle)))
        draw.polygon(pts, fill=a)


def make_image(cat: dict):
    img = Image.new("RGB", (W, H), cat["bg"])
    draw = ImageDraw.Draw(img)

    draw_gradient(draw, W, H, cat["bg"], cat["accent"])

    # Accent border lines
    draw.rectangle([0, 0, W, 6], fill=cat["accent"])
    draw.rectangle([0, H-6, W, H], fill=cat["accent"])

    draw_decorations(draw, cat["shapes"], W, H, cat["accent"])

    # Try to use a bold font, fall back to default
    try:
        font_big   = ImageFont.truetype("arialbd.ttf", 64)
        font_med   = ImageFont.truetype("arial.ttf",   28)
        font_small = ImageFont.truetype("arial.ttf",   22)
    except OSError:
        font_big   = ImageFont.load_default(size=56)
        font_med   = ImageFont.load_default(size=28)
        font_small = ImageFont.load_default(size=20)

    # Category label (top right area)
    label = cat["label"]
    draw.text((W - 20, 30), label, font=font_big, fill=cat["accent"], anchor="ra")

    # Sub-lines
    for i, line in enumerate(cat["lines"]):
        y = H - 110 + i * 32
        draw.text((W - 20, y), line, font=font_small, fill=(200, 200, 200), anchor="ra")

    # Dim overlay on left side for visual depth
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(W // 2):
        alpha = int(60 * (1 - x / (W // 2)))
        od.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    path = os.path.join("images", cat["file"])
    img.save(path, "JPEG", quality=92)
    print(f"  OK: {path}")


if __name__ == "__main__":
    print("Rasmlar yaratilmoqda...")
    for cat in CATEGORIES:
        make_image(cat)
    print("Tayyor!")
