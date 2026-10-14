# @vertical denuncia
"""
Congela, em CSV versionado, o recorte de denúncias que sustenta o relatório
"Os primeiros 14 dias da proibição".

🔴 POR QUE CONGELAR, E NÃO LER O BANCO NA GERAÇÃO. Os dois relatórios que já
existem — arrecadação e bloqueio — leem CSV, nunca o banco vivo. Não é zelo
inútil: `complaints` recebe linha nova a cada minuto, e um relatório que
consulta na hora da geração muda de número entre o PDF, o card social e a
landing. O CSV é o artefato que prova o que foi publicado.

🔴 NENHUMA LINHA INDIVIDUAL SAI DAQUI. O congelado é agregado: contagem por dia,
por categoria e por tipo de domínio. `description` e `reporter_email` NUNCA são
exportados — são texto de terceiro, com PII, e o relatório não precisa deles
para o que afirma. [[reference_despublicacao_por_iniciais]]

Uso:
    python3 scripts/relatorio-mp1394/congela.py            # corte padrão: 09/10
    CORTE=2026-10-09 python3 scripts/relatorio-mp1394/congela.py

Precisa de SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY em .env.local.
"""
import csv, json, os, pathlib, re, sys, urllib.parse, urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[2]
SAIDA = RAIZ / ".lovable/research/mp1394-2026-10/datasets"

# ── a janela, e por que estas datas ─────────────────────────────────────────
# MP 1.394 publicada em 25/09/2026, em vigor desde a publicação (art. 7º §1º:
# depósitos vedados já nesse dia). O dia 0 é 25/09; 14 dias cheios terminam em
# 09/10. A janela de comparação tem o MESMO número de dias ANTES do dia 0, para
# que a razão por dia não dependa do tamanho do recorte — foi exatamente esse o
# erro que quase virou manchete: medir só o depois faz qualquer coisa parecer
# novidade. [[feedback_medir_o_recorte_e_concluir_do_todo]]
import datetime

MP_VIGENCIA = "2026-09-25"
# O corte MANDA, e os dias saem dele. Antes isto era ao contrário — `DIAS` fixo
# em 14 e `CORTE` lido e nunca usado, de modo que a mensagem de erro mandava
# passar uma variável que não fazia nada. Com o corte mandando, `CORTE=` encolhe
# a janela de verdade, e `DIAS` passa a ser consequência medida, não promessa.
CORTE = os.environ.get("CORTE", "2026-10-09")

def dia(iso, delta):
    return (datetime.date.fromisoformat(iso) + datetime.timedelta(days=delta)).isoformat()

DIAS = (datetime.date.fromisoformat(CORTE) - datetime.date.fromisoformat(MP_VIGENCIA)).days
if DIAS < 1:
    sys.exit(f"🔴 CORTE={CORTE} não é depois da vigência ({MP_VIGENCIA}).")

DEPOIS_INI, DEPOIS_FIM = MP_VIGENCIA, CORTE                   # [0, +DIAS)

# ── 🔴 O BASELINE NÃO É A JANELA SIMÉTRICA, E ISSO É MEDIDO ─────────────────
# A escolha óbvia seria comparar com os mesmos DIAS imediatamente antes da MP.
# Medido, essa janela está CONTAMINADA: de 17 a 24/09 as denúncias caíram para
# mediana de 3,5/dia contra 13,0/dia no período estável, e em 18/09 não houve
# nenhuma. Não foi o formulário: `form_submissions` acompanha `complaints` 1 a 1
# o tempo todo. O que caiu foi gente CHEGANDO — `form_submission_events` foi de
# ~80/dia para 13 em 18/09. Problema de tráfego a montante, causa não apurada.
#
# Comparar contra esses dias daria ~12×. Contra o período estável dá ~4,5×. O
# relatório publica o segundo, e diz por quê — o primeiro erraria por um fator
# de quase 3. [[feedback_limiar_de_alarme_sem_n]]
REF_INI, REF_FIM = "2026-07-01", "2026-09-17"   # estável, 77 dias
ANOMALIA_INI, ANOMALIA_FIM = "2026-09-17", MP_VIGENCIA  # excluída, declarada
ANTES_INI, ANTES_FIM = REF_INI, REF_FIM

# ── trava 1: o corte não pode estar no futuro ───────────────────────────────
if datetime.date.fromisoformat(DEPOIS_FIM) > datetime.date.today():
    sys.exit(
        f"🔴 a janela termina em {DEPOIS_FIM} e hoje é {datetime.date.today()}.\n"
        f"   Gerar agora publicaria {DIAS} dias contando dias que não existem.\n"
        f"   Rode a partir de {DEPOIS_FIM}, ou passe CORTE= para um recorte menor\n"
        f"   — e então mude o título, porque ele promete 14 dias."
    )

# ── credenciais ─────────────────────────────────────────────────────────────
env_path = RAIZ / ".env.local"
if not env_path.exists():
    sys.exit(f"🔴 {env_path} não existe.")
env = {}
for linha in env_path.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^([A-Z0-9_]+)\s*=\s*(.*)$", linha.strip())
    if m:
        env[m.group(1)] = m.group(2).strip().strip("\"'")
for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
    if not env.get(k):
        sys.exit(f"🔴 {k} ausente em .env.local")

BASE = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/"
CAB = {"apikey": env["SUPABASE_SERVICE_ROLE_KEY"],
       "Authorization": "Bearer " + env["SUPABASE_SERVICE_ROLE_KEY"]}

def consulta(tabela, params):
    # ⚠️ PostgREST corta em 1.000 linhas SEM erro. Paginamos sempre.
    todas, passo, inicio = [], 1000, 0
    while True:
        q = dict(params); q["limit"] = passo; q["offset"] = inicio
        url = BASE + tabela + "?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers=CAB)
        lote = json.loads(urllib.request.urlopen(req, timeout=120).read())
        todas.extend(lote)
        if len(lote) < passo:
            return todas
        inicio += passo

# ── leitura ─────────────────────────────────────────────────────────────────
linhas = consulta("complaints", {
    "select": "created_at,problem_type,platform_url",
    "created_at": f"gte.{REF_INI}",
    "order": "created_at",
})
linhas = [r for r in linhas if r["created_at"][:10] < DEPOIS_FIM]

def fase(iso):
    """Três fases, não duas. A anomalia tem nome e fica de fora das razões."""
    d = iso[:10]
    if d >= MP_VIGENCIA:
        return "depois"
    if d >= ANOMALIA_INI:
        return "anomalia"
    return "referencia"

def dominio(url):
    """🔴 `sem_url` exige que NÃO haja URL de verdade, não só string vazia.

    A primeira versão testava só `if not u`, e o campo quase nunca vem vazio:
    vem com nome de marca, texto solto, "não sei". Tudo isso caía em
    `fora_do_bet_br` e inflava o número que sustenta a frase central do
    relatório. Medido: 0 contra 298 sem URL no mesmo recorte.
    """
    u = (url or "").strip().lower()
    if not re.match(r"^https?://", u):
        return "sem_url"
    if ".bet.br" in u:
        return "bet_br"
    return "fora_do_bet_br"

# ── trava 2: as duas janelas têm de ter o mesmo tamanho ─────────────────────
n_antes = sum(1 for r in linhas if fase(r["created_at"]) == "referencia")
n_depois = sum(1 for r in linhas if fase(r["created_at"]) == "depois")
if n_antes == 0 or n_depois == 0:
    sys.exit(f"🔴 janela vazia: antes={n_antes}, depois={n_depois}. Nada a publicar.")

SAIDA.mkdir(parents=True, exist_ok=True)

def escreve(nome, cabecalho, linhas_csv):
    with open(SAIDA / nome, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas_csv)
    print(f"  {nome}: {len(linhas_csv)} linhas")

# 1. por dia
# 🔴 O CALENDÁRIO É PREENCHIDO: dia sem denúncia sai com 0, não sai de fora.
#    A primeira versão montava o dicionário só a partir dos registros, e dia
#    zerado simplesmente não existia no CSV. Isso corrompe tudo que vem depois:
#    a mediana passa a ser sobre "dias com ao menos uma denúncia", `len(ref)`
#    deixa de ser o número de dias do período, e o relatório afirmaria uma base
#    de N dias que não é a que foi medida. E ESTE recorte TEM dia zerado —
#    18/09, dentro da anomalia. Ausência de denúncia é dado.
#    [[reference_coluna_sem_escritor_o_null_e_o_dado]]
por_dia = {}
for r in linhas:
    d = r["created_at"][:10]
    por_dia[d] = por_dia.get(d, 0) + 1

d0, d1 = datetime.date.fromisoformat(REF_INI), datetime.date.fromisoformat(DEPOIS_FIM)
calendario = []
while d0 < d1:
    iso = d0.isoformat()
    calendario.append([iso, fase(iso), por_dia.get(iso, 0)])
    d0 += datetime.timedelta(days=1)
zerados = [l[0] for l in calendario if l[2] == 0]
if zerados:
    print(f"  ⚠️ dias sem nenhuma denúncia (saem com 0, não omitidos): {zerados}")
escreve("denuncias_por_dia.csv", ["data", "fase", "denuncias"], calendario)

# 2. por categoria
# ⚠️ `problem_type` é multivalorado, separado por "; ". Contamos a CATEGORIA, não
#    a combinação — somar as categorias dá mais que o total de denúncias, e o
#    texto tem de dizer isso.
por_cat = {}
for r in linhas:
    f = fase(r["created_at"])
    for c in [x.strip() for x in (r["problem_type"] or "").split(";") if x.strip()]:
        por_cat.setdefault(c, {"referencia": 0, "anomalia": 0, "depois": 0})[f] += 1
escreve("denuncias_por_categoria.csv", ["categoria", "referencia", "anomalia", "depois"],
        [[c, v["referencia"], v["anomalia"], v["depois"]] for c, v in
         sorted(por_cat.items(), key=lambda kv: -kv[1]["depois"])])

# 3. por tipo de domínio
por_dom = {}
for r in linhas:
    k = (dominio(r.get("platform_url")), fase(r["created_at"]))
    por_dom[k] = por_dom.get(k, 0) + 1
escreve("denuncias_por_dominio.csv", ["dominio", "referencia", "anomalia", "depois"],
        [[d, por_dom.get((d, "referencia"), 0), por_dom.get((d, "anomalia"), 0), por_dom.get((d, "depois"), 0)]
         for d in ("fora_do_bet_br", "sem_url", "bet_br")])

# 4. procedência do congelado
(SAIDA / "COMO_FOI_MEDIDO.md").write_text(
    f"""# Congelado do relatório — MP 1.394

| campo | valor |
|---|---|
| tabela | `complaints` |
| vigência da MP (dia 0) | {MP_VIGENCIA} |
| janela ANTES | {ANTES_INI} a {ANTES_FIM} ({DIAS} dias) |
| janela DEPOIS | {DEPOIS_INI} a {DEPOIS_FIM} ({DIAS} dias) |
| denúncias antes | {n_antes} |
| denúncias depois | {n_depois} |
| congelado em | {datetime.date.today().isoformat()} |

🔴 As duas janelas têm **o mesmo número de dias**, de propósito. Medir só o
depois faz qualquer coisa parecer novidade: a denúncia contra casa não
autorizada já era a esmagadora maioria antes da MP, e só a comparação por dia
mostra isso.

🔴 **Nenhuma linha individual foi exportada.** Sem `description`, sem e-mail,
sem protocolo. Só contagem por dia, categoria e tipo de domínio.

⚠️ `problem_type` é multivalorado: a soma das categorias é maior que o total de
denúncias. O relatório diz isso onde usa a quebra.
""",
    encoding="utf-8",
)
print(f"\n  janela antes:  {ANTES_INI} → {ANTES_FIM}  ({n_antes} denúncias)")
print(f"  janela depois: {DEPOIS_INI} → {DEPOIS_FIM}  ({n_depois} denúncias)")
print(f"  congelado em {SAIDA.relative_to(RAIZ)}")
