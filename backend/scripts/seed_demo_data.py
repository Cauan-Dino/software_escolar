"""Popula o banco com dados fictícios em massa para demo/apresentação: turmas,
professores, responsáveis, ~1000 alunos e matrículas em vários status.

Uso:
    uv run python -m scripts.seed_demo_data
    # ou, com o venv local:
    .venv/Scripts/python.exe -m scripts.seed_demo_data

Idempotente na prática: se já existem >= 500 alunos, não faz nada (evita duplicar
ao rodar duas vezes sem querer).
"""

import random
from datetime import date, timedelta

from app.core.database import SessionLocal
from app.modules.auth.models import User  # noqa: F401 — registra a tabela `users` (FKs de pessoas)
from app.modules.matricula.models import Matricula
from app.modules.matricula.schemas import StatusMatricula, TipoMatricula
from app.modules.pessoas.models import Aluno, Professor, Responsavel, ResponsavelAluno
from app.modules.pessoas.schemas import Parentesco
from app.modules.turmas.models import Turma, TurmaProfessor
from app.shared.serie import Serie, Turno

random.seed(42)

TOTAL_ALUNOS = 1000
ANO_LETIVO = 2026
HOJE = date(2026, 10, 9)

NOMES_M = [
    "João", "Pedro", "Lucas", "Gabriel", "Matheus", "Rafael", "Gustavo", "Felipe",
    "Bruno", "Thiago", "Rodrigo", "Carlos", "Eduardo", "Marcos", "André", "Diego",
    "Vitor", "Daniel", "Ricardo", "Fernando", "Leonardo", "Henrique", "Caio", "Davi",
    "Miguel", "Arthur", "Heitor", "Bernardo", "Theo", "Enzo", "Samuel", "Noah",
]
NOMES_F = [
    "Maria", "Ana", "Juliana", "Fernanda", "Patricia", "Camila", "Beatriz", "Larissa",
    "Amanda", "Carla", "Renata", "Simone", "Isabela", "Gabriela", "Laura", "Sofia",
    "Valentina", "Helena", "Alice", "Manuela", "Luiza", "Julia", "Lavínia", "Cecilia",
    "Mariana", "Leticia", "Bianca", "Natalia", "Sabrina", "Vanessa", "Priscila", "Debora",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Monteiro", "Cardoso",
    "Reis", "Araujo", "Castro", "Andrade", "Nascimento", "Moreira", "Nunes", "Marques",
]

SERIES_ORDEM: list[tuple[Serie, int]] = [
    (Serie.MATERNAL_1, 2),
    (Serie.MATERNAL_2, 3),
    (Serie.INFANTIL_1, 4),
    (Serie.INFANTIL_2, 5),
    (Serie.ANO_1, 6),
    (Serie.ANO_2, 7),
    (Serie.ANO_3, 8),
    (Serie.ANO_4, 9),
    (Serie.ANO_5, 10),
]
TURNOS = [Turno.MANHA, Turno.TARDE, Turno.INTEGRAL]
FORMACOES = [
    "Pedagogia", "Letras", "Matemática", "Educação Física", "Artes",
    "Ciências Biológicas", "História", "Geografia", "Normal Superior",
]


def _cpf(seed: int) -> str:
    """Gera um CPF com dígitos verificadores válidos a partir de um inteiro único."""
    base = [int(d) for d in f"{seed:09d}"]

    def digito(digits: list[int]) -> int:
        soma = sum(d * peso for d, peso in zip(digits, range(len(digits) + 1, 1, -1), strict=True))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    d1 = digito(base)
    d2 = digito([*base, d1])
    return "".join(str(d) for d in [*base, d1, d2])


def _telefone(seed: int) -> str:
    return f"(11) 9{seed % 10000:04d}-{(seed * 7) % 10000:04d}"


def _nome_completo(masculino: bool) -> str:
    primeiro = random.choice(NOMES_M if masculino else NOMES_F)
    sobrenomes = random.sample(SOBRENOMES, k=2)
    return f"{primeiro} {sobrenomes[0]} {sobrenomes[1]}"


def _email(nome: str, seed: int) -> str:
    slug = nome.lower().replace(" ", ".")
    for a, b in [("á", "a"), ("ã", "a"), ("â", "a"), ("é", "e"), ("ê", "e"), ("í", "i"), ("ó", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")]:
        slug = slug.replace(a, b)
    return f"{slug}{seed}@email.com"


def main() -> None:
    with SessionLocal() as db:
        ja_tem = db.query(Aluno).count()
        if ja_tem >= 500:
            print(f"Já existem {ja_tem} alunos no banco. Nada a fazer (script é só para popular um banco vazio).")
            return

        print("Criando turmas...")
        turmas: dict[tuple[Serie, Turno], Turma] = {}
        for serie, _idade in SERIES_ORDEM:
            for turno in TURNOS:
                t = Turma(serie=serie, ano_letivo=ANO_LETIVO, turno=turno, capacidade=30, vagas_ocupadas=0)
                db.add(t)
                turmas[(serie, turno)] = t
        db.flush()

        print("Criando professores...")
        professores: list[Professor] = []
        for i in range(24):
            masculino = i % 2 == 0
            nome = _nome_completo(masculino)
            p = Professor(
                nome=nome,
                cpf=_cpf(700_000_000 + i),
                email=_email(nome, i),
                telefone=_telefone(700_000 + i),
                formacao=random.choice(FORMACOES),
            )
            db.add(p)
            professores.append(p)
        db.flush()

        # 1-2 professores por turma.
        for t in turmas.values():
            for p in random.sample(professores, k=random.choice([1, 2])):
                db.add(TurmaProfessor(turma_id=t.id, professor_id=p.id))

        print(f"Criando {TOTAL_ALUNOS} alunos, responsáveis e matrículas...")
        responsaveis_pool: list[Responsavel] = []
        alunos_criados = 0
        matriculas_criadas = 0
        rng_cpf_resp = 100_000_000
        rng_cpf_aluno = 300_000_000

        for i in range(TOTAL_ALUNOS):
            serie, idade = random.choices(SERIES_ORDEM, weights=[10, 10, 11, 11, 13, 13, 12, 11, 9])[0]
            turno = random.choice(TURNOS)
            masculino = random.random() < 0.5
            nome_aluno = _nome_completo(masculino)

            nasc = date(HOJE.year - idade, random.randint(1, 12), random.randint(1, 28))

            aluno = Aluno(nome=nome_aluno, data_nascimento=nasc, cpf=None)
            db.add(aluno)
            db.flush()
            alunos_criados += 1

            # ~35% de chance de reaproveitar um responsável já existente (irmãos).
            if responsaveis_pool and random.random() < 0.35:
                responsavel = random.choice(responsaveis_pool)
            else:
                mae = random.random() < 0.55
                nome_resp = _nome_completo(not mae)
                rng_cpf_resp += 1
                responsavel = Responsavel(
                    nome=nome_resp,
                    cpf=_cpf(rng_cpf_resp),
                    email=_email(nome_resp, rng_cpf_resp),
                    telefone=_telefone(rng_cpf_resp),
                )
                db.add(responsavel)
                db.flush()
                responsaveis_pool.append(responsavel)

            parentesco = random.choices(
                [Parentesco.MAE, Parentesco.PAI, Parentesco.AVO, Parentesco.TIO, Parentesco.OUTRO],
                weights=[45, 40, 8, 4, 3],
            )[0]
            db.add(
                ResponsavelAluno(
                    responsavel_id=responsavel.id,
                    aluno_id=aluno.id,
                    parentesco=parentesco,
                    responsavel_financeiro=True,
                    pode_buscar=True,
                )
            )

            # Status da matrícula: a maioria ATIVA numa turma, parte em análise/pré.
            roll = random.random()
            turma = turmas[(serie, turno)]
            if roll < 0.75 and turma.vagas_ocupadas < turma.capacidade:
                status = StatusMatricula.ATIVA
                turma_id = turma.id
                turma.vagas_ocupadas += 1
                decidido_em = HOJE - timedelta(days=random.randint(5, 120))
            elif roll < 0.9:
                status = StatusMatricula.EM_ANALISE
                turma_id = None
                decidido_em = None
            else:
                status = StatusMatricula.PRE_MATRICULA
                turma_id = None
                decidido_em = None

            db.add(
                Matricula(
                    aluno_id=aluno.id,
                    ano_letivo=ANO_LETIVO,
                    serie=serie,
                    turno=turno,
                    turma_id=turma_id,
                    tipo=TipoMatricula.NOVA,
                    status=status,
                    criado_por_user_id=1,
                    decidido_por_user_id=1 if decidido_em else None,
                    decidido_em=decidido_em,
                )
            )
            matriculas_criadas += 1

            if alunos_criados % 100 == 0:
                db.commit()
                print(f"  {alunos_criados}/{TOTAL_ALUNOS}...")

        db.commit()
        print(
            f"Pronto: {alunos_criados} alunos, {len(responsaveis_pool)} responsáveis, "
            f"{len(professores)} professores, {len(turmas)} turmas, {matriculas_criadas} matrículas."
        )


if __name__ == "__main__":
    main()
