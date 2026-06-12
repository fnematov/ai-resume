"""Localized Telegram bot system messages (uz / ru / en).

Only the bot's own messages are translated. Org-authored content — vacancy titles,
message templates, privacy notice — is sent as written.
"""

DEFAULT_LANG = "uz"
SUPPORTED_LANGS = ("uz", "ru")

# Shown before a language is chosen (bilingual).
CHOOSE_LANGUAGE = "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык:"

LANG_NAMES = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "welcome": "Send your resume here (PDF, image, or Word document) and we'll match it against the role.",
        "applying_for": "You're applying for <b>{title}</b>.",
        "position_closed": "That position is no longer open.",
        "no_open_positions": "There are no open positions right now.",
        "choose_position": "Please choose the position you're applying for:",
        "choose_position_first": "Please choose a position first:",
        "forget_done": "🗑 All your data has been permanently deleted. Take care!",
        "forget_none": "We have no data stored for you.",
        "resume_received": "✅ Resume received!",
        "cover_ask": "Would you like to add a <b>cover letter</b>? It's considered in the AI review and can strengthen your application.",
        "btn_add_cover": "✍️ Add cover letter",
        "btn_skip": "Skip",
        "cover_prompt": "✍️ Please send your cover letter now — as a text message or a file. It will be considered together with your resume.",
        "cover_send_textfile": "Please send your cover letter as text or a file.",
        "cover_added": "✅ Cover letter added — thank you! Your application is being reviewed. 🍀",
        "application_reviewing": "✅ Thanks! Your application is being reviewed. Good luck! 🍀",
        "test_received": "✅ Your test task was received — thank you! We'll review it shortly.",
        "unsupported_file": "Unsupported file type. Please send a PDF, image, or Word document.",
        "file_too_large": "That file is too large.",
        "inbound_ack": "Thanks — your message was received. The team will get back to you. 🙌",
        "forget_hint": "ℹ️ Send /forget anytime to delete your data.",
    },
    "uz": {
        "welcome": "Rezyumeingizni shu yerga yuboring (PDF, rasm yoki Word hujjat) — biz uni lavozimga moslab tahlil qilamiz.",
        "applying_for": "Siz <b>{title}</b> lavozimiga ariza topshiryapsiz.",
        "position_closed": "Bu lavozim hozir ochiq emas.",
        "no_open_positions": "Hozircha ochiq lavozimlar yo'q.",
        "choose_position": "Iltimos, ariza topshirmoqchi bo'lgan lavozimni tanlang:",
        "choose_position_first": "Avval lavozimni tanlang:",
        "forget_done": "🗑 Barcha ma'lumotlaringiz butunlay o'chirildi. Sog' bo'ling!",
        "forget_none": "Sizga oid saqlangan ma'lumot yo'q.",
        "resume_received": "✅ Rezyume qabul qilindi!",
        "cover_ask": "<b>Motivatsion xat</b> (cover letter) qo'shasizmi? U AI tahlilida hisobga olinadi va arizangizni kuchaytirishi mumkin.",
        "btn_add_cover": "✍️ Motivatsion xat qo'shish",
        "btn_skip": "O'tkazib yuborish",
        "cover_prompt": "✍️ Endi motivatsion xatingizni yuboring — matn yoki fayl ko'rinishida. U rezyume bilan birga ko'rib chiqiladi.",
        "cover_send_textfile": "Iltimos, motivatsion xatni matn yoki fayl sifatida yuboring.",
        "cover_added": "✅ Motivatsion xat qo'shildi — rahmat! Arizangiz ko'rib chiqilmoqda. 🍀",
        "application_reviewing": "✅ Rahmat! Arizangiz ko'rib chiqilmoqda. Omad! 🍀",
        "test_received": "✅ Test topshirig'ingiz qabul qilindi — rahmat! Tez orada ko'rib chiqamiz.",
        "unsupported_file": "Qo'llab-quvvatlanmaydigan fayl turi. PDF, rasm yoki Word hujjat yuboring.",
        "file_too_large": "Bu fayl juda katta.",
        "inbound_ack": "Rahmat — xabaringiz qabul qilindi. Jamoa siz bilan bog'lanadi. 🙌",
        "forget_hint": "ℹ️ Ma'lumotlaringizni o'chirish uchun istalgan vaqt /forget yuboring.",
    },
    "ru": {
        "welcome": "Отправьте сюда своё резюме (PDF, изображение или Word) — мы сопоставим его с вакансией.",
        "applying_for": "Вы откликаетесь на вакансию <b>{title}</b>.",
        "position_closed": "Эта вакансия больше не открыта.",
        "no_open_positions": "Сейчас нет открытых вакансий.",
        "choose_position": "Пожалуйста, выберите вакансию, на которую откликаетесь:",
        "choose_position_first": "Сначала выберите вакансию:",
        "forget_done": "🗑 Все ваши данные полностью удалены. Всего доброго!",
        "forget_none": "У нас нет сохранённых данных о вас.",
        "resume_received": "✅ Резюме получено!",
        "cover_ask": "Хотите добавить <b>сопроводительное письмо</b>? Оно учитывается в AI-анализе и может усилить вашу заявку.",
        "btn_add_cover": "✍️ Добавить письмо",
        "btn_skip": "Пропустить",
        "cover_prompt": "✍️ Отправьте сопроводительное письмо — текстом или файлом. Оно будет рассмотрено вместе с резюме.",
        "cover_send_textfile": "Пожалуйста, отправьте письмо текстом или файлом.",
        "cover_added": "✅ Письмо добавлено — спасибо! Ваша заявка рассматривается. 🍀",
        "application_reviewing": "✅ Спасибо! Ваша заявка рассматривается. Удачи! 🍀",
        "test_received": "✅ Ваше тестовое задание получено — спасибо! Скоро рассмотрим.",
        "unsupported_file": "Неподдерживаемый тип файла. Отправьте PDF, изображение или документ Word.",
        "file_too_large": "Этот файл слишком большой.",
        "inbound_ack": "Спасибо — ваше сообщение получено. Команда свяжется с вами. 🙌",
        "forget_hint": "ℹ️ Отправьте /forget в любой момент, чтобы удалить свои данные.",
    },
}


def t(lang: str | None, key: str, **kwargs) -> str:
    table = MESSAGES.get(lang or DEFAULT_LANG, MESSAGES[DEFAULT_LANG])
    text = table.get(key) or MESSAGES[DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text


def language_keyboard() -> dict:
    # All languages on a single row (side by side).
    return {
        "inline_keyboard": [
            [{"text": LANG_NAMES[code], "callback_data": f"lang_{code}"} for code in SUPPORTED_LANGS]
        ]
    }
