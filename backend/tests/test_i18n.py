from app.services.telegram.i18n import (
    MESSAGES,
    SUPPORTED_LANGS,
    language_keyboard,
    t,
)


def test_all_languages_have_the_same_keys():
    en_keys = set(MESSAGES["en"])
    for lang in SUPPORTED_LANGS:
        assert set(MESSAGES[lang]) == en_keys, f"{lang} keys differ from en"


def test_t_returns_localized_text():
    assert t("uz", "file_too_large") == MESSAGES["uz"]["file_too_large"]
    assert t("ru", "file_too_large") == MESSAGES["ru"]["file_too_large"]
    assert t("en", "file_too_large") == MESSAGES["en"]["file_too_large"]


def test_t_formats_variables():
    assert "Acme" in t("uz", "applying_for", title="Acme")
    assert "Acme" in t("ru", "applying_for", title="Acme")


def test_t_falls_back_to_default_for_unknown_lang():
    # Default is Uzbek.
    assert t("de", "file_too_large") == MESSAGES["uz"]["file_too_large"]
    assert t(None, "file_too_large") == MESSAGES["uz"]["file_too_large"]


def test_supported_langs_are_uz_and_ru():
    assert SUPPORTED_LANGS == ("uz", "ru")


def test_language_keyboard_is_single_row_side_by_side():
    kb = language_keyboard()
    rows = kb["inline_keyboard"]
    assert len(rows) == 1  # one row => buttons side by side
    codes = [btn["callback_data"] for btn in rows[0]]
    assert codes == [f"lang_{c}" for c in SUPPORTED_LANGS]
