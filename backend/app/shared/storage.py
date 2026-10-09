"""Armazenamento local de arquivos enviados (documentos da matrícula).

- O nome salvo é gerado pelo servidor (UUID): o nome enviado pelo usuário nunca vira caminho.
- O tipo é conferido pelos primeiros bytes ("magic number"), não só pela extensão.
- `resolve` impede path traversal (`../../etc/passwd`).

Para produção, troque por um storage de objetos (S3/MinIO) mantendo as mesmas funções.
"""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError

ALLOWED_TYPES: dict[str, tuple[str, bytes]] = {
    "application/pdf": (".pdf", b"%PDF"),
    "image/png": (".png", b"\x89PNG"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
}


@dataclass(frozen=True)
class StoredFile:
    path: str  # relativo à pasta de uploads
    content_type: str
    original_name: str


def _root() -> Path:
    return Path(settings.upload_dir).resolve()


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(name).name).strip() or "arquivo"
    return cleaned[:100]


def detect_content_type(content: bytes) -> str | None:
    for content_type, (_, magic) in ALLOWED_TYPES.items():
        if content.startswith(magic):
            return content_type
    return None


def save_file(subdir: str, original_name: str, content: bytes) -> StoredFile:
    if not content:
        raise BusinessRuleError("Arquivo vazio.", "ARQUIVO_INVALIDO")
    if len(content) > settings.upload_max_bytes:
        limite_mb = settings.upload_max_bytes // (1024 * 1024)
        raise BusinessRuleError(f"Arquivo maior que {limite_mb} MB.", "ARQUIVO_GRANDE")
    content_type = detect_content_type(content)
    if content_type is None:
        raise BusinessRuleError("Envie um PDF, PNG ou JPG.", "ARQUIVO_INVALIDO")
    extension = ALLOWED_TYPES[content_type][0]
    relative = Path(subdir) / f"{uuid.uuid4().hex}{extension}"
    target = resolve(relative.as_posix())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return StoredFile(relative.as_posix(), content_type, safe_filename(original_name))


def resolve(relative_path: str) -> Path:
    root = _root()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        raise NotFoundError("Arquivo não encontrado.")
    return target


def open_file(relative_path: str) -> Path:
    target = resolve(relative_path)
    if not target.is_file():
        raise NotFoundError("Arquivo não encontrado.")
    return target


def delete_file(relative_path: str) -> None:
    target = resolve(relative_path)
    target.unlink(missing_ok=True)
