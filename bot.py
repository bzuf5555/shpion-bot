import logging
import os
import random
from datetime import datetime

from telegram import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.constants import ChatType, ChatMemberStatus
from telegram.error import BadRequest, Forbidden
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, PreCheckoutQueryHandler, filters

from config import BOT_TOKEN, CATEGORIES, CATEGORY_IMAGES, MIN_PLAYERS, MAX_PLAYERS, OWNER_ID, REAL_CATEGORIES

JOIN_TIMEOUT = 180  # 3 daqiqa (soniyada)
_bot_username: str = ""

# Maxsus kategoriya qo'shish jarayonidagi adminlar
# user_id -> {"name": str, "file_ids": list}
_pending_cat: dict[int, dict] = {}
from game import GameState, get_game, save_state, load_state
from subscriptions import (
    PLANS, add_subscription, get_expiry, is_subscribed,
    create_promo, use_promo, get_expiring_soon,
    is_group_subscribed, add_group_subscription, get_group_expiry,
    track_game, get_user_stats, get_group_leaderboard,
    add_referral, get_referrer, claim_referral_bonus,
    record_payment, get_global_stats,
    get_lang, set_lang,
    save_custom_category, load_custom_categories, delete_custom_category,
)
from translations import t

# Har bir guruh uchun alohida minimum o'yinchi soni
_chat_min: dict[int, int] = {}

def get_min(chat_id: int) -> int:
    return _chat_min.get(chat_id, MIN_PLAYERS)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_ADMIN_STATUSES = {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}

STATE_LABELS = {
    "idle":     "O'yin yo'q",
    "category": "Kategoriya tanlanmoqda",
    "spies":    "Ayg'oqchi soni tanlanmoqda",
    "joining":  "O'yinchilar qo'shilmoqda",
    "roles":    "O'yin davom etmoqda",
    "voting":   "Ovoz berish davom etmoqda",
}


# ─── helpers ────────────────────────────────────────────────────────────────

def _display_name(user) -> str:
    name = f"@{user.username}" if user.username else user.full_name
    if _is_owner(user.id):
        return f"👑 {name}"
    if is_subscribed(user.id):
        return f"⭐ {name}"
    return name


def _join_keyboard(player_count: int, min_players: int) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton("🎮 O'yinga qo'shilish", callback_data="join")]]
    if player_count >= min_players:
        rows.append([InlineKeyboardButton("▶️ O'yinni boshlash", callback_data="start_game")])
    return InlineKeyboardMarkup(rows)


def _join_text(game: GameState) -> str:
    player_list = "\n".join(f"  • {game.player_names[uid]}" for uid in game.players)
    return (
        f"Kategoriya: {game.category}  |  Ayg'oqchilar: {game.spy_count}\n\n"
        f"O'yinga qo'shilganlar ({len(game.players)}/{MAX_PLAYERS}):\n"
        f"{player_list or '  —'}"
    )


def _role_keyboard(game: GameState) -> InlineKeyboardMarkup:
    chat_id = game.join_chat_id or 0
    rows = [
        [InlineKeyboardButton(
            game.player_names[uid],
            url=f"https://t.me/{_bot_username}?start=reveal_{chat_id}_{uid}"
        )]
        for uid in game.players
    ]
    rows.append([InlineKeyboardButton("🗳 Ovoz berish", callback_data="start_vote")])
    rows.append([InlineKeyboardButton("🏁 O'yinni tugatish", callback_data="end_game")])
    return InlineKeyboardMarkup(rows)


def _vote_keyboard(game: GameState, voter_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"{'✅ ' if game.votes.get(voter_id) == uid else ''}{game.player_names[uid]}",
            callback_data=f"vote_{uid}"
        )]
        for uid in game.players if uid != voter_id
    ]
    voted_count = len(game.votes)
    rows.append([InlineKeyboardButton(
        f"📊 Natija ({voted_count}/{len(game.players)} ovoz)",
        callback_data="vote_result"
    )])
    rows.append([InlineKeyboardButton("🏁 O'yinni tugatish", callback_data="end_game")])
    return InlineKeyboardMarkup(rows)


async def _is_admin(chat, user_id: int) -> bool:
    member = await chat.get_member(user_id)
    return member.status in _ADMIN_STATUSES

def _is_owner(user_id: int) -> bool:
    return OWNER_ID != 0 and user_id == OWNER_ID


# ─── commands ────────────────────────────────────────────────────────────────

async def _handle_reveal(update, user, arg: str) -> None:
    lang = get_lang(user.id)
    try:
        _, chat_id_str, uid_str = arg.split("_", 2)
        chat_id = int(chat_id_str)
        uid     = int(uid_str)
    except Exception:
        await update.message.reply_text("Noto'g'ri havola.")
        return

    if user.id != uid:
        await update.message.reply_text("Bu havola siz uchun emas!")
        return

    game = get_game(chat_id)
    if game.state not in ("roles", "voting"):
        await update.message.reply_text("O'yin tugagan yoki hali boshlanmagan.")
        return
    if user.id not in game.players:
        await update.message.reply_text("Siz bu o'yinda qatnashmaysiz.")
        return
    if user.id in game.roles_received:
        await update.message.reply_text(t("role_already", lang))
        return

    is_spy = user.id in game.spies
    if is_spy:
        spy_img = "images/spy.jpg"
        if os.path.isfile(spy_img):
            with open(spy_img, "rb") as f:
                await update.message.reply_photo(f, caption=t("spy_caption", lang))
        else:
            await update.message.reply_text(t("spy_caption", lang))
    else:
        image_path = game.selected_image or ""
        caption = t("civilian_caption", lang, cat=game.category)
        if image_path and os.path.isfile(image_path):
            with open(image_path, "rb") as img:
                await update.message.reply_photo(img, caption=caption)
        elif image_path:
            # Telegram file_id (maxsus kategoriya)
            await update.message.reply_photo(image_path, caption=caption)
        else:
            await update.message.reply_text(caption)

    game.roles_received.append(user.id)
    save_state()


async def _subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⭐ {p['stars']} Stars — {p['label']}", callback_data=f"buy_{k}")]
        for k, p in PLANS.items()
    ])
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t("sub_menu", lang), reply_markup=keyboard)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        if context.args:
            arg = context.args[0]
            if arg == "subscribe":
                await _subscribe_menu(update, context)
                return
            if arg.startswith("ref_"):
                try:
                    referrer_id = int(arg[4:])
                    if referrer_id != user.id:
                        add_referral(referrer_id, user.id)
                except ValueError:
                    pass
            if arg.startswith("reveal_"):
                await _handle_reveal(update, user, arg)
                return
        lang = get_lang(user.id)
        await update.message.reply_text(t("start_private", lang))
        return

    # Obuna tekshiruvi (owner uchun kerak emas)
    if not _is_owner(user.id) and not is_subscribed(user.id) and not is_group_subscribed(chat.id):
        lang = get_lang(user.id)
        bot_username = (await context.bot.get_me()).username
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t("sub_buy_btn", lang), url=f"https://t.me/{bot_username}?start=subscribe")
        ]])
        await update.message.reply_text(
            t("sub_required", lang, name=_display_name(user)),
            reply_markup=keyboard,
        )
        return

    game = get_game(chat.id)
    if game.state != "idle":
        await update.message.reply_text("O'yin allaqachon boshlangan! Avval tugating.")
        return

    game.state = "category"
    save_state()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in CATEGORIES]
    )
    await update.message.reply_text("Kategoriyani tanlang:", reply_markup=keyboard)


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
        await update.message.reply_text("Obuna olish uchun botga shaxsiy xabar yuboring.")
        return
    if _is_owner(update.effective_user.id):
        await update.message.reply_text("Siz bot egasisiz — obuna kerak emas.")
        return
    await _subscribe_menu(update, context)


async def cmd_mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_lang(user.id)
    if _is_owner(user.id):
        await update.message.reply_text(t("status_owner", lang))
        return
    expiry = get_expiry(user.id)
    if not expiry or expiry < datetime.utcnow():
        bot_username = (await context.bot.get_me()).username
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(t("sub_buy_btn", lang), url=f"https://t.me/{bot_username}?start=subscribe")
        ]])
        await update.message.reply_text(t("status_none", lang), reply_markup=keyboard)
    else:
        await update.message.reply_text(t("status_active", lang, date=expiry.strftime("%d.%m.%Y")))


async def cmd_addpromo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "Ishlatish: /addpromo KOD reja foydalanish_soni\n"
            "Misol: /addpromo PROMO10 month 10"
        )
        return
    code = context.args[0].upper()
    plan_key = context.args[1].lower()
    if plan_key not in PLANS:
        await update.message.reply_text("Noto'g'ri reja: week | month | half | year")
        return
    try:
        max_uses = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Foydalanish soni raqam bo'lishi kerak.")
        return
    create_promo(code, plan_key, max_uses)
    plan = PLANS[plan_key]
    await update.message.reply_text(
        f"✅ Promo kod yaratildi!\n"
        f"Kod: {code}\nReja: {plan['label']}\nLimit: {max_uses} marta"
    )


async def cmd_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Ishlatish: /promo KOD")
        return
    code = context.args[0]
    user_id = update.effective_user.id
    result = use_promo(code, user_id)

    if result == "not_found":
        await update.message.reply_text("❌ Bunday promo kod mavjud emas.")
    elif result == "already_used":
        await update.message.reply_text("❌ Bu promo kodni allaqachon ishlatgansiz.")
    elif result == "expired":
        await update.message.reply_text("❌ Bu promo kodning limiti tugagan.")
    else:
        plan = PLANS[result]
        expires = add_subscription(user_id, plan["days"])
        await update.message.reply_text(
            f"✅ Promo kod qabul qilindi!\n"
            f"Obuna: {plan['label']}\n"
            f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
        )


async def cmd_addcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /addcategory KATEGORIYA_NOMI")
        return
    name = " ".join(context.args)
    if name in CATEGORY_IMAGES:
        await update.message.reply_text(f"'{name}' kategoriyasi allaqachon mavjud.")
        return
    _pending_cat[update.effective_user.id] = {"name": name, "file_ids": []}
    await update.message.reply_text(
        f"'{name}' kategoriyasi uchun rasmlar yuboring.\n"
        f"Tugatgach /donecategory yozing.\nBekor qilish: /cancelcategory"
    )


async def cmd_donecategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid not in _pending_cat:
        await update.message.reply_text("Avval /addcategory buyrug'ini yuboring.")
        return
    pending = _pending_cat.pop(uid)
    if not pending["file_ids"]:
        await update.message.reply_text("Hech qanday rasm qo'shilmadi.")
        return
    name = pending["name"]
    fids = pending["file_ids"]
    save_custom_category(name, fids)
    REAL_CATEGORIES.append(name)
    CATEGORIES.insert(-1, name)
    CATEGORY_IMAGES[name] = fids
    await update.message.reply_text(
        f"✅ '{name}' kategoriyasi {len(fids)} ta rasm bilan qo'shildi!"
    )


async def cmd_cancelcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid in _pending_cat:
        name = _pending_cat.pop(uid)["name"]
        await update.message.reply_text(f"'{name}' kategoriyasi bekor qilindi.")
    else:
        await update.message.reply_text("Faol kategoriya yo'q.")


async def cmd_delcategory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /delcategory KATEGORIYA_NOMI")
        return
    name = " ".join(context.args)
    built_in = {"Cars", "Watches", "Jobs", "Bloggers", "18+ Actress", "Others"}
    if name in built_in:
        await update.message.reply_text("Standart kategoriyalarni o'chirib bo'lmaydi.")
        return
    if name not in CATEGORY_IMAGES:
        await update.message.reply_text(f"'{name}' kategoriyasi topilmadi.")
        return
    delete_custom_category(name)
    REAL_CATEGORIES.remove(name)
    CATEGORIES.remove(name)
    del CATEGORY_IMAGES[name]
    await update.message.reply_text(f"✅ '{name}' kategoriyasi o'chirildi.")


async def cmd_mycategories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    custom = load_custom_categories()
    if not custom:
        await update.message.reply_text("Maxsus kategoriyalar yo'q.")
        return
    lines = ["📋 Maxsus kategoriyalar:"]
    for name, imgs in custom:
        lines.append(f"• {name} — {len(imgs)} ta rasm")
    await update.message.reply_text("\n".join(lines))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid not in _pending_cat:
        return
    photo = update.message.photo[-1]
    _pending_cat[uid]["file_ids"].append(photo.file_id)
    count = len(_pending_cat[uid]["file_ids"])
    await update.message.reply_text(
        f"✅ Rasm qo'shildi ({count} ta). Yana yuboring yoki /donecategory"
    )


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ])
    await update.message.reply_text(t("choose_lang"), reply_markup=keyboard)


async def cmd_ref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = get_lang(user.id)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    await update.message.reply_text(t("ref_msg", lang, link=link))


async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    s = get_user_stats(user.id)
    expiry = get_expiry(user.id)

    lines = [f"📊 {user.first_name} statistikasi:"]
    lines.append(f"O'yinlar: {s['games']} ta")
    lines.append(f"Ayg'oqchi bo'lganlar: {s['as_spy']} ta")
    if expiry and expiry > datetime.utcnow():
        lines.append(f"Obuna: {expiry.strftime('%d.%m.%Y')} gacha")
    elif _is_owner(user.id):
        lines.append("Obuna: Cheksiz (owner)")
    else:
        lines.append("Obuna: Yo'q")
    await update.message.reply_text("\n".join(lines))


async def cmd_groupstats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        await update.message.reply_text("Bu buyruq faqat guruhda ishlaydi.")
        return
    rows = get_group_leaderboard(chat.id)
    if not rows:
        await update.message.reply_text("Hali bu guruhda o'yin o'ynalmagan.")
        return
    lines = ["🏆 Guruh reytingi (top 10):"]
    for i, (name, games, spy) in enumerate(rows, 1):
        lines.append(f"{i}. {name} — {games} o'yin, {spy} marta ayg'oqchi")
    grp_exp = get_group_expiry(chat.id)
    if grp_exp and grp_exp > datetime.utcnow():
        lines.append(f"\n🔑 Guruh obunasi: {grp_exp.strftime('%d.%m.%Y')} gacha")
    await update.message.reply_text("\n".join(lines))


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    s = get_global_stats()
    await update.message.reply_text(
        f"📈 Bot statistikasi:\n\n"
        f"👤 Foydalanuvchilar: {s['users']} ta\n"
        f"🎮 Jami o'yinlar: {s['total_games']} ta\n"
        f"👥 Jami o'yinchilar: {s['total_players']} ta\n\n"
        f"✅ Faol obunalar: {s['active_sub']} ta\n"
        f"🏘 Faol guruh obunalari: {s['active_grp']} ta\n\n"
        f"⭐ Jami daromad: {s['total_stars']} Stars"
    )


async def cmd_groupsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == ChatType.PRIVATE:
        await update.message.reply_text("Bu buyruq guruhda ishlaydi.")
        return
    grp_exp = get_group_expiry(chat.id)
    status = ""
    if grp_exp and grp_exp > datetime.utcnow():
        status = f"✅ Guruh obunasi: {grp_exp.strftime('%d.%m.%Y')} gacha\n\n"

    group_plans = {k: v for k, v in PLANS.items() if v["group"]}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⭐ {p['stars']} Stars — {p['label']}", callback_data=f"buy_{k}")]
        for k, p in group_plans.items()
    ])
    await update.message.reply_text(
        f"{status}Butun guruh uchun obuna — barcha a'zolar bepul o'ynaydi:\n\n"
        "⭐ 15 Stars — Guruh 1 Hafta\n"
        "⭐ 30 Stars — Guruh 1 Oy\n"
        "⭐ 100 Stars — Guruh 6 Oy\n"
        "⭐ 150 Stars — Guruh 1 Yil",
        reply_markup=keyboard,
    )


async def cmd_gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Ishlatish: /gift @username week | month | half | year"
        )
        return

    username = context.args[0].lstrip("@")
    plan_key = context.args[1].lower()
    plan = PLANS.get(plan_key)

    if not plan:
        await update.message.reply_text(
            "Noto'g'ri reja. Quyidagilardan birini tanlang:\n"
            "week | month | half | year"
        )
        return

    try:
        chat = await context.bot.get_chat(f"@{username}")
        user_id = chat.id
        name = f"@{username}"
    except Exception:
        await update.message.reply_text(
            f"@{username} topilmadi. Username to'g'riligini tekshiring."
        )
        return

    expires = add_subscription(user_id, plan["days"])

    await update.message.reply_text(
        f"🎁 @{username} ga {plan['label']} obuna sovg'a qilindi!\n"
        f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
    )

    try:
        await context.bot.send_message(
            user_id,
            f"🎁 Sizga {plan['label']} bepul obuna sovg'a qilindi!\n"
            f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
        )
    except (Forbidden, BadRequest):
        pass


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return

    user = update.effective_user
    game = get_game(chat.id)

    if game.state == "idle":
        await update.message.reply_text("Hozir hech qanday faol o'yin yo'q.")
        return

    if not _is_owner(user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return

    _cancel_join_job(context, chat.id)
    game.reset()
    save_state()
    await update.message.reply_text("O'yin bekor qilindi. Yangi o'yin uchun /start bosing.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return

    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return

    game = get_game(chat.id)
    label = STATE_LABELS.get(game.state, game.state)

    if game.state == "idle":
        await update.message.reply_text(f"Holat: {label}")
        return

    lines = [f"Holat: {label}"]
    if game.category:
        lines.append(f"Kategoriya: {game.category}")
    if game.spy_count:
        lines.append(f"Ayg'oqchilar soni: {game.spy_count}")
    if game.players:
        names = ", ".join(game.player_names[uid] for uid in game.players)
        lines.append(f"O'yinchilar ({len(game.players)}): {names}")

    await update.message.reply_text("\n".join(lines))


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Sizning Telegram ID ingiz: `{user.id}`", parse_mode="Markdown")



async def cmd_setmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Ishlatish: /setmin <son>  (masalan: /setmin 3)")
        return
    n = int(context.args[0])
    if not 1 <= n <= MAX_PLAYERS - 1:
        await update.message.reply_text(f"Son 1 dan {MAX_PLAYERS - 1} gacha bo'lishi kerak.")
        return
    _chat_min[chat.id] = n
    await update.message.reply_text(f"Minimum o'yinchi soni {n} ta qilib belgilandi.")


async def cmd_reveal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    game = get_game(chat.id)
    if game.state != "roles" or not game.spies:
        await update.message.reply_text("Hozir faol o'yin yo'q yoki rollar hali tayinlanmagan.")
        return
    spy_names = [game.player_names[uid] for uid in game.spies]
    await update.message.reply_text(
        f"🕵️ Ayg'oqchi(lar): {', '.join(spy_names)}"
    )


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat bot egasi uchun.")
        return
    game = get_game(chat.id)
    if game.state != "joining":
        await update.message.reply_text("O'yinchilarni faqat qo'shilish bosqichida chiqarish mumkin.")
        return
    if not context.args:
        await update.message.reply_text("Ishlatish: /kick @username")
        return

    target = context.args[0].lstrip("@").lower()
    found_uid = None
    for uid, name in game.player_names.items():
        if name.lstrip("@").lower() == target or name.lower() == target:
            found_uid = uid
            break

    if found_uid is None:
        await update.message.reply_text(f"@{target} o'yinchilar ro'yxatida topilmadi.")
        return

    kicked_name = game.player_names[found_uid]
    game.players.remove(found_uid)
    del game.player_names[found_uid]
    save_state()

    # Qo'shilish xabarini yangilash
    if game.join_message_id and game.join_chat_id:
        try:
            await context.bot.edit_message_text(
                chat_id=game.join_chat_id,
                message_id=game.join_message_id,
                text=_join_text(game),
                reply_markup=_join_keyboard(len(game.players), get_min(chat.id)),
            )
        except BadRequest:
            pass

    await update.message.reply_text(f"{kicked_name} o'yindan chiqarildi.")


# ─── callback router ─────────────────────────────────────────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat = query.message.chat
    user = query.from_user
    game = get_game(chat.id)
    data: str = query.data

    if data.startswith("lang_"):
        lang = data[5:]
        set_lang(user.id, lang)
        await query.answer(t("lang_set", lang), show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    if data.startswith("buy_"):
        await _on_buy(query, context, user, data[4:])
        return
    await query.answer()
    if data.startswith("cat_"):
        await _on_category(query, game, data[4:])
    if data.startswith("spy_"):
        await _on_spy_count(query, context, game, int(data[4:]))
    elif data == "join":
        await _on_join(query, game, user)
    elif data == "start_game":
        await _on_start_game(query, context, game)
    elif data == "start_vote":
        await _on_start_vote(query, game, user)
    elif data.startswith("vote_") and data != "vote_result":
        await _on_vote(query, game, user, int(data[5:]))
    elif data == "vote_result":
        await _on_vote_result(query, game)
    elif data == "end_game":
        await _on_end_game(query, context, game)


# ─── payment handlers ────────────────────────────────────────────────────────

async def _on_buy(query, context, user, data: str) -> None:
    # data = "plan_key" yoki "gplan_key_chatid" (guruh uchun)
    parts = data.split("_", 1)
    plan_key = parts[0]
    chat_id_override = int(parts[1]) if len(parts) > 1 else None

    plan = PLANS.get(plan_key)
    if not plan:
        await query.answer()
        return

    is_group_plan = plan.get("group", False)

    # Guruh obunasi — invoice guruhda ko'rsatiladi
    if is_group_plan:
        if query.message.chat.type == ChatType.PRIVATE:
            await query.answer("Guruh obunasi guruhda amalga oshiriladi!", show_alert=True)
            return
        await query.answer()
        invoice_chat = query.message.chat_id
        payload = f"grp_{invoice_chat}_{plan_key}"
    else:
        # Shaxsiy obuna — faqat private chatda
        if query.message.chat.type != ChatType.PRIVATE:
            await query.answer("Shaxsiy obuna faqat private chatda!", show_alert=True)
            return
        await query.answer()
        invoice_chat = user.id
        payload = f"sub_{plan_key}"

    try:
        await context.bot.send_invoice(
            chat_id=invoice_chat,
            title=f"Shpion Bot — {plan['label']}",
            description=f"{plan['desc']}\n\n⚠️ Stars yetarli bo'lmasa: Telegram → Settings → Stars",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(plan["label"], plan["stars"])],
        )
    except Exception as e:
        logger.error("send_invoice error: %s", e)
        await query.message.reply_text(f"Xatolik yuz berdi: {e}")


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payment = update.message.successful_payment
    payload  = payment.invoice_payload   # sub_week | sub_gmonth | grp_CHATID_gweek
    user_id  = update.effective_user.id

    # Guruh obunasi: payload = grp_CHATID_PLANKEY
    if payload.startswith("grp_"):
        parts = payload.split("_", 2)
        chat_id  = int(parts[1])
        plan_key = parts[2]
        plan = PLANS.get(plan_key)
        if not plan:
            return
        record_payment(user_id, plan_key, payment.total_amount)
        expires = add_group_subscription(chat_id, plan["days"])
        await update.message.reply_text(
            f"✅ Guruh obunasi faollashdi!\n"
            f"Reja: {plan['label']}\n"
            f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
        )
        try:
            await context.bot.send_message(
                chat_id,
                f"🎉 Guruh obunasi faollashdi! ({plan['label']})\n"
                f"Barcha a'zolar endi bepul o'ynay oladi.\n"
                f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
            )
        except Exception:
            pass
        return

    # Shaxsiy obuna
    plan_key = payload[4:]
    plan = PLANS.get(plan_key)
    if not plan:
        return
    lang = get_lang(user_id)
    record_payment(user_id, plan_key, payment.total_amount)
    expires = add_subscription(user_id, plan["days"])
    await update.message.reply_text(
        t("payment_ok", lang, label=plan["label"], date=expires.strftime("%d.%m.%Y"))
    )

    # Referral bonus
    referrer_id = claim_referral_bonus(user_id)
    if referrer_id:
        add_subscription(referrer_id, 3)
        try:
            rlang = get_lang(referrer_id)
            await context.bot.send_message(referrer_id, t("ref_bonus", rlang))
        except Exception:
            pass


# ─── step handlers ───────────────────────────────────────────────────────────

async def _on_category(query, game: GameState, category: str) -> None:
    if game.state != "category":
        return

    if category == "🎲 Random":
        chosen = random.choice(REAL_CATEGORIES)
        display = "🎲 Random"
    else:
        chosen = category
        display = category

    game.category = chosen
    game.state = "spies"
    save_state()

    rows = [
        [InlineKeyboardButton(str(i), callback_data=f"spy_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"spy_{i}") for i in range(6, 10)],
    ]
    await query.edit_message_text(
        f"Kategoriya: {display}\nAyg'oqchilar sonini tanlang (1–9):",
        reply_markup=InlineKeyboardMarkup(rows),
    )


def _cancel_join_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    for job in context.job_queue.get_jobs_by_name(f"join_{chat_id}"):
        job.schedule_removal()


async def _join_timeout_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    game = get_game(chat_id)
    if game.state != "joining":
        return

    min_p = get_min(chat_id)
    if len(game.players) < min_p:
        game.reset()
        save_state()
        await context.bot.send_message(
            chat_id, "⏰ Vaqt tugadi! Yetarli o'yinchi qo'shilmadi. /start bilan qayta boshlang."
        )
        return

    game.state = "roles"
    game.assign_spies()
    images = CATEGORY_IMAGES.get(game.category, [])
    game.selected_image = random.choice(images) if images else None
    save_state()

    keyboard = _role_keyboard(game)
    text = (
        f"⏰ Vaqt tugadi! O'yin avtomatik boshlandi.\nKategoriya: {game.category}\n\n"
        "O'z ismingizni toping va bosing — rolingizni shaxsiy chatda bilib oling:"
    )
    if game.join_message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=game.join_message_id,
                text=text, reply_markup=keyboard,
            )
            return
        except Exception:
            pass
    await context.bot.send_message(chat_id, text, reply_markup=keyboard)


async def _on_spy_count(query, context, game: GameState, count: int) -> None:
    if game.state != "spies":
        return
    game.spy_count = count
    game.state = "joining"
    game.join_chat_id = query.message.chat_id
    save_state()

    await query.edit_message_text(
        _join_text(game),
        reply_markup=_join_keyboard(0, get_min(query.message.chat_id)),
    )
    game.join_message_id = query.message.message_id
    save_state()

    context.job_queue.run_once(
        _join_timeout_job,
        JOIN_TIMEOUT,
        chat_id=query.message.chat_id,
        name=f"join_{query.message.chat_id}",
    )


async def _on_join(query, game: GameState, user) -> None:
    if game.state != "joining":
        return

    name = _display_name(user)
    added = game.add_player(user.id, name)
    if not added:
        already = user.id in game.players
        msg = "Allaqachon qo'shilgansiz!" if already else "Joy to'liq (15/15)!"
        await query.answer(msg, show_alert=True)
        return

    save_state()
    await query.edit_message_text(
        _join_text(game),
        reply_markup=_join_keyboard(len(game.players), get_min(query.message.chat_id)),
    )


async def _on_start_game(query, context, game: GameState) -> None:
    if game.state != "joining":
        return
    min_p = get_min(query.message.chat_id)
    if len(game.players) < min_p:
        await query.answer(f"Kamida {min_p} ta o'yinchi kerak!", show_alert=True)
        return

    _cancel_join_job(context, query.message.chat_id)
    game.state = "roles"
    game.assign_spies()
    images = CATEGORY_IMAGES.get(game.category, [])
    game.selected_image = random.choice(images) if images else None
    save_state()

    await query.edit_message_text(
        f"O'yin boshlandi!  Kategoriya: {game.category}\n\n"
        "O'z ismingizni toping va bosing — rolingizni shaxsiy chatda bilib oling:",
        reply_markup=_role_keyboard(game),
    )


async def _on_role_reveal(query, context, game: GameState, user, target_uid: int) -> None:
    if game.state != "roles":
        await query.answer("O'yin hali boshlanmagan.", show_alert=True)
        return
    lang = get_lang(user.id)
    if user.id != target_uid:
        await query.answer(t("not_your_btn", lang), show_alert=True)
        return
    if user.id in game.roles_received:
        await query.answer(t("role_already", lang), show_alert=True)
        return

    is_spy = user.id in game.spies
    try:
        if is_spy:
            spy_img = "images/spy.jpg"
            if os.path.isfile(spy_img):
                with open(spy_img, "rb") as f:
                    await context.bot.send_photo(user.id, f, caption=t("spy_caption", lang))
            else:
                await context.bot.send_message(user.id, t("spy_caption", lang))
        else:
            image_path = game.selected_image or ""
            if image_path and os.path.isfile(image_path):
                with open(image_path, "rb") as img:
                    await context.bot.send_photo(
                        user.id, img,
                        caption=t("civilian_caption", lang, cat=game.category)
                    )
            else:
                await context.bot.send_message(
                    user.id, t("civilian_caption", lang, cat=game.category)
                )
        game.roles_received.append(user.id)
        save_state()
        await query.answer(t("role_sent", lang), show_alert=True)
    except Forbidden:
        await query.answer(t("start_bot_first", lang), show_alert=True)
    except BadRequest as e:
        logger.error("send role error: %s", e)
        await query.answer("Xatolik yuz berdi, qayta urining.", show_alert=True)


async def _on_start_vote(query, game: GameState, user) -> None:
    if game.state != "roles":
        await query.answer("Ovoz berish faqat o'yin davomida!", show_alert=True)
        return
    if len(game.players) < 2:
        await query.answer("Ovoz berish uchun kamida 2 o'yinchi kerak!", show_alert=True)
        return
    game.votes = {}
    game.state = "voting"
    game.vote_message_id = query.message.message_id
    save_state()

    voted_count = len(game.votes)
    await query.edit_message_text(
        f"🗳 Ovoz berish boshlandi!\nKim ayg'oqchi deb o'ylaysiz?\n\n"
        f"Ovoz berganlar: {voted_count}/{len(game.players)}",
        reply_markup=_vote_keyboard(game, user.id),
    )


async def _on_vote(query, game: GameState, user, target_uid: int) -> None:
    if game.state != "voting":
        await query.answer("Hozir ovoz berish vaqti emas!", show_alert=True)
        return
    if user.id not in game.players:
        await query.answer("Siz bu o'yinda qatnashmaysiz!", show_alert=True)
        return

    game.votes[user.id] = target_uid
    save_state()

    voted_count = len(game.votes)
    target_name = game.player_names.get(target_uid, str(target_uid))
    await query.answer(f"Ovozingiz: {target_name}", show_alert=False)

    try:
        await query.edit_message_text(
            f"🗳 Ovoz berish davom etmoqda...\n\n"
            f"Ovoz berganlar: {voted_count}/{len(game.players)}",
            reply_markup=_vote_keyboard(game, user.id),
        )
    except Exception:
        pass


async def _on_vote_result(query, game: GameState) -> None:
    if game.state not in ("voting", "roles"):
        return

    if not game.votes:
        await query.answer("Hali hech kim ovoz bermagan!", show_alert=True)
        return

    # Ovozlarni hisoblash
    counts: dict[int, int] = {}
    for target in game.votes.values():
        counts[target] = counts.get(target, 0) + 1

    max_votes = max(counts.values())
    leaders = [uid for uid, c in counts.items() if c == max_votes]

    lines = ["📊 Ovoz natijalari:\n"]
    for uid in sorted(counts, key=lambda x: -counts[x]):
        name = game.player_names.get(uid, str(uid))
        bar = "🔴" * counts[uid] + "⚪" * (len(game.votes) - counts[uid])
        lines.append(f"{bar} {name} — {counts[uid]} ovoz")

    lines.append("")
    spy_names = [game.player_names.get(uid) for uid in game.spies]

    if len(leaders) == 1:
        chosen = game.player_names.get(leaders[0])
        is_caught = leaders[0] in game.spies
        if is_caught:
            lines.append(f"✅ {chosen} — ayg'oqchi topildi!")
        else:
            lines.append(f"❌ {chosen} — ayg'oqchi emas edi!")
        lines.append(f"Haqiqiy ayg'oqchi(lar): {', '.join(spy_names)}")
    else:
        chosen_names = [game.player_names.get(u) for u in leaders]
        lines.append(f"🤝 Durrang: {', '.join(chosen_names)}")
        lines.append(f"Haqiqiy ayg'oqchi(lar): {', '.join(spy_names)}")

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏁 O'yinni tugatish", callback_data="end_game")
        ]])
    )


async def _on_end_game(query, context, game: GameState) -> None:
    if game.state == "idle":
        return

    _cancel_join_job(context, query.message.chat_id)

    if game.state in ("roles", "voting") and game.spies:
        spy_names = [game.player_names[uid] for uid in game.spies]
        result = "Ayg'oqchi(lar): " + ", ".join(spy_names)
        track_game(query.message.chat_id, game.player_names, game.spies)
    else:
        result = None

    game.reset()
    save_state()

    text = "O'yin tugadi!\n\n"
    if result:
        text += f"*** {result} ***\n\n"
    text += "Yangi o'yin boshlash uchun /start bosing."

    await query.edit_message_text(text)


# ─── bot commands setup ──────────────────────────────────────────────────────

async def _expiry_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_username = (await context.bot.get_me()).username
    for user_id, expires in get_expiring_soon(hours=24):
        try:
            lang = get_lang(user_id)
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(t("extend_btn", lang), url=f"https://t.me/{bot_username}?start=subscribe")
            ]])
            await context.bot.send_message(
                user_id,
                t("sub_expiry_reminder", lang, date=expires.strftime("%d.%m.%Y %H:%M")),
                reply_markup=keyboard,
            )
        except Exception:
            pass


async def _set_commands(app: Application) -> None:
    global _bot_username
    _bot_username = (await app.bot.get_me()).username
    all_cmds = [
        BotCommand("start",     "O'yinni boshlash"),
        BotCommand("subscribe",   "Obuna olish (Stars bilan)"),
        BotCommand("groupsub",   "Guruh obunasi olish"),
        BotCommand("mystatus",   "Obuna holatini ko'rish"),
        BotCommand("mystats",    "O'yin statistikangiz"),
        BotCommand("groupstats", "Guruh reytingi"),
        BotCommand("promo",      "Promo kod ishlatish"),
        BotCommand("ref",        "Referral havola olish (+3 kun bonus)"),
        BotCommand("language",   "Tilni o'zgartirish / Change language"),
        BotCommand("myid",      "O'zingizning Telegram ID ni ko'rish"),
        BotCommand("gift",      "[Admin] Foydalanuvchiga obuna sovg'a qilish"),
        BotCommand("addpromo",      "[Admin] Promo kod yaratish"),
        BotCommand("stats",         "[Admin] Bot statistikasi"),
        BotCommand("addcategory",   "[Admin] Yangi kategoriya qo'shish"),
        BotCommand("donecategory",  "[Admin] Kategoriya rasmlarini saqlash"),
        BotCommand("delcategory",   "[Admin] Kategoriya o'chirish"),
        BotCommand("mycategories",  "[Admin] Maxsus kategoriyalar ro'yxati"),
        BotCommand("cancel",    "[Admin] O'yinni bekor qilish"),
        BotCommand("status",    "[Admin] O'yin holatini ko'rish"),
        BotCommand("setmin",    "[Admin] Minimum o'yinchi sonini belgilash"),
        BotCommand("reveal",    "[Admin] Ayg'oqchini oshkor qilish"),
        BotCommand("kick",      "[Admin] O'yinchini chiqarish"),
    ]
    await app.bot.set_my_commands(all_cmds, scope=BotCommandScopeAllGroupChats())

    if OWNER_ID:
        try:
            await app.bot.set_my_commands(
                all_cmds,
                scope=BotCommandScopeChat(chat_id=OWNER_ID),
            )
        except Exception as e:
            logger.warning("Owner commands set failed: %s", e)


# ─── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring.")

    load_state()

    # Maxsus kategoriyalarni yuklash
    for cat_name, file_ids in load_custom_categories():
        if cat_name not in CATEGORY_IMAGES:
            REAL_CATEGORIES.append(cat_name)
            CATEGORIES.insert(-1, cat_name)
            CATEGORY_IMAGES[cat_name] = file_ids

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_set_commands)
        .build()
    )
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("mystatus",  cmd_mystatus))
    app.add_handler(CommandHandler("promo",      cmd_promo))
    app.add_handler(CommandHandler("addpromo",   cmd_addpromo))
    app.add_handler(CommandHandler("gift",       cmd_gift))
    app.add_handler(CommandHandler("ref",      cmd_ref))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("mystats",    cmd_mystats))
    app.add_handler(CommandHandler("groupstats", cmd_groupstats))
    app.add_handler(CommandHandler("groupsub",   cmd_groupsub))
    app.add_handler(CommandHandler("stats",         cmd_stats))
    app.add_handler(CommandHandler("addcategory",   cmd_addcategory))
    app.add_handler(CommandHandler("donecategory",  cmd_donecategory))
    app.add_handler(CommandHandler("cancelcategory",cmd_cancelcategory))
    app.add_handler(CommandHandler("delcategory",   cmd_delcategory))
    app.add_handler(CommandHandler("mycategories",  cmd_mycategories))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("setmin",    cmd_setmin))
    app.add_handler(CommandHandler("reveal",    cmd_reveal))
    app.add_handler(CommandHandler("kick",      cmd_kick))
    app.add_handler(CommandHandler("myid",      cmd_myid))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(CallbackQueryHandler(on_callback))

    # Har 6 soatda obuna eslatmalarini tekshirish
    app.job_queue.run_repeating(_expiry_reminder_job, interval=21600, first=60)

    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
