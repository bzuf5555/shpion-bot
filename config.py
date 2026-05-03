import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))

# Ixtiyoriy: PostgreSQL ulash uchun (bo'lmasa SQLite ishlatiladi)
# Misol: postgresql://user:password@localhost:5432/shpion
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

CATEGORIES: list[str] = ["Cars", "Watches", "Jobs", "Bloggers", "18+ Actress"]

CATEGORY_IMAGES: dict[str, list[str]] = {
    "Cars":        ["images/cars_1.jpg",     "images/cars_2.jpg",     "images/cars_3.jpg"],
    "Watches":     ["images/watches_1.jpg",  "images/watches_2.jpg",  "images/watches_3.jpg"],
    "Jobs":        ["images/jobs_1.jpg",     "images/jobs_2.jpg",     "images/jobs_3.jpg"],
    "Bloggers":    ["images/bloggers_1.jpg", "images/bloggers_2.jpg", "images/bloggers_3.jpg"],
    "18+ Actress": [f"images/actress_{i}.jpg" for i in range(1, 8)],
}

MIN_PLAYERS: int = 1  # test uchun, keyinchalik 4 ga qaytaring
MAX_PLAYERS: int = 15
