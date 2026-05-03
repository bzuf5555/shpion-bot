import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))

# Ixtiyoriy: PostgreSQL ulash uchun (bo'lmasa SQLite ishlatiladi)
# Misol: postgresql://user:password@localhost:5432/shpion
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

REAL_CATEGORIES: list[str] = ["Cars", "Watches", "Jobs", "Bloggers", "18+ Actress", "Others"]
CATEGORIES: list[str] = REAL_CATEGORIES + ["🎲 Random"]

CATEGORY_IMAGES: dict[str, list[str]] = {
    "Cars":        [f"images/cars_{i}.jpg" for i in range(1, 11)],
    "Watches":     [f"images/watches_{i}.jpg" for i in range(1, 10)],
    "Jobs":        [f"images/jobs_{i}.jpg" for i in range(1, 10)],
    "Bloggers":    [f"images/bloggers_{i}.jpg" for i in range(1, 11)],
    "18+ Actress": [f"images/actress_{i}.jpg" for i in range(1, 8)],
    "Others":      [f"images/others_{i}.jpg"  for i in range(1, 29)],
}

MIN_PLAYERS: int = 1  # test uchun, keyinchalik 4 ga qaytaring
MAX_PLAYERS: int = 15
