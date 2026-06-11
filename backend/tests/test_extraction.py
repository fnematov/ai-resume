from app.services.extraction import (
    ALLOWED_EXTENSIONS,
    DOCX_MIME,
    PDF_MIME,
    guess_mime,
    normalize_document,
)


def test_guess_mime_by_extension():
    assert guess_mime("resume.pdf") == PDF_MIME
    assert guess_mime("photo.PNG") == "image/png"
    assert guess_mime("cv.docx") == DOCX_MIME
    assert guess_mime("unknown.xyz", "application/x-thing") == "application/x-thing"


def test_allowed_extensions_cover_expected_types():
    for ext in (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".docx"):
        assert ext in ALLOWED_EXTENSIONS


def test_normalize_image_is_native():
    doc = normalize_document(b"\x89PNG fake", "shot.png", "image/png")
    assert doc.is_native
    assert doc.media_type == "image/png"


def test_normalize_plaintext_fallback():
    doc = normalize_document(b"just some text", "notes.txt", "text/plain")
    assert not doc.is_native
    assert "just some text" in (doc.text or "")


def test_normalize_pdf_keeps_native_even_if_textless():
    # Not a real PDF; text extraction fails gracefully but stays native.
    doc = normalize_document(b"%PDF-1.4 broken", "cv.pdf", PDF_MIME)
    assert doc.is_native
    assert doc.media_type == PDF_MIME
