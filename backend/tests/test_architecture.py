"""Testes de arquitetura: garantem automaticamente as regras do docs/ARQUITETURA.md.

Se um destes testes falhar, NÃO desative o teste: ajuste o código para seguir o padrão
(ou discuta a mudança da regra num PR que também atualize a documentação).
"""

import ast
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BACKEND_DIR / "app"
MODULES_DIR = APP_DIR / "modules"
TESTS_DIR = BACKEND_DIR / "tests"

REQUIRED_FILES = (
    "__init__.py",
    "models.py",
    "schemas.py",
    "repository.py",
    "service.py",
    "router.py",
    "permissions.py",
)
# O que um módulo pode importar de OUTRO módulo.
ALLOWED_CROSS_MODULE = {"service", "schemas"}
# Arquivos declarativos: testados indiretamente pelos testes de repository/router/service.
FILES_WITHOUT_OWN_TEST = {"__init__.py", "models.py", "schemas.py"}


def module_names() -> list[str]:
    return sorted(
        d.name for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("__")
    )


def imported_modules(path: Path) -> set[str]:
    """Nomes completos importados pelo arquivo (ex.: 'app.modules.pessoas.service')."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def cross_module_imports(module: str) -> set[tuple[str, str]]:
    """(outro_modulo, arquivo) importados pelo módulo `module`."""
    result: set[tuple[str, str]] = set()
    for path in (MODULES_DIR / module).rglob("*.py"):
        for name in imported_modules(path):
            parts = name.split(".")
            if len(parts) >= 4 and parts[:2] == ["app", "modules"] and parts[2] != module:
                result.add((parts[2], parts[3]))
    return result


def has_code(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        for node in tree.body
    )


@pytest.mark.parametrize("module", module_names())
def test_every_module_has_the_standard_files(module):
    missing = [f for f in REQUIRED_FILES if not (MODULES_DIR / module / f).exists()]
    assert not missing, f"Módulo '{module}' sem os arquivos obrigatórios: {missing}"


@pytest.mark.parametrize("module", module_names())
def test_modules_only_use_service_or_schemas_of_other_modules(module):
    forbidden = {
        (other, file)
        for other, file in cross_module_imports(module)
        if file not in ALLOWED_CROSS_MODULE
    }
    assert not forbidden, (
        f"'{module}' importa internals de outros módulos: {sorted(forbidden)}. "
        "Use o service público do outro módulo."
    )


def test_module_dependency_graph_is_acyclic():
    graph = {m: {other for other, _ in cross_module_imports(m)} for m in module_names()}
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in done:
            return
        assert node not in visiting, f"Dependência circular entre módulos: {' -> '.join(path)}"
        visiting.add(node)
        for neighbor in graph.get(node, set()):
            visit(neighbor, [*path, neighbor])
        visiting.discard(node)
        done.add(node)

    for module in graph:
        visit(module, [module])


@pytest.mark.parametrize("package", ["core", "shared"])
def test_core_and_shared_do_not_depend_on_modules(package):
    offenders = [
        str(path.relative_to(BACKEND_DIR))
        for path in (APP_DIR / package).rglob("*.py")
        if any(name.startswith("app.modules") for name in imported_modules(path))
    ]
    assert not offenders, f"{package}/ não pode importar módulos de negócio: {offenders}"


@pytest.mark.parametrize("module", module_names())
def test_router_does_not_touch_repository_or_models(module):
    imports = imported_modules(MODULES_DIR / module / "router.py")
    bad = {i for i in imports if i.endswith((".repository", ".models"))}
    assert not bad, f"router de '{module}' deve chamar só o service: {bad}"


@pytest.mark.parametrize("module", module_names())
def test_service_does_not_know_http(module):
    imports = imported_modules(MODULES_DIR / module / "service.py")
    bad = {i for i in imports if i.split(".")[0] in {"fastapi", "starlette"}}
    assert not bad, f"service de '{module}' não deve importar FastAPI/Starlette: {bad}"


@pytest.mark.parametrize("module", module_names())
def test_repository_never_commits(module):
    source = (MODULES_DIR / module / "repository.py").read_text(encoding="utf-8")
    assert ".commit(" not in source, "Quem faz commit é o service, ao final do caso de uso."


def expected_test_file(path: Path) -> Path:
    relative = path.relative_to(APP_DIR)
    return TESTS_DIR / relative.parent / f"test_{relative.name}"


def code_files() -> list[Path]:
    return sorted(
        p for p in APP_DIR.rglob("*.py") if p.name not in FILES_WITHOUT_OWN_TEST and has_code(p)
    )


@pytest.mark.parametrize("path", code_files(), ids=lambda p: str(p.relative_to(APP_DIR)))
def test_every_code_file_has_a_test_file(path):
    expected = expected_test_file(path)
    assert expected.exists(), f"Falta o arquivo de teste {expected.relative_to(BACKEND_DIR)}"
