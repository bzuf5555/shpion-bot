# Shpion Bot — Loyiha Hujjatlari

## Maqsad
Telegram guruh o'yini: bir yoki bir nechta ayg'oqchi yashiringan holda o'yinchilar guruhda rollarini aniqlaydi.

## Fayl tuzilmasi
```
shpion-bot/
  bot.py          — asosiy bot, barcha Telegram handlerlar
  game.py         — GameState sinfi, o'yin mantiq
  config.py       — BOT_TOKEN, kategoriyalar, limitlar
  images/         — kategoriya rasmlari (cars.jpg, watches.jpg, jobs.jpg, bloggers.jpg)
  requirements.txt
  .env            — maxfiy token (gitga yuklanmaydi)
  .env.example    — namuna
  task.md         — vazifalar ro'yxati
```

## Ishga tushirish
```bash
pip install -r requirements.txt
cp .env.example .env   # tokenni yozing
python bot.py
```

## O'yin oqimi
1. Guruhda `/start` → 4 kategoriya tanlanadi
2. Ayg'oqchi soni tanlanadi (1–9)
3. "Qo'shilish" tugmasi chiqadi, max 15 o'yinchi
4. 4+ o'yinchi bo'lganda "Boshlash" tugmasi paydo bo'ladi
5. Boshlanganda barcha o'yinchilar tugma sifatida ko'rsatiladi
6. Har bir o'yinchi o'z ismini bosadi → shaxsiy chatga rol keladi
   - Oddiy o'yinchi: kategoriya rasmi
   - Ayg'oqchi: "Sen ayg'oqchisan!" matni
7. "Tugatish" tugmasi → o'yin reset

## Qoidalar
- Har bir guruh uchun alohida GameState (chat_id kalit)
- Bot guruh chatida ishlaydi, rollar faqat DM orqali keladi
- O'yinchi avval botga `/start` yuborishi shart (DM ochiq bo'lishi uchun)
- `python-telegram-bot` v20+ (async)
- Holat xotirada saqlanadi (restart'da o'chadi)

## Muhit o'zgaruvchilari
| O'zgaruvchi | Ta'rif |
|-------------|--------|
| `BOT_TOKEN` | @BotFather dan olingan token |

## Rasmlar
`images/` papkasiga qo'yiladigan fayllar:
- `cars.jpg` — Cars kategoriyasi uchun
- `watches.jpg` — Watches uchun
- `jobs.jpg` — Jobs uchun
- `bloggers.jpg` — Bloggers uchun

Agar rasm topilmasa, bot matn xabari yuboradi.
