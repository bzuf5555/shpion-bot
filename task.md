# Shpion Bot — Vazifalar

## ✅ Bajarildi
- [x] Loyiha tuzilmasi va fayllar yaratildi
- [x] `config.py` — sozlamalar va konstantalar
- [x] `game.py` — o'yin holati va mantiq
- [x] `bot.py` — asosiy bot kodi (barcha handlerlar)
- [x] `requirements.txt` — kutubxonalar ro'yxati
- [x] `.env.example` — muhit o'zgaruvchilari namunasi
- [x] `CLAUDE.md` — loyiha hujjatlari
- [x] Kategoriya tanlash oqimi (Cars, Watches, Jobs, Bloggers, 18+ Actress)
- [x] Ayg'oqchi soni tanlash (1–9)
- [x] O'yinga qo'shilish tugmasi va 15 ta limit
- [x] 4+ o'yinchi bo'lganda "O'yinni boshlash" tugmasi
- [x] Tasodifiy ayg'oqchi tayinlash
- [x] Har bir o'yinchi o'z ismini bosib rolini ko'rishi
- [x] Ayg'oqchiga "Sen ayg'oqchisan!" xabari
- [x] Oddiy o'yinchilarga kategoriya tasviri (DM)
- [x] "O'yinni tugatish" tugmasi va reset
- [x] Rasm fayllarini generatsiya qilish (Pillow, barcha 5 kategoriya)
- [x] Admin buyruqlari — `/cancel` (admin), `/status` (holat ko'rish)
- [x] O'yin natijasini guruhga e'lon qilish (kim ayg'oqchi edi?)
- [x] JSON file persistence — `game_state.json` restart'dan keyin holat saqlanadi
- [x] Ko'p guruh uchun parallel o'yinlar (chat_id kalit orqali — ishlaydi)

## ⏳ Keyingi bosqich (ixtiyoriy)
- [x] DB persistence — SQLite (default) + PostgreSQL (DATABASE_URL berilsa) qo'llab-quvvatlash
- [ ] O'yin vaqt limiti — qo'shilish bosqichi uchun timeout
- [ ] O'yinchi chiqib ketish imkoniyati ("Chiqish" tugmasi qo'shilish bosqichida)
