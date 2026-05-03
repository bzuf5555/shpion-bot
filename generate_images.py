"""Har bir kategoriya uchun 3 ta xilma-xil rasm yaratadi."""
from PIL import Image, ImageDraw, ImageFont
import os, math

os.makedirs("images", exist_ok=True)

W, H = 800, 500

VARIANTS = [
    # Cars
    {"file": "images/cars_1.jpg",     "label": "CARS",        "bg": (18,18,28),   "accent": (220,50,50),   "shape": "car"},
    {"file": "images/cars_2.jpg",     "label": "CARS",        "bg": (10,25,10),   "accent": (50,220,80),   "shape": "car"},
    {"file": "images/cars_3.jpg",     "label": "CARS",        "bg": (25,15,5),    "accent": (255,165,0),   "shape": "car"},
    # Watches
    {"file": "images/watches_1.jpg",  "label": "WATCHES",     "bg": (20,15,10),   "accent": (212,175,55),  "shape": "watch"},
    {"file": "images/watches_2.jpg",  "label": "WATCHES",     "bg": (10,10,25),   "accent": (100,180,255), "shape": "watch"},
    {"file": "images/watches_3.jpg",  "label": "WATCHES",     "bg": (20,5,20),    "accent": (200,80,220),  "shape": "watch"},
    # Jobs
    {"file": "images/jobs_1.jpg",     "label": "JOBS",        "bg": (10,20,40),   "accent": (0,150,255),   "shape": "job"},
    {"file": "images/jobs_2.jpg",     "label": "JOBS",        "bg": (25,10,5),    "accent": (255,120,0),   "shape": "job"},
    {"file": "images/jobs_3.jpg",     "label": "JOBS",        "bg": (5,25,15),    "accent": (0,200,120),   "shape": "job"},
    # Bloggers
    {"file": "images/bloggers_1.jpg", "label": "BLOGGERS",    "bg": (25,10,35),   "accent": (180,0,255),   "shape": "blog"},
    {"file": "images/bloggers_2.jpg", "label": "BLOGGERS",    "bg": (30,5,5),     "accent": (255,50,100),  "shape": "blog"},
    {"file": "images/bloggers_3.jpg", "label": "BLOGGERS",    "bg": (5,20,30),    "accent": (0,210,210),   "shape": "blog"},
    # 18+ Actress
    {"file": "images/actress_1.jpg",  "label": "18+ ACTRESS", "bg": (30,5,5),     "accent": (220,20,60),   "shape": "actress"},
    {"file": "images/actress_2.jpg",  "label": "18+ ACTRESS", "bg": (20,5,25),    "accent": (180,0,180),   "shape": "actress"},
    {"file": "images/actress_3.jpg",  "label": "18+ ACTRESS", "bg": (5,10,30),    "accent": (30,100,255),  "shape": "actress"},
]


def draw_gradient(draw, w, h, bg, accent):
    for y in range(h):
        t = y / h
        r = int(bg[0] + (accent[0] - bg[0]) * t * 0.3)
        g = int(bg[1] + (accent[1] - bg[1]) * t * 0.3)
        b = int(bg[2] + (accent[2] - bg[2]) * t * 0.3)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_shape(draw, shape, w, h, accent):
    dim = tuple(max(0, c - 80) for c in accent)

    if shape == "car":
        draw.rounded_rectangle([80, 280, 450, 360], radius=20, fill=dim)
        draw.rounded_rectangle([140, 240, 400, 290], radius=30, fill=dim)
        draw.ellipse([100, 345, 165, 390], fill=accent)
        draw.ellipse([360, 345, 425, 390], fill=accent)
        draw.ellipse([115, 355, 150, 380], fill=(30,30,30))
        draw.ellipse([375, 355, 410, 380], fill=(30,30,30))
        for i, y in enumerate(range(200, 420, 35)):
            draw.line([(500, y), (750, y - i*2)], fill=(*accent, 80), width=2)

    elif shape == "watch":
        cx, cy, r = 200, 310, 100
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=accent, width=8)
        draw.ellipse([cx-r+15, cy-r+15, cx+r-15, cy+r-15], fill=dim, outline=accent, width=4)
        draw.line([cx, cy, cx, cy-60], fill=accent, width=5)
        draw.line([cx, cy, cx+50, cy], fill=(255,255,255), width=3)
        draw.ellipse([cx-5, cy-5, cx+5, cy+5], fill=accent)
        draw.rounded_rectangle([cx-25, cy-r-40, cx+25, cy-r], radius=8, fill=dim)
        draw.rounded_rectangle([cx-25, cy+r, cx+25, cy+r+40], radius=8, fill=dim)

    elif shape == "job":
        bx, by = 130, 230
        draw.rounded_rectangle([bx, by+30, bx+220, by+160], radius=10, fill=dim, outline=accent, width=4)
        draw.rounded_rectangle([bx+60, by, bx+160, by+50], radius=8, outline=accent, width=4)
        draw.line([bx, by+95, bx+220, by+95], fill=accent, width=4)
        draw.rectangle([bx+95, by+80, bx+125, by+110], fill=accent)
        for i, val in enumerate([80, 130, 60, 110, 90]):
            x = 470 + i*50
            draw.rectangle([x, 400-val, x+30, 400], fill=accent if i == 1 else dim)

    elif shape == "blog":
        px, py = 130, 200
        draw.rounded_rectangle([px, py, px+130, py+220], radius=18, fill=dim, outline=accent, width=5)
        draw.rounded_rectangle([px+10, py+20, px+120, py+200], radius=6, fill=(10,10,20))
        draw.ellipse([px+55, py+205, px+75, py+215], fill=accent)
        for ox, oy, sz in [(380,240,40),(460,290,28),(420,350,35)]:
            draw.ellipse([ox, oy, ox+sz, oy+sz], outline=accent, width=3)
        for r2 in [30, 55, 80]:
            draw.arc([580-r2, 260-r2, 580+r2, 260+r2], -60, 60, fill=accent, width=3)

    elif shape == "actress":
        for fx in range(80, 650, 110):
            draw.rectangle([fx, 220, fx+90, 400], outline=accent, width=3)
            draw.rectangle([fx+8, 230, fx+82, 390], fill=dim)
            for fy in [225, 385]:
                for hx in range(fx+10, fx+85, 20):
                    draw.rectangle([hx, fy-5, hx+12, fy+5], fill=accent)
        cx2, cy2 = 680, 310
        pts = []
        for i in range(10):
            angle = math.pi/2 + i*2*math.pi/10
            r2 = 60 if i % 2 == 0 else 28
            pts.append((cx2 + r2*math.cos(angle), cy2 - r2*math.sin(angle)))
        draw.polygon(pts, fill=accent)


def make_image(v: dict):
    img = Image.new("RGB", (W, H), v["bg"])
    draw = ImageDraw.Draw(img)
    draw_gradient(draw, W, H, v["bg"], v["accent"])
    draw.rectangle([0, 0, W, 6], fill=v["accent"])
    draw.rectangle([0, H-6, W, H], fill=v["accent"])
    draw_shape(draw, v["shape"], W, H, v["accent"])

    try:
        font_big   = ImageFont.truetype("arialbd.ttf", 64)
        font_small = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font_big   = ImageFont.load_default(size=56)
        font_small = ImageFont.load_default(size=20)

    draw.text((W-20, 30), v["label"], font=font_big, fill=v["accent"], anchor="ra")
    lines = {
        "car":     ["Fast cars", "Speed & Style", "Who knows them best?"],
        "watch":   ["Luxury Timepieces", "Elegance & Precision", "Time is money"],
        "job":     ["Professions & Careers", "Work & Expertise", "What do you do?"],
        "blog":    ["Social Media Stars", "Content Creators", "Followers & Fame"],
        "actress": ["Film Industry", "Actresses & Stars", "Lights, Camera, Action!"],
    }
    for i, line in enumerate(lines[v["shape"]]):
        draw.text((W-20, H-110+i*32), line, font=font_small, fill=(200,200,200), anchor="ra")

    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    for x in range(W//2):
        alpha = int(60*(1-x/(W//2)))
        od.line([(x,0),(x,H)], fill=(0,0,0,alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(v["file"], "JPEG", quality=92)
    print(f"OK: {v['file']}")


if __name__ == "__main__":
    print("Rasmlar yaratilmoqda...")
    for v in VARIANTS:
        make_image(v)
    print("Tayyor! Jami:", len(VARIANTS), "ta rasm")
