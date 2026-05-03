STRINGS: dict[str, dict[str, str]] = {
    # ── /start private ──────────────────────────────────────────────────────
    "start_private": {
        "uz": "Assalomu alaykum! Men guruh o'yini botiman.\nGuruhga qo'shib, /start buyrug'ini yuboring.",
        "ru": "Привет! Я бот для групповой игры.\nДобавьте меня в группу и отправьте /start.",
        "en": "Hello! I'm a group game bot.\nAdd me to a group and send /start.",
    },
    # ── game already running ─────────────────────────────────────────────────
    "game_running": {
        "uz": "O'yin allaqachon boshlangan! Avval tugating.",
        "ru": "Игра уже идёт! Сначала завершите её.",
        "en": "Game already in progress! End it first.",
    },
    # ── subscription required ────────────────────────────────────────────────
    "sub_required": {
        "uz": "{name}, o'yin boshlash uchun obuna kerak!",
        "ru": "{name}, для начала игры нужна подписка!",
        "en": "{name}, a subscription is required to start the game!",
    },
    "sub_buy_btn": {
        "uz": "⭐ Obuna olish",
        "ru": "⭐ Купить подписку",
        "en": "⭐ Subscribe",
    },
    # ── category selection ───────────────────────────────────────────────────
    "choose_category": {
        "uz": "Kategoriyani tanlang:",
        "ru": "Выберите категорию:",
        "en": "Choose a category:",
    },
    # ── spy count ────────────────────────────────────────────────────────────
    "choose_spies": {
        "uz": "Kategoriya: {cat}\nAyg'oqchilar sonini tanlang (1–9):",
        "ru": "Категория: {cat}\nВыберите количество шпионов (1–9):",
        "en": "Category: {cat}\nChoose the number of spies (1–9):",
    },
    # ── join phase ───────────────────────────────────────────────────────────
    "join_header": {
        "uz": "Kategoriya: {cat}  |  Ayg'oqchilar: {spies}\n\nO'yinga qo'shilganlar ({count}/{max}):\n{players}",
        "ru": "Категория: {cat}  |  Шпионов: {spies}\n\nУчастники ({count}/{max}):\n{players}",
        "en": "Category: {cat}  |  Spies: {spies}\n\nPlayers ({count}/{max}):\n{players}",
    },
    "join_btn": {
        "uz": "🎮 O'yinga qo'shilish",
        "ru": "🎮 Присоединиться",
        "en": "🎮 Join Game",
    },
    "start_btn": {
        "uz": "▶️ O'yinni boshlash",
        "ru": "▶️ Начать игру",
        "en": "▶️ Start Game",
    },
    "already_joined": {
        "uz": "Allaqachon qo'shilgansiz!",
        "ru": "Вы уже в игре!",
        "en": "You already joined!",
    },
    "game_full": {
        "uz": "Joy to'liq (15/15)!",
        "ru": "Мест нет (15/15)!",
        "en": "Game is full (15/15)!",
    },
    # ── game start ───────────────────────────────────────────────────────────
    "game_started": {
        "uz": "O'yin boshlandi!  Kategoriya: {cat}\n\nO'z ismingizni toping va bosing — rolingizni shaxsiy chatda bilib oling:",
        "ru": "Игра началась!  Категория: {cat}\n\nНайдите своё имя и нажмите — роль придёт в личку:",
        "en": "Game started!  Category: {cat}\n\nFind your name and tap it — your role will be sent privately:",
    },
    "vote_btn": {
        "uz": "🗳 Ovoz berish",
        "ru": "🗳 Голосовать",
        "en": "🗳 Vote",
    },
    "end_btn": {
        "uz": "🏁 O'yinni tugatish",
        "ru": "🏁 Завершить игру",
        "en": "🏁 End Game",
    },
    # ── role reveal DM ───────────────────────────────────────────────────────
    "role_sent": {
        "uz": "Rolingiz shaxsiy chatga yuborildi!",
        "ru": "Роль отправлена в личку!",
        "en": "Your role was sent privately!",
    },
    "role_already": {
        "uz": "Rolingizni allaqachon ko'rdingiz!",
        "ru": "Вы уже видели свою роль!",
        "en": "You already revealed your role!",
    },
    "not_your_btn": {
        "uz": "Bu tugma siz uchun emas!",
        "ru": "Эта кнопка не для вас!",
        "en": "This button is not for you!",
    },
    "start_bot_first": {
        "uz": "Bot sizga xabar yubora olmadi!\nAvval botga shaxsiy /start yuboring.",
        "ru": "Бот не может написать вам!\nСначала напишите боту /start в личку.",
        "en": "Bot couldn't message you!\nFirst send /start to the bot privately.",
    },
    "spy_caption": {
        "uz": "🕵️ Sen ayg'oqchisan!",
        "ru": "🕵️ Ты шпион!",
        "en": "🕵️ You are the spy!",
    },
    "civilian_caption": {
        "uz": "Sizning rolingiz: {cat} o'yinchisi 🎭",
        "ru": "Ваша роль: игрок категории {cat} 🎭",
        "en": "Your role: {cat} player 🎭",
    },
    # ── end game ─────────────────────────────────────────────────────────────
    "game_over": {
        "uz": "O'yin tugadi!\n\n*** {spies} ***\n\nYangi o'yin boshlash uchun /start bosing.",
        "ru": "Игра завершена!\n\n*** {spies} ***\n\nДля новой игры нажмите /start.",
        "en": "Game over!\n\n*** {spies} ***\n\nPress /start for a new game.",
    },
    "game_over_no_result": {
        "uz": "O'yin tugadi!\nYangi o'yin boshlash uchun /start bosing.",
        "ru": "Игра завершена!\nДля новой игры нажмите /start.",
        "en": "Game over!\nPress /start for a new game.",
    },
    "spy_label": {
        "uz": "Ayg'oqchi(lar): {names}",
        "ru": "Шпион(ы): {names}",
        "en": "Spy(-ies): {names}",
    },
    # ── timeout ──────────────────────────────────────────────────────────────
    "timeout_no_players": {
        "uz": "⏰ Vaqt tugadi! Yetarli o'yinchi qo'shilmadi. /start bilan qayta boshlang.",
        "ru": "⏰ Время вышло! Недостаточно игроков. Начните заново с /start.",
        "en": "⏰ Time's up! Not enough players joined. Start again with /start.",
    },
    "timeout_autostart": {
        "uz": "⏰ Vaqt tugadi! O'yin avtomatik boshlandi.\nKategoriya: {cat}\n\nO'z ismingizni toping va bosing:",
        "ru": "⏰ Время вышло! Игра запущена автоматически.\nКатегория: {cat}\n\nНайдите своё имя и нажмите:",
        "en": "⏰ Time's up! Game started automatically.\nCategory: {cat}\n\nFind your name and tap it:",
    },
    # ── subscribe menu ───────────────────────────────────────────────────────
    "sub_menu": {
        "uz": "Obuna rejasini tanlang:\n\n⭐ 5 Stars — 1 Hafta\n⭐ 15 Stars — 1 Oy\n⭐ 50 Stars — 6 Oy\n⭐ 100 Stars — 1 Yil\n\n💡 Stars yetarli bo'lmasa: Telegram → Settings → Stars",
        "ru": "Выберите план подписки:\n\n⭐ 5 Stars — 1 Неделя\n⭐ 15 Stars — 1 Месяц\n⭐ 50 Stars — 6 Месяцев\n⭐ 100 Stars — 1 Год\n\n💡 Если Stars не хватает: Telegram → Settings → Stars",
        "en": "Choose a subscription plan:\n\n⭐ 5 Stars — 1 Week\n⭐ 15 Stars — 1 Month\n⭐ 50 Stars — 6 Months\n⭐ 100 Stars — 1 Year\n\n💡 Not enough Stars? Go to Telegram → Settings → Stars",
    },
    # ── payment success ──────────────────────────────────────────────────────
    "payment_ok": {
        "uz": "✅ To'lov qabul qilindi!\nObuna: {label}\nTugash sanasi: {date}",
        "ru": "✅ Оплата принята!\nПодписка: {label}\nДействует до: {date}",
        "en": "✅ Payment accepted!\nSubscription: {label}\nExpires: {date}",
    },
    # ── subscription expiry reminder ─────────────────────────────────────────
    "sub_expiry_reminder": {
        "uz": "⚠️ Obunangiz ertaga {date} da tugaydi!\nUzaytirish uchun quyidagi tugmani bosing.",
        "ru": "⚠️ Ваша подписка заканчивается завтра {date}!\nНажмите кнопку ниже для продления.",
        "en": "⚠️ Your subscription expires tomorrow {date}!\nTap the button below to renew.",
    },
    "extend_btn": {
        "uz": "⭐ Uzaytirish",
        "ru": "⭐ Продлить",
        "en": "⭐ Renew",
    },
    # ── mystatus ─────────────────────────────────────────────────────────────
    "status_active": {
        "uz": "✅ Obuna faol\nTugash sanasi: {date}",
        "ru": "✅ Подписка активна\nДействует до: {date}",
        "en": "✅ Subscription active\nExpires: {date}",
    },
    "status_none": {
        "uz": "Faol obunangiz yo'q.",
        "ru": "У вас нет активной подписки.",
        "en": "You have no active subscription.",
    },
    "status_owner": {
        "uz": "Siz bot egasisiz — cheksiz kirish.",
        "ru": "Вы владелец бота — безлимитный доступ.",
        "en": "You are the bot owner — unlimited access.",
    },
    # ── language command ─────────────────────────────────────────────────────
    "choose_lang": {
        "uz": "Tilni tanlang / Выберите язык / Choose language:",
        "ru": "Tilni tanlang / Выберите язык / Choose language:",
        "en": "Tilni tanlang / Выберите язык / Choose language:",
    },
    "lang_set": {
        "uz": "✅ Til o'rnatildi: O'zbek",
        "ru": "✅ Язык установлен: Русский",
        "en": "✅ Language set: English",
    },
    # ── referral ─────────────────────────────────────────────────────────────
    "ref_msg": {
        "uz": "🔗 Sizning referral havolangiz:\n{link}\n\nDo'stingiz bu havola orqali botga kirib, obuna olsa — sizga 3 kunlik BEPUL obuna qo'shiladi!",
        "ru": "🔗 Ваша реферальная ссылка:\n{link}\n\nКогда друг перейдёт по ссылке и оформит подписку — вы получите 3 дня БЕСПЛАТНО!",
        "en": "🔗 Your referral link:\n{link}\n\nWhen a friend signs up and subscribes via your link — you get 3 FREE days!",
    },
    "ref_bonus": {
        "uz": "🎁 Do'stingiz obuna oldi! Sizga 3 kunlik bonus obuna qo'shildi!",
        "ru": "🎁 Ваш друг оформил подписку! Вам начислено 3 бонусных дня!",
        "en": "🎁 Your friend subscribed! You've received 3 bonus days!",
    },
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    text = STRINGS.get(key, {}).get(lang) or STRINGS.get(key, {}).get("uz", key)
    return text.format(**kwargs) if kwargs else text
