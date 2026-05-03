import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Ixtiyoriy: PostgreSQL ulash uchun (bo'lmasa SQLite ishlatiladi)
# Misol: postgresql://user:password@localhost:5432/shpion
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

CATEGORIES: list[str] = ["Cars", "Watches", "Jobs", "Bloggers", "18+ Actress"]

CATEGORY_IMAGES: dict[str, str] = {
    "Cars":        "images/cars.jpg",
    "Watches":     "images/watches.jpg",
    "Jobs":        "images/jobs.jpg",
    "Bloggers":    "images/bloggers.jpg",
    "18+ Actress": "images/actress.jpg",
}

MIN_PLAYERS: int = 4
MAX_PLAYERS: int = 15
