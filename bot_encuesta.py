import asyncio
import csv
import hashlib
import hmac
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from cuestionario import (
    ACCEPT_LABEL,
    CANCELLED_TEXT,
    CONSENT_TEXT,
    EXPIRED_SURVEY_TEXT,
    MISSING_SETTINGS_TEXT,
    NO_ACTIVE_SURVEY_TEXT,
    QUESTIONS,
    REJECT_LABEL,
    REJECTED_TEXT,
    SKIP_LABEL,
    SUS_COLUMNS,
    TEXT_QUESTION_TYPE,
    THANKS_TEXT,
    TIMEOUT_TEXT,
    USE_BUTTONS_TEXT,
)
from exportador_excel import generar_excel_desde_csv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HASH_SECRET = os.getenv("HASH_SECRET")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

DATA_DIR = Path(os.getenv("DATA_DIR", "."))
CSV_PATH = DATA_DIR / "resultados_telegram.csv"
CSV_ENCODING = "utf-8-sig"
CONVERSATION_TIMEOUT_SECONDS = 900
MAX_TEXT_LENGTH = 10000
DURATION_DECIMALS = 2
ATTEMPT_ID_BYTES = 8
SUS_SCORE_MULTIPLIER = 2.5
SCALE_MINIMUM = 1
SCALE_MAXIMUM = 5
ITEMS_PER_CYCLE = 2
FORMULA_PREFIXES = "=+-@"
FORMULA_ESCAPE = "'"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

CONSENT_YES = "consent:yes"
CONSENT_NO = "consent:no"
CONSENT_PATTERN = r"^consent:(yes|no)$"
ANSWER_PREFIX = "ans"
SKIP_PREFIX = "skip"
BACK_PREFIX = "back"
NEXT_PREFIX = "next"
SEPARATOR = ":"
ANSWER_PATTERN = r"^(ans:\d+:\d+|skip:\d+|back:\d+|next:\d+)$"
ABANDON_PREFIX = "P"
BACK_LABEL = "⬅️ Anterior"
NEXT_LABEL = "Siguiente ➡️"
SELECTED_PREFIX = "✓ "

END_COMPLETED = "completado"
END_CANCEL = "cancel"
END_TIMEOUT = "timeout"
END_RESTART = "reinicio"

NO_DATA_TEXT = "Aún no hay respuestas registradas."
UNAUTHORIZED_TEXT = "No tienes permiso para usar este comando."

CSV_FIELDS = (
    [
        "intento_id",
        "id_participante_hash",
        "fecha_inicio",
        "fecha_fin",
        "completado",
        "duracion_segundos",
        "pregunta_abandono",
        "motivo_fin",
    ]
    + [question["column"] for question in QUESTIONS]
    + ["sus_puntaje"]
)

CONSENT, SURVEY = range(2)

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

csv_lock = asyncio.Lock()


def anonymize_user_id(user_id):
    return hmac.new(
        HASH_SECRET.encode("utf-8"), str(user_id).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def calculate_sus_score(answers):
    total = 0
    for position, column in enumerate(SUS_COLUMNS):
        if column not in answers:
            return ""
        value = int(answers[column])
        if position % ITEMS_PER_CYCLE == 0:
            total += value - SCALE_MINIMUM
        else:
            total += SCALE_MAXIMUM - value
    return round(total * SUS_SCORE_MULTIPLIER, DURATION_DECIMALS)


def sanitize_text(text):
    cleaned = text.strip()[:MAX_TEXT_LENGTH]
    if cleaned and cleaned[0] in FORMULA_PREFIXES:
        return FORMULA_ESCAPE + cleaned
    return cleaned


def read_rows():
    rows = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, newline="", encoding=CSV_ENCODING) as file:
            for row in csv.DictReader(file):
                rows[row["intento_id"]] = row
    return rows


def write_rows(rows):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_path = tempfile.mkstemp(
        dir=CSV_PATH.parent, suffix=".tmp", text=True
    )
    try:
        with os.fdopen(file_descriptor, "w", newline="", encoding=CSV_ENCODING) as file:
            writer = csv.DictWriter(
                file, fieldnames=CSV_FIELDS, extrasaction="ignore", restval=""
            )
            writer.writeheader()
            writer.writerows(rows.values())
        os.replace(temp_path, CSV_PATH)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def upsert_row(row):
    rows = read_rows()
    rows[row["intento_id"]] = row
    write_rows(rows)


async def save_row(row):
    async with csv_lock:
        try:
            await asyncio.to_thread(upsert_row, row)
        except Exception:
            logger.exception("No se pudo escribir el CSV")


def build_row(user_data, completed, end_reason):
    end_time = datetime.now()
    start_time = user_data["start_time"]
    row = {
        "intento_id": user_data["attempt_id"],
        "id_participante_hash": user_data["user_hash"],
        "fecha_inicio": start_time.isoformat(timespec="seconds"),
        "fecha_fin": end_time.isoformat(timespec="seconds"),
        "completado": completed,
        "duracion_segundos": round(
            (end_time - start_time).total_seconds(), DURATION_DECIMALS
        ),
        "pregunta_abandono": "" if completed else f"{ABANDON_PREFIX}{user_data['q_index'] + 1}",
        "motivo_fin": end_reason,
        "sus_puntaje": calculate_sus_score(user_data["answers"]),
    }
    row.update(user_data["answers"])
    return row


def create_session(update):
    return {
        "start_time": datetime.now(),
        "attempt_id": os.urandom(ATTEMPT_ID_BYTES).hex(),
        "user_hash": anonymize_user_id(update.effective_user.id),
        "chat_id": update.effective_chat.id,
        "consent": False,
        "q_index": 0,
        "answers": {},
    }


def is_in_progress(user_data):
    return bool(user_data.get("consent")) and "start_time" in user_data


def is_text_question(question):
    return question.get("type") == TEXT_QUESTION_TYPE


def build_question_text(q_index, answers=None):
    question = QUESTIONS[q_index]
    text = f"Pregunta {q_index + 1} de {len(QUESTIONS)}\n{question['text']}"
    if answers and is_text_question(question) and question["column"] in answers:
        saved = answers[question["column"]]
        current = saved if saved else "(Omitida)"
        text += f"\n\nRespuesta actual: {current}"
    return text


def build_consent_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(ACCEPT_LABEL, callback_data=CONSENT_YES),
                InlineKeyboardButton(REJECT_LABEL, callback_data=CONSENT_NO),
            ]
        ]
    )


def build_navigation_row(q_index, answers):
    question = QUESTIONS[q_index]
    nav_buttons = []
    if q_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                BACK_LABEL, callback_data=f"{BACK_PREFIX}{SEPARATOR}{q_index}"
            )
        )
    if answers and question["column"] in answers:
        nav_buttons.append(
            InlineKeyboardButton(
                NEXT_LABEL, callback_data=f"{NEXT_PREFIX}{SEPARATOR}{q_index}"
            )
        )
    return nav_buttons


def build_text_keyboard(q_index, answers):
    rows = [
        [
            InlineKeyboardButton(
                SKIP_LABEL, callback_data=f"{SKIP_PREFIX}{SEPARATOR}{q_index}"
            )
        ]
    ]
    nav_row = build_navigation_row(q_index, answers)
    if nav_row:
        rows.append(nav_row)
    return InlineKeyboardMarkup(rows)


def build_options_keyboard(q_index, answers):
    question = QUESTIONS[q_index]
    saved_value = answers.get(question["column"]) if answers else None
    buttons = []
    for option_index, label in enumerate(question["options"]):
        display_label = f"{SELECTED_PREFIX}{label}" if saved_value == label else label
        data = f"{ANSWER_PREFIX}{SEPARATOR}{q_index}{SEPARATOR}{option_index}"
        buttons.append(InlineKeyboardButton(display_label, callback_data=data))
    size = question["columns"]
    rows = [buttons[start : start + size] for start in range(0, len(buttons), size)]
    nav_row = build_navigation_row(q_index, answers)
    if nav_row:
        rows.append(nav_row)
    return InlineKeyboardMarkup(rows)


def build_keyboard(q_index, answers=None):
    if is_text_question(QUESTIONS[q_index]):
        return build_text_keyboard(q_index, answers)
    return build_options_keyboard(q_index, answers)


def store_choice(user_data, parts):
    question = QUESTIONS[user_data["q_index"]]
    if parts[0] == SKIP_PREFIX:
        if not is_text_question(question):
            return False
        user_data["answers"][question["column"]] = ""
        return True
    option_index = int(parts[2])
    if is_text_question(question) or option_index >= len(question["options"]):
        return False
    user_data["answers"][question["column"]] = question["options"][option_index]
    return True


async def advance(context, send):
    user_data = context.user_data
    user_data["q_index"] += 1
    if user_data["q_index"] < len(QUESTIONS):
        next_index = user_data["q_index"]
        await send(
            build_question_text(next_index, user_data["answers"]),
            build_keyboard(next_index, user_data["answers"]),
        )
        return SURVEY
    await save_row(build_row(user_data, True, END_COMPLETED))
    await send(THANKS_TEXT, None)
    user_data.clear()
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_in_progress(context.user_data):
        await save_row(build_row(context.user_data, False, END_RESTART))
    context.user_data.clear()
    context.user_data.update(create_session(update))
    await update.message.reply_text(CONSENT_TEXT, reply_markup=build_consent_keyboard())
    return CONSENT


async def handle_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == CONSENT_NO:
        context.user_data.clear()
        await query.edit_message_text(REJECTED_TEXT)
        return ConversationHandler.END
    context.user_data["consent"] = True
    context.user_data["q_index"] = 0
    await query.edit_message_text(
        build_question_text(0, context.user_data["answers"]),
        reply_markup=build_keyboard(0, context.user_data["answers"]),
    )
    return SURVEY


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(SEPARATOR)
    user_data = context.user_data
    if int(parts[1]) != user_data["q_index"]:
        return SURVEY

    if parts[0] == BACK_PREFIX:
        if user_data["q_index"] > 0:
            user_data["q_index"] -= 1
            prev_index = user_data["q_index"]
            await query.edit_message_text(
                build_question_text(prev_index, user_data["answers"]),
                reply_markup=build_keyboard(prev_index, user_data["answers"]),
            )
        return SURVEY

    async def send(text, markup):
        await query.edit_message_text(text, reply_markup=markup)

    if parts[0] == NEXT_PREFIX:
        question = QUESTIONS[user_data["q_index"]]
        if question["column"] not in user_data["answers"]:
            return SURVEY
        return await advance(context, send)

    if not store_choice(user_data, parts):
        return SURVEY

    return await advance(context, send)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    question = QUESTIONS[user_data["q_index"]]
    if not is_text_question(question):
        await update.message.reply_text(USE_BUTTONS_TEXT)
        return SURVEY
    user_data["answers"][question["column"]] = sanitize_text(update.message.text)

    async def send(text, markup):
        await update.message.reply_text(text, reply_markup=markup)

    return await advance(context, send)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_in_progress(context.user_data):
        await save_row(build_row(context.user_data, False, END_CANCEL))
    context.user_data.clear()
    await update.message.reply_text(CANCELLED_TEXT)
    return ConversationHandler.END


async def handle_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get("chat_id")
    if is_in_progress(context.user_data):
        await save_row(build_row(context.user_data, False, END_TIMEOUT))
    context.user_data.clear()
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=TIMEOUT_TEXT)
    return ConversationHandler.END


async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_USER_ID or str(update.effective_user.id) != ADMIN_USER_ID:
        await update.message.reply_text(UNAUTHORIZED_TEXT)
        return
    async with csv_lock:
        if not CSV_PATH.exists():
            await update.message.reply_text(NO_DATA_TEXT)
            return
        xlsx_path = await asyncio.to_thread(generar_excel_desde_csv, CSV_PATH)
        with open(xlsx_path, "rb") as file:
            await update.message.reply_document(
                document=file,
                filename="resultados_encuesta_uptc.xlsx",
                caption="Aquí tienes los resultados formateados en Excel.",
            )


async def show_buttons_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(USE_BUTTONS_TEXT)


async def show_no_active_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(NO_ACTIVE_SURVEY_TEXT)


async def show_expired_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer(EXPIRED_SURVEY_TEXT, show_alert=True)


def create_conversation():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CONSENT: [CallbackQueryHandler(handle_consent, pattern=CONSENT_PATTERN)],
            SURVEY: [
                CallbackQueryHandler(handle_answer, pattern=ANSWER_PATTERN),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
            ],
            ConversationHandler.TIMEOUT: [TypeHandler(Update, handle_timeout)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.ALL & ~filters.COMMAND, show_buttons_hint),
        ],
        allow_reentry=True,
        conversation_timeout=CONVERSATION_TIMEOUT_SECONDS,
    )

def main():
    if not TELEGRAM_BOT_TOKEN or not HASH_SECRET:
        raise SystemExit(MISSING_SETTINGS_TEXT)
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(create_conversation())
    application.add_handler(CommandHandler("exportar", export_csv))
    application.add_handler(CommandHandler("cancel", show_no_active_survey))
    application.add_handler(CallbackQueryHandler(show_expired_survey))
    logger.info("Bot en ejecución...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()