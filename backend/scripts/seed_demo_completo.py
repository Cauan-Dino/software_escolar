"""Completa o sistema com dados fictícios: funcionários, logins de equipe, tabela de preços,
bolsas, cobranças, notas (todas as disciplinas), frequência, calendário e avisos.

Complementa `seed_demo_data` (que cria turmas/professores/alunos/matrículas). É ADITIVO: não
altera nem apaga nada que já existe, e cada seção é pulada se a tabela dela já tiver dados.

Uso (dentro do ambiente da API):
    python -m scripts.seed_demo_completo --dry-run   # executa tudo e faz rollback
    python -m scripts.seed_demo_completo             # grava de verdade
"""

import random
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.roles import Role
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.calendario.models import EventoCalendario
from app.modules.calendario.schemas import TipoEvento
from app.modules.comunicacao.models import Aviso
from app.modules.comunicacao.schemas import PublicoAlvo
from app.modules.financeiro.models import (
    Bolsa,
    Cobranca,
    StatusCobranca,
    TabelaPreco,
    TipoCobranca,
)
from app.modules.frequencia.models import Frequencia
from app.modules.frequencia.schemas import StatusFrequencia
from app.modules.matricula.models import Matricula
from app.modules.matricula.schemas import StatusMatricula
from app.modules.notas.models import Nota
from app.modules.notas.schemas import DISCIPLINAS, Periodo
from app.modules.pessoas.models import Aluno, Funcionario, Professor
from app.modules.pessoas.schemas import TipoFuncionario
from app.modules.turmas.models import Turma, TurmaProfessor
from app.shared.serie import Serie

random.seed(2026)

ANO = 2026
HOJE = date(2026, 10, 9)
INICIO_AULAS = date(2026, 2, 2)
ADMIN_ID = 1

FERIADOS = {
    date(2026, 2, 16): "Segunda de Carnaval",
    date(2026, 2, 17): "Terça de Carnaval",
    date(2026, 4, 3): "Sexta-feira Santa",
    date(2026, 4, 21): "Tiradentes",
    date(2026, 5, 1): "Dia do Trabalho",
    date(2026, 6, 4): "Corpus Christi",
    date(2026, 9, 7): "Independência do Brasil",
    date(2026, 10, 12): "Nossa Senhora Aparecida",
    date(2026, 11, 2): "Finados",
    date(2026, 11, 15): "Proclamação da República",
    date(2026, 12, 25): "Natal",
}
RECESSO = (date(2026, 7, 6), date(2026, 7, 17))  # recesso escolar de julho

FUNCIONARIOS = [
    ("Marta Aparecida Nogueira", "Secretária escolar", TipoFuncionario.ADMINISTRATIVO),
    ("Cláudia Regina Teixeira", "Coordenadora pedagógica", TipoFuncionario.ADMINISTRATIVO),
    ("Roberto Carlos Pacheco", "Diretor", TipoFuncionario.ADMINISTRATIVO),
    ("Sandra Helena Borges", "Tesoureira", TipoFuncionario.ADMINISTRATIVO),
    ("Paulo Sérgio Mendonça", "Auxiliar administrativo", TipoFuncionario.ADMINISTRATIVO),
    ("Adriana Cristina Farias", "Psicopedagoga", TipoFuncionario.ADMINISTRATIVO),
    ("Joana D'Arc Medeiros", "Recepcionista", TipoFuncionario.ADMINISTRATIVO),
    ("Antônio Carlos Bezerra", "Porteiro", TipoFuncionario.PRESTADOR_SERVICO),
    ("Lúcia Maria Figueiredo", "Auxiliar de limpeza", TipoFuncionario.PRESTADOR_SERVICO),
    ("Raimunda Nonata Sales", "Cozinheira", TipoFuncionario.PRESTADOR_SERVICO),
    ("José Ailton Ramos", "Motorista do transporte escolar", TipoFuncionario.PRESTADOR_SERVICO),
    ("Eliane Cristina Duarte", "Monitora de recreação", TipoFuncionario.PRESTADOR_SERVICO),
]

PRECOS = {  # série: (matrícula, mensalidade)
    Serie.MATERNAL_1: (Decimal("480.00"), Decimal("890.00")),
    Serie.MATERNAL_2: (Decimal("480.00"), Decimal("890.00")),
    Serie.INFANTIL_1: (Decimal("520.00"), Decimal("950.00")),
    Serie.INFANTIL_2: (Decimal("520.00"), Decimal("950.00")),
    Serie.ANO_1: (Decimal("580.00"), Decimal("1050.00")),
    Serie.ANO_2: (Decimal("580.00"), Decimal("1050.00")),
    Serie.ANO_3: (Decimal("620.00"), Decimal("1120.00")),
    Serie.ANO_4: (Decimal("620.00"), Decimal("1120.00")),
    Serie.ANO_5: (Decimal("650.00"), Decimal("1190.00")),
}

MOTIVOS_BOLSA = [
    "Bolsa irmãos", "Bolsa mérito acadêmico", "Convênio empresa parceira",
    "Bolsa social", "Desconto funcionário", "Bolsa esportiva",
]


def _cpf(seed: int) -> str:
    base = [int(d) for d in f"{seed:09d}"]

    def digito(digits: list[int]) -> int:
        soma = sum(d * p for d, p in zip(digits, range(len(digits) + 1, 1, -1), strict=True))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    d1 = digito(base)
    d2 = digito([*base, d1])
    return "".join(str(d) for d in [*base, d1, d2])


def _dia_letivo(d: date) -> bool:
    if d.weekday() >= 5 or d in FERIADOS:
        return False
    return not (RECESSO[0] <= d <= RECESSO[1])


def _dias_letivos(ate: date) -> list[date]:
    dias, d = [], INICIO_AULAS
    while d <= ate:
        if _dia_letivo(d):
            dias.append(d)
        d += timedelta(days=1)
    return dias


def _nota(base: float, bimestre: int) -> float:
    valor = random.gauss(base + (0.1 * (bimestre - 1)), 1.0)
    return round(min(10.0, max(0.0, valor)), 1)


def _dt(d: date, hora: int = 9) -> datetime:
    return datetime(d.year, d.month, d.day, hora, 0, tzinfo=timezone.utc)


def secao_funcionarios(db) -> None:
    if db.scalar(select(func.count()).select_from(Funcionario)):
        print("[funcionarios] já existem — pulando")
        return
    for i, (nome, cargo, tipo) in enumerate(FUNCIONARIOS):
        slug = nome.lower().split()[0].replace("á", "a").replace("ú", "u").replace("é", "e")
        db.add(
            Funcionario(
                nome=nome,
                cpf=_cpf(500_000_000 + i),
                email=f"{slug}.{i}@semeando.edu.br",
                telefone=f"(11) 9{8000 + i:04d}-{1000 + i * 37:04d}",
                cargo=cargo,
                tipo=tipo,
            )
        )
    print(f"[funcionarios] {len(FUNCIONARIOS)} criados")


def secao_logins(db) -> list[tuple[str, str, str]]:
    """Cria logins de equipe (secretaria, financeiro, 2 professores) com senha aleatória."""
    criados: list[tuple[str, str, str]] = []
    alvos = [
        ("secretaria@semeando.edu.br", "Marta Aparecida Nogueira", Role.SECRETARIA, None),
        ("financeiro@semeando.edu.br", "Sandra Helena Borges", Role.FINANCEIRO, None),
    ]
    professores = db.scalars(
        select(Professor)
        .join(TurmaProfessor, TurmaProfessor.professor_id == Professor.id)
        .where(Professor.user_id.is_(None), Professor.deleted_at.is_(None))
        .distinct()
        .order_by(Professor.id)
        .limit(2)
    ).all()
    for p in professores:
        slug = ".".join(p.nome.lower().split()[:2]).replace("é", "e").replace("á", "a")
        alvos.append((f"{slug}@semeando.edu.br", p.nome, Role.PROFESSOR, p))

    for email, nome, role, professor in alvos:
        if db.scalar(select(User).where(User.email == email)):
            continue
        senha = secrets.token_urlsafe(9)
        user = User(email=email, nome=nome, password_hash=hash_password(senha), role=role, is_active=True)
        db.add(user)
        db.flush()
        if professor is not None:
            professor.user_id = user.id
        criados.append((role.value, email, senha))
    print(f"[logins] {len(criados)} criados")
    return criados


def secao_precos(db) -> None:
    if db.scalar(select(func.count()).select_from(TabelaPreco)):
        print("[precos] já existem — pulando")
        return
    for serie, (mat, mens) in PRECOS.items():
        db.add(TabelaPreco(serie=serie.value, ano_letivo=ANO, valor_matricula=mat, valor_mensalidade=mens))
    print(f"[precos] {len(PRECOS)} criados")


def _alunos_ativos(db) -> list[tuple[int, int, int, Serie]]:
    """(aluno_id, matricula_id, turma_id, serie) das matrículas ATIVAS com turma."""
    rows = db.execute(
        select(Matricula.aluno_id, Matricula.id, Matricula.turma_id, Matricula.serie)
        .where(
            Matricula.status == StatusMatricula.ATIVA,
            Matricula.ano_letivo == ANO,
            Matricula.turma_id.is_not(None),
        )
        .order_by(Matricula.id)
    ).all()
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def secao_bolsas_cobrancas(db, ativos) -> None:
    if db.scalar(select(func.count()).select_from(Bolsa)) or db.scalar(select(func.count()).select_from(Cobranca)):
        print("[financeiro] já existem bolsas/cobranças — pulando")
        return

    bolsistas: dict[int, Decimal] = {}
    for aluno_id, *_ in random.sample(ativos, k=int(len(ativos) * 0.07)):
        pct = Decimal(random.choice([10, 15, 20, 25, 30, 50]))
        bolsistas[aluno_id] = pct
        db.add(
            Bolsa(
                aluno_id=aluno_id,
                percentual_desconto=pct,
                motivo=random.choice(MOTIVOS_BOLSA),
                vigencia_inicio=date(ANO, 1, 1),
                vigencia_fim=date(ANO, 12, 31),
            )
        )

    competencias = [f"{ANO}-{m:02d}" for m in range(2, HOJE.month + 1)]
    n = 0
    for aluno_id, matricula_id, _turma, serie in ativos:
        preco_mat, preco_mens = PRECOS[serie]
        pct = bolsistas.get(aluno_id, Decimal(0))
        # Perfil do pagador: pontual, atrasa às vezes, ou inadimplente a partir de um mês.
        perfil = random.choices(["pontual", "atrasa", "inadimplente"], weights=[78, 14, 8])[0]
        corte = random.choice(competencias[3:-1]) if perfil == "inadimplente" else None

        venc_mat = date(ANO, 1, 15)
        db.add(
            Cobranca(
                aluno_id=aluno_id, matricula_id=matricula_id, tipo=TipoCobranca.MATRICULA,
                competencia=None, valor_original=preco_mat, valor_desconto=Decimal(0),
                valor_final=preco_mat, vencimento=venc_mat, status=StatusCobranca.PAGA,
                pago_em=_dt(venc_mat - timedelta(days=random.randint(0, 5)), 14),
                gateway_referencia=f"fake-{secrets.token_hex(6)}",
            )
        )
        n += 1

        for comp in competencias:
            ano, mes = (int(p) for p in comp.split("-"))
            venc = date(ano, mes, 10)
            desconto = (preco_mens * pct / Decimal(100)).quantize(Decimal("0.01"))
            final = preco_mens - desconto
            pago_em, ref = None, None
            if venc > HOJE:
                status = StatusCobranca.PENDENTE
            elif perfil == "inadimplente" and comp >= corte:
                status = StatusCobranca.ATRASADA
            elif mes == HOJE.month:  # vence hoje ou já venceu neste mês
                if random.random() < 0.6:
                    status = StatusCobranca.PAGA
                    pago_em = _dt(venc - timedelta(days=random.randint(0, 6)), 11)
                else:
                    status = StatusCobranca.ATRASADA if venc < HOJE - timedelta(days=5) else StatusCobranca.PENDENTE
            else:
                status = StatusCobranca.PAGA
                atraso = random.randint(1, 12) if perfil == "atrasa" and random.random() < 0.5 else -random.randint(0, 8)
                pago_em = _dt(min(venc + timedelta(days=atraso), HOJE), 10)
            if status == StatusCobranca.PAGA:
                ref = f"fake-{secrets.token_hex(6)}"
            db.add(
                Cobranca(
                    aluno_id=aluno_id, matricula_id=matricula_id, tipo=TipoCobranca.MENSALIDADE,
                    competencia=comp, valor_original=preco_mens, valor_desconto=desconto,
                    valor_final=final, vencimento=venc, status=status, pago_em=pago_em,
                    gateway_referencia=ref,
                )
            )
            n += 1
    print(f"[financeiro] {len(bolsistas)} bolsas, {n} cobranças")


def secao_notas(db, ativos) -> None:
    if db.scalar(select(func.count()).select_from(Nota)):
        print("[notas] já existem — pulando")
        return
    # Quem lança: um professor com login da turma, senão a administração.
    prof_user = {
        tp.turma_id: u
        for tp, u in db.execute(
            select(TurmaProfessor, Professor.user_id)
            .join(Professor, Professor.id == TurmaProfessor.professor_id)
            .where(Professor.user_id.is_not(None))
        ).all()
    }
    n = 0
    for aluno_id, _mat, turma_id, _serie in ativos:
        habilidade = min(9.6, max(3.5, random.gauss(7.3, 1.3)))
        lancador = prof_user.get(turma_id, ADMIN_ID)
        for disc in DISCIPLINAS:
            afinidade = random.gauss(0, 0.8)
            for bim, periodo in enumerate(
                [Periodo.BIMESTRE_1, Periodo.BIMESTRE_2, Periodo.BIMESTRE_3, Periodo.BIMESTRE_4], start=1
            ):
                if bim == 4 and disc not in ("Português", "Matemática"):
                    continue  # 4º bimestre em andamento: só as provas já aplicadas
                valor = _nota(habilidade + afinidade, bim)
                db.add(
                    Nota(
                        aluno_id=aluno_id, turma_id=turma_id, disciplina=disc, periodo=periodo,
                        valor=valor, lancado_por_user_id=lancador,
                        observacao="Precisa de reforço" if valor < 5 and random.random() < 0.4 else None,
                    )
                )
                n += 1
        if n % 5000 < 40:
            db.flush()
    print(f"[notas] {n} lançamentos ({len(DISCIPLINAS)} disciplinas)")


def secao_frequencia(db, ativos) -> None:
    if db.scalar(select(func.count()).select_from(Frequencia)):
        print("[frequencia] já existe — pulando")
        return
    dias = _dias_letivos(HOJE - timedelta(days=1))
    rows: list[dict] = []
    for aluno_id, _mat, turma_id, _serie in ativos:
        p_falta = random.choices([0.02, 0.05, 0.10, 0.22], weights=[55, 30, 11, 4])[0]
        for d in dias:
            r = random.random()
            if r < p_falta * 0.75:
                status, obs = StatusFrequencia.FALTA, None
            elif r < p_falta:
                status = StatusFrequencia.FALTA_JUSTIFICADA
                obs = random.choice(["Atestado médico", "Consulta médica", "Viagem em família", "Doença"])
            else:
                status, obs = StatusFrequencia.PRESENTE, None
            rows.append(
                {"aluno_id": aluno_id, "turma_id": turma_id, "data": d, "status": status,
                 "observacao": obs, "lancado_por_user_id": ADMIN_ID}
            )
        if len(rows) >= 20_000:
            db.bulk_insert_mappings(Frequencia, rows)
            rows.clear()
    if rows:
        db.bulk_insert_mappings(Frequencia, rows)
    print(f"[frequencia] {len(ativos)} alunos × {len(dias)} dias letivos")


def secao_calendario(db, turmas: list[int]) -> None:
    if db.scalar(select(func.count()).select_from(EventoCalendario)):
        print("[calendario] já existe — pulando")
        return
    eventos: list[tuple] = []
    for d, nome in FERIADOS.items():
        eventos.append((nome, None, d, None, TipoEvento.FERIADO, None))
    eventos += [
        ("Início do ano letivo", "Boas-vindas a alunos e famílias.", date(2026, 2, 2), None, TipoEvento.EVENTO, None),
        ("Reunião de pais — 1º bimestre", "Entrega de boletins e conversa com professores.", date(2026, 4, 18), None, TipoEvento.REUNIAO, None),
        ("Reunião de pais — 2º bimestre", "Entrega de boletins e conversa com professores.", date(2026, 6, 27), None, TipoEvento.REUNIAO, None),
        ("Reunião de pais — 3º bimestre", "Entrega de boletins e conversa com professores.", date(2026, 9, 26), None, TipoEvento.REUNIAO, None),
        ("Reunião de pais — 4º bimestre", "Entrega de boletins finais.", date(2026, 12, 12), None, TipoEvento.REUNIAO, None),
        ("Festa Junina", "Quadrilha, comidas típicas e brincadeiras. Traje caipira.", date(2026, 6, 20), None, TipoEvento.EVENTO, None),
        ("Recesso escolar de julho", None, RECESSO[0], RECESSO[1], TipoEvento.OUTRO, None),
        ("Semana da Criança", "Atividades recreativas durante toda a semana.", date(2026, 10, 5), date(2026, 10, 9), TipoEvento.EVENTO, None),
        ("Feira de Ciências", "Apresentação dos projetos dos alunos do Fundamental.", date(2026, 10, 24), None, TipoEvento.EVENTO, None),
        ("Show de Talentos", "Apresentações artísticas dos alunos.", date(2026, 11, 7), None, TipoEvento.EVENTO, None),
        ("Formatura do 5º ano", "Cerimônia de conclusão do Fundamental I.", date(2026, 12, 17), None, TipoEvento.EVENTO, None),
        ("Encerramento do ano letivo", None, date(2026, 12, 18), None, TipoEvento.EVENTO, None),
    ]
    for bim, (ini, fim) in enumerate(
        [(date(2026, 3, 23), date(2026, 3, 27)), (date(2026, 6, 1), date(2026, 6, 5)),
         (date(2026, 9, 14), date(2026, 9, 18)), (date(2026, 11, 30), date(2026, 12, 4))], start=1
    ):
        eventos.append((f"Semana de provas — {bim}º bimestre", "Avaliações de todas as disciplinas.", ini, fim, TipoEvento.PROVA, None))
    for turma_id in random.sample(turmas, k=min(6, len(turmas))):
        eventos.append(("Prova de Matemática", "Conteúdo: capítulos 5 a 8.", date(2026, 10, random.randint(13, 30)), None, TipoEvento.PROVA, turma_id))
        eventos.append(("Passeio ao museu", "Autorização assinada obrigatória.", date(2026, 11, random.randint(3, 27)), None, TipoEvento.EVENTO, turma_id))
    for titulo, desc, ini, fim, tipo, turma_id in eventos:
        db.add(EventoCalendario(titulo=titulo, descricao=desc, data_inicio=ini, data_fim=fim,
                                tipo=tipo, turma_id=turma_id, criado_por_user_id=ADMIN_ID))
    print(f"[calendario] {len(eventos)} eventos")


def secao_avisos(db, turmas: list[int]) -> None:
    if db.scalar(select(func.count()).select_from(Aviso)):
        print("[avisos] já existem — pulando")
        return
    avisos = [
        ("Bem-vindos ao ano letivo 2026!", "Desejamos um excelente ano a todos. O calendário completo está disponível no portal.", PublicoAlvo.TODOS, None, True, date(2026, 2, 1)),
        ("Uniforme obrigatório", "Lembramos que o uso do uniforme completo é obrigatório de segunda a sexta.", PublicoAlvo.RESPONSAVEIS, None, False, date(2026, 2, 9)),
        ("Reunião pedagógica", "Reunião de planejamento com todos os professores na próxima sexta, às 17h.", PublicoAlvo.PROFESSORES, None, False, date(2026, 3, 10)),
        ("Vacinação contra a gripe", "Campanha de vacinação na escola em parceria com o posto de saúde. Traga a carteirinha.", PublicoAlvo.RESPONSAVEIS, None, False, date(2026, 4, 6)),
        ("Festa Junina — como participar", "A festa será no dia 20/06. Contamos com doações de prendas e comidas típicas.", PublicoAlvo.TODOS, None, False, date(2026, 5, 25)),
        ("Boletim do 2º bimestre disponível", "O boletim já pode ser consultado no portal do responsável.", PublicoAlvo.RESPONSAVEIS, None, False, date(2026, 6, 26)),
        ("Aviso de recesso", "Recesso escolar de 06 a 17 de julho. As aulas retornam em 20/07.", PublicoAlvo.TODOS, None, False, date(2026, 6, 30)),
        ("Mensalidades de setembro", "Lembramos que o vencimento é no dia 10. Evite multa e juros pagando em dia.", PublicoAlvo.RESPONSAVEIS, None, False, date(2026, 9, 1)),
        ("Semana da Criança", "Teremos atividades especiais de 05 a 09/10. Venha com roupa confortável!", PublicoAlvo.TODOS, None, True, date(2026, 10, 1)),
        ("Feira de Ciências em 24/10", "Os alunos do Fundamental apresentarão seus projetos. Convidamos todas as famílias.", PublicoAlvo.TODOS, None, False, date(2026, 10, 6)),
    ]
    for turma_id in random.sample(turmas, k=min(4, len(turmas))):
        avisos.append(("Material para o projeto de artes", "Trazer cola, tesoura sem ponta e papel colorido até quinta-feira.", PublicoAlvo.TURMA, turma_id, False, date(2026, 10, random.randint(1, 8))))
    for titulo, corpo, publico, turma_id, fixado, quando in avisos:
        db.add(Aviso(titulo=titulo, corpo=corpo, publico_alvo=publico, turma_id=turma_id, fixado=fixado,
                     publicado_por_user_id=ADMIN_ID, publicado_em=_dt(quando, 8)))
    print(f"[avisos] {len(avisos)} avisos")


def main() -> None:
    dry = "--dry-run" in sys.argv
    with SessionLocal() as db:
        secao_funcionarios(db)
        logins = secao_logins(db)
        secao_precos(db)
        db.flush()

        ativos = _alunos_ativos(db)
        turmas = list(db.scalars(select(Turma.id).where(Turma.ano_letivo == ANO)))
        print(f"Base: {len(ativos)} matrículas ATIVAS com turma, {len(turmas)} turmas")

        secao_bolsas_cobrancas(db, ativos)
        secao_notas(db, ativos)
        secao_frequencia(db, ativos)
        secao_calendario(db, turmas)
        secao_avisos(db, turmas)

        if dry:
            db.rollback()
            print("DRY-RUN: tudo revertido, nada foi gravado.")
        else:
            db.commit()
            print("OK: gravado.")
        for role, email, senha in logins:
            print(f"LOGIN {role} {email} {'(dry-run: descartado)' if dry else senha}")


if __name__ == "__main__":
    main()
