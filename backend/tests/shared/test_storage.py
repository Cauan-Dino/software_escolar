import pytest

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.shared import storage

PDF = b"%PDF-1.4 conteudo de teste"
PNG = b"\x89PNG\r\n\x1a\n...."


@pytest.fixture(autouse=True)
def tmp_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


def test_save_and_open_pdf():
    stored = storage.save_file("matriculas/1", "certidão nascimento.pdf", PDF)
    assert stored.content_type == "application/pdf"
    assert stored.path.startswith("matriculas/1/")
    assert stored.path.endswith(".pdf")
    assert storage.open_file(stored.path).read_bytes() == PDF


def test_content_type_comes_from_bytes_not_from_name():
    stored = storage.save_file("x", "foto.pdf", PNG)
    assert stored.content_type == "image/png"
    assert stored.path.endswith(".png")


@pytest.mark.parametrize("content", [b"", b"MZ executavel", b"<script>alert(1)</script>"])
def test_rejects_empty_or_unknown_files(content):
    with pytest.raises(BusinessRuleError):
        storage.save_file("x", "a.pdf", content)


def test_rejects_big_files(monkeypatch):
    monkeypatch.setattr(settings, "upload_max_bytes", 10)
    with pytest.raises(BusinessRuleError) as exc:
        storage.save_file("x", "a.pdf", PDF)
    assert exc.value.code == "ARQUIVO_GRANDE"


def test_path_traversal_is_blocked():
    with pytest.raises(NotFoundError):
        storage.resolve("../../etc/passwd")
    with pytest.raises(NotFoundError):
        storage.open_file("nao/existe.pdf")


def test_safe_filename_strips_directories_and_odd_chars():
    assert storage.safe_filename("../../segredo<>.pdf") == "segredo__.pdf"
    assert storage.safe_filename("") == "arquivo"


def test_delete_file():
    stored = storage.save_file("x", "a.pdf", PDF)
    storage.delete_file(stored.path)
    with pytest.raises(NotFoundError):
        storage.open_file(stored.path)
