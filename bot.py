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
from game import GameState, get_game, save_state, load_state
from subscriptions import PLANS, add_subscription, get_expiry, is_subscribed, create_promo, use_promo

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
}


# ─── helpers ────────────────────────────────────────────────────────────────

def _display_name(user) -> str:
    return f"@{user.username}" if user.username else user.full_name


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
    rows = [
        [InlineKeyboardButton(game.player_names[uid], callback_data=f"role_{uid}")]
        for uid in game.players
    ]
    rows.append([InlineKeyboardButton("🏁 O'yinni tugatish", callback_data="end_game")])
    return InlineKeyboardMarkup(rows)


async def _is_admin(chat, user_id: int) -> bool:
    member = await chat.get_member(user_id)
    return member.status in _ADMIN_STATUSES

def _is_owner(user_id: int) -> bool:
    return OWNER_ID != 0 and user_id == OWNER_ID


# ─── commands ────────────────────────────────────────────────────────────────

async def _subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⭐ {p['stars']} Stars — {p['label']}", callback_data=f"buy_{k}")]
        for k, p in PLANS.items()
    ])
    await update.message.reply_text(
        "Obuna rejasini tanlang:\n\n"
        "⭐ 5 Stars — 1 Hafta\n"
        "⭐ 15 Stars — 1 Oy\n"
        "⭐ 50 Stars — 6 Oy\n"
        "⭐ 100 Stars — 1 Yil\n\n"
        "💡 Stars yetarli bo'lmasa: Telegram → Settings → Stars",
        reply_markup=keyboard,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        if context.args and context.args[0] == "subscribe":
            await _subscribe_menu(update, context)
            return
        await update.message.reply_text(
            "Assalomu alaykum! Men guruh o'yini botiman.\n"
            "Guruhga qo'shib, /start buyrug'ini yuboring."
        )
        return

    # Obuna tekshiruvi (owner uchun kerak emas)
    if not _is_owner(user.id) and not is_subscribed(user.id):
        bot_username = (await context.bot.get_me()).username
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "⭐ Obuna olish",
                url=f"https://t.me/{bot_username}?start=subscribe"
            )
        ]])
        await update.message.reply_text(
            f"{_display_name(user)}, o'yin boshlash uchun obuna kerak!",
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
    if _is_owner(user.id):
        await update.message.reply_text("Siz bot egasisiz — cheksiz kirish.")
        return
    expiry = get_expiry(user.id)
    if not expiry or expiry < datetime.utcnow():
        bot_username = (await context.bot.get_me()).username
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⭐ Obuna olish", url=f"https://t.me/{bot_username}?start=subscribe")
        ]])
        await update.message.reply_text("Faol obunangiz yo'q.", reply_markup=keyboard)
    else:
        await update.message.reply_text(
            f"✅ Obuna faol\nTugash sanasi: {expiry.strftime('%d.%m.%Y')}"
        )


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
    elif data.startswith("role_"):
        await _on_role_reveal(query, context, game, user, int(data[5:]))
    elif data == "end_game":
        await _on_end_game(query, context, game)


# ─── payment handlers ────────────────────────────────────────────────────────

async def _on_buy(query, context, user, plan_key: str) -> None:
    plan = PLANS.get(plan_key)
    if not plan:
        await query.answer()
        return
    if query.message.chat.type != ChatType.PRIVATE:
        await query.answer("To'lov faqat shaxsiy chatda!", show_alert=True)
        return
    await query.answer()
    try:
        await context.bot.send_invoice(
            chat_id=user.id,
            title=f"Shpion Bot — {plan['label']}",
            description=(
                f"{plan['desc']}\n\n"
                f"⚠️ Stars yetarli bo'lmasa: Telegram → Settings → Stars"
            ),
            payload=f"sub_{plan_key}",
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
    payload = update.message.successful_payment.invoice_payload  # sub_week / sub_month ...
    plan_key = payload[4:]
    plan = PLANS.get(plan_key)
    if not plan:
        return
    user_id = update.effective_user.id
    expires = add_subscription(user_id, plan["days"])
    await update.message.reply_text(
        f"✅ To'lov qabul qilindi!\n"
        f"Obuna: {plan['label']}\n"
        f"Tugash sanasi: {expires.strftime('%d.%m.%Y')}"
    )


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
    if user.id != target_uid:
        await query.answer("Bu tugma siz uchun emas!", show_alert=True)
        return
    if user.id in game.roles_received:
        await query.answer("Rolingizni allaqachon ko'rdingiz!", show_alert=True)
        return

    is_spy = user.id in game.spies
    try:
        if is_spy:
            spy_img = "images/spy.jpg"
            if os.path.isfile(spy_img):
                with open(spy_img, "rb") as f:
                    await context.bot.send_photo(user.id, f, caption="🕵️ Sen ayg'oqchisan!")
            else:
                await context.bot.send_message(user.id, "🕵️ Sen ayg'oqchisan!")
        else:
            image_path = game.selected_image or ""
            if image_path and os.path.isfile(image_path):
                with open(image_path, "rb") as img:
                    await context.bot.send_photo(
                        user.id, img,
                        caption=f"Sizning rolingiz: {game.category} o'yinchisi 🎭"
                    )
            else:
                await context.bot.send_message(
                    user.id,
                    f"Sizning rolingiz: {game.category} o'yinchisi 🎭"
                )
        game.roles_received.append(user.id)
        save_state()
        await query.answer("Rolingiz shaxsiy chatga yuborildi!", show_alert=True)
    except Forbidden:
        await query.answer(
            "Bot sizga xabar yubora olmadi!\nAvval botga shaxsiy /start yuboring.",
            show_alert=True,
        )
    except BadRequest as e:
        logger.error("send role error: %s", e)
        await query.answer("Xatolik yuz berdi, qayta urining.", show_alert=True)


async def _on_end_game(query, context, game: GameState) -> None:
    if game.state == "idle":
        return

    _cancel_join_job(context, query.message.chat_id)

    if game.state == "roles" and game.spies:
        spy_names = [game.player_names[uid] for uid in game.spies]
        result = "Ayg'oqchi(lar): " + ", ".join(spy_names)
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

async def _set_commands(app: Application) -> None:
    all_cmds = [
        BotCommand("start",     "O'yinni boshlash"),
        BotCommand("subscribe", "Obuna olish (Stars bilan)"),
        BotCommand("mystatus",  "Obuna holatini ko'rish"),
        BotCommand("promo",     "Promo kod ishlatish"),
        BotCommand("myid",      "O'zingizning Telegram ID ni ko'rish"),
        BotCommand("gift",      "[Admin] Foydalanuvchiga obuna sovg'a qilish"),
        BotCommand("addpromo",  "[Admin] Promo kod yaratish"),
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

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(_set_commands)
        .build()
    )
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("mystatus",  cmd_mystatus))
    app.add_handler(CommandHandler("promo",    cmd_promo))
    app.add_handler(CommandHandler("addpromo", cmd_addpromo))
    app.add_handler(CommandHandler("gift",     cmd_gift))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("setmin",    cmd_setmin))
    app.add_handler(CommandHandler("reveal",    cmd_reveal))
    app.add_handler(CommandHandler("kick",      cmd_kick))
    app.add_handler(CommandHandler("myid",      cmd_myid))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(CallbackQueryHandler(on_callback))

    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
