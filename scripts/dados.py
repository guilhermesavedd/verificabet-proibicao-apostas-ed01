#!/usr/bin/env python3
# @vertical denuncia
"""
Números do relatório "Os primeiros 14 dias da proibição"
→ `src/data/proibicao-apostas-ed01.json`.

🔴 Nenhum número é digitado na página, no prerender, no locale ou no card: todos
leem `textos[idioma]` daqui, já formatados. Percentual escrito à mão sobrevive a
qualquer correção de dado e sai publicado errado sem que nada falhe.

De onde vem cada número:
  · Denúncias: CSVs congelados por `congela.py` em
    `.lovable/research/mp1394-2026-10/datasets/`. Agregados, sem linha individual.
  · Receita Federal: DECLARADO — são fatos de um documento, não contagem nossa.
    Nota SIC CETAD/COEST nº 186 e 187, de 29/09/2026, em custódia.

⚠️ Chaves com prefixo `mp`, como `blk` no relatório de bloqueio: o prerender
funde os números de todos os estudos num único saco de variáveis.

🔴 A RAZÃO NÃO USA A JANELA SIMÉTRICA. Ver o cabeçalho de `congela.py`: os 14
dias antes da MP estão contaminados por uma queda de tráfego (17–24/09), e
compará-los daria ~12× contra ~4,5× do período estável. A referência é a
MEDIANA diária de 01/07 a 16/09 — mediana, não média, porque a série tem picos
de notícia e a média os carrega.

Uso: python3 scripts/relatorio-mp1394/dados.py
"""
import csv
import datetime
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "relatorio-bloqueio"))
# ⚠️ Importado, não copiado. `formato.py` já resolve separador e mês por idioma,
#    e duplicá-lo garantiria divergência na primeira correção. Ele está etiquetado
#    na vertical `bloqueio`; o mapa mostra este uso em "também aparece em".
from formato import (  # noqa: E402
    IDIOMAS, bilhoes, data_curta, data_longa, inteiro, intervalo, mes_curto,
    mes_longo, milhoes, num, pct,
)

RAIZ = pathlib.Path(__file__).resolve().parents[2]
DADOS = RAIZ / ".lovable/research/mp1394-2026-10/datasets"
SAIDA = RAIZ / "src/data/proibicao-apostas-ed01.json"

MP_VIGENCIA = "2026-09-25"

# ── DECLARADO: fatos de documento, não contagem nossa ───────────────────────
# Cada um com o protocolo que o sustenta, em custódia no R2.
DECLARADO = {
    "nota_data": "2026-09-29",       # Nota SIC CETAD/COEST 186 e 187
    "nota_protocolos": ["18800.146056/2026-05", "18800.145988/2026-22"],
    # 🔴 Os dois pedidos foram protocolados CINCO DIAS ANTES da MP 1.394. Não é
    #    detalhe: muda o que a seção pode afirmar. Perguntamos antes de a
    #    proibição existir, não depois dela.
    "pedido_data": "2026-09-20",
    # O texto LITERAL dos dois pedidos e das duas respostas está em
    # docs/custodia/2026-10-05-pedidos-lai-receita-cetad.json, com sha256 e o id
    # de manifestação de cada um. A seção afirma o que NÓS perguntamos, e sem
    # esse arquivo a afirmação era paráfrase. [[feedback_anexo_de_lai_le_a_pergunta]]
    "pedido_urls": {
        "18800.146056/2026-05": "https://buscalai.cgu.gov.br/busca/11683587",
        "18800.145988/2026-22": "https://buscalai.cgu.gov.br/busca/11682759",
    },
    # 🥇 A encomenda de estimativa fiscal ao Cetad existe e é RÁPIDA, e isso sai
    #    da própria Nota 023: "o pedido da presente complementação teve origem em
    #    reunião realizada pela Secretaria Executiva do Ministério da Fazenda, às
    #    17h30 de 5 de março de 2026" — e a nota é datada de 6 de março. Menos de
    #    24 horas. É o que faz a ausência significar algo.
    "nota_023_reuniao": "2026-03-05",
    # 🔴 Data de publicação, em UM lugar só. Ela aparece na capa do PDF, no
    #    rodapé do card e no `datePublished` do JSON-LD da página — três cópias
    #    que derivariam. Tem de bater com o fim da janela: `congela.py` recusa
    #    rodar antes, porque é quando os 14 dias fecham.
    "publicacao": "2026-10-14",
    "notas_citadas": ["009/2026", "023/2026"],
    "nota_009_data": "2026-01-22",
    "nota_023_data": "2026-03-06",
    # 🔴 O "0" do quarto número grande. É DERIVADO, não medido por nós: a
    #    resposta do CETAD afirma que as notas 009 e 023 são os ÚNICOS
    #    documentos que produziu sobre o assunto, e nenhuma das duas avalia
    #    restrição ou proibição — ambas tratam do AUMENTO da arrecadação.
    #    Fica aqui, e não digitado no texto, para que o número e o protocolo
    #    que o sustenta morem no mesmo lugar. A ressalva de alcance (é o que o
    #    CETAD conhece, não negativa de existência no governo) está na copy e
    #    em `ressalvas`. [[feedback_public_claims_irregular_vs_golpe]]
    "estudos_sobre_proibir": 0,
}


def le_csv(nome):
    with open(DADOS / nome, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── trava 1: o congelado tem de existir ─────────────────────────────────────
if not DADOS.exists():
    sys.exit(
        f"🔴 {DADOS.relative_to(RAIZ)} não existe.\n"
        "   Rode antes: python3 scripts/relatorio-mp1394/congela.py"
    )

por_dia = le_csv("denuncias_por_dia.csv")
por_dom = le_csv("denuncias_por_dominio.csv")

# ── a escala do que foi proibido, do acervo de LAI ─────────────────────────
# 🔴 Congelado por `congela-lai.py`, que já aplicou safra por grão e tirou os
#    meses em consolidação. Aqui NÃO se refaz essa conta — se faltar o arquivo,
#    para, em vez de publicar o relatório sem a seção que o título promete.
for _arq in ("lai_fluxo_mensal.csv", "lai_ggr_mensal.csv",
             "lai_arrecadacao_tributo.csv", "lai_urls_bloqueadas.csv"):
    if not (DADOS / _arq).exists():
        sys.exit(
            f"🔴 falta {_arq} no congelado.\n"
            "   Rode antes: python3 scripts/relatorio-mp1394/congela-lai.py"
        )

fluxo = le_csv("lai_fluxo_mensal.csv")
ggr_mensal = le_csv("lai_ggr_mensal.csv")
tributos = le_csv("lai_arrecadacao_tributo.csv")
urls_mensal = le_csv("lai_urls_bloqueadas.csv")

lai_meses = [r["mes"] for r in fluxo]
tot_aportes = sum(float(r["aportado"]) for r in fluxo)
tot_retiradas = sum(float(r["retirado"]) for r in fluxo)
tot_liquido = tot_aportes - tot_retiradas
tot_ggr = sum(float(r["ggr"]) for r in ggr_mensal)
tot_tributos = sum(float(r["total"]) for r in tributos)
tot_urls = sum(int(r["urls"]) for r in urls_mensal)

# 🔴 `cpfs_unicos` É MENSAL. Média e pico, nunca soma — somar 20 meses conta a
#    mesma pessoa 20 vezes. E nada de dividir um total de 18 meses por ele.
cpfs = [(r["mes"], int(r["cpfs_unicos"])) for r in fluxo if int(r["cpfs_unicos"]) > 0]
if not cpfs:
    sys.exit("🔴 nenhum mês com cpfs_unicos no congelado de LAI.")
cpfs_media = sum(v for _, v in cpfs) / len(cpfs)
cpfs_pico_mes, cpfs_pico = max(cpfs, key=lambda kv: kv[1])

# A contribuição da Lei 14.790, separável desde a safra de 22/09.
L14790 = next((float(r["total"]) for r in tributos if r["codigo"] == "L14790"), None)
if L14790 is None:
    sys.exit("🔴 a linha L14790 sumiu do congelado de arrecadação; o texto a cita.")

# ── a queda que já acontecia ANTES da MP ───────────────────────────────────
# 🥇 Achado: o mercado encolhia antes de ser proibido. A janela é o ano corrente
#    até o último mês FECHADO — jan a jun/2026 em 05/10. Não é escolha
#    editorial: é "o que o ano de 2026 mostra com dado consolidado".
ano = max(lai_meses)[:4]
queda = [r for r in fluxo if r["mes"].startswith(ano)]
if len(queda) < 3:
    sys.exit(f"🔴 só {len(queda)} meses fechados em {ano}; poucos para falar em tendência.")
q_ini, q_fim = queda[0], queda[-1]
q_ap_pct = 100.0 * (1 - float(q_fim["aportado"]) / float(q_ini["aportado"]))
q_cp_pct = 100.0 * (1 - int(q_fim["cpfs_unicos"]) / int(q_ini["cpfs_unicos"]))

# ── o instrumento: números do relatório de bloqueio, NÃO remedidos ─────────
# 🔴 Lidos do JSON da ed02, que é o artefato publicado. Remedir aqui produziria
#    um segundo número para o mesmo fato, e os dois relatórios do site
#    divergiriam sobre quanto a Vivo bloqueia. [[project_radar_public_single_source]]
BLOQ = json.loads((RAIZ / "src/data/bloqueio-apostas-ed02.json").read_text(encoding="utf-8"))["textos"]

# ── para onde foi o dinheiro: números do relatório de ARRECADAÇÃO ──────────
# 🔴 Mesma regra do bloqueio: lidos do artefato publicado, NÃO remedidos. A
#    repartição tem janela PRÓPRIA (6 meses do 1º semestre de 2026) e base
#    própria — é percentual do que foi REPARTIDO naquele semestre, não dos
#    tributos de 18 meses desta página. Juntar os dois numa frase faria o leitor
#    ler "1,18% de R$ 28 bi", que é falso por uma ordem de grandeza.
_arr = json.loads((RAIZ / "src/data/arrecadacao-apostas-ed01.json").read_text(encoding="utf-8"))
ARR = _arr["textos"]
_ABREV = {"jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
          "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"}


def _mes_iso(rotulo):
    """'jan/2026' → '2026-01'. A janela sai do metadado do PRÓPRIO gerador de
    arrecadação, para não existir uma segunda cópia dela aqui."""
    abrev, _, ano = rotulo.strip().partition("/")
    if abrev[:3].lower() not in _ABREV or not ano.isdigit():
        sys.exit(f"🔴 não consegui ler a janela da arrecadação em {rotulo!r}.")
    return f"{ano}-{_ABREV[abrev[:3].lower()]}"


# 🥇 A CONSTÂNCIA é o que torna o 1,18% publicável como desenho, e não como
#    acaso do semestre. O relatório de arrecadação já mede as três janelas — o
#    array se chama `constancia` — e as três dão a mesma fatia. Sem isso a
#    objeção óbvia ("escolheram o semestre que convinha") fica de pé.
_const = _arr.get("constancia") or []
if len(_const) != 3:
    sys.exit(f"🔴 `constancia` do relatório de arrecadação tem {len(_const)} linhas, esperava 3.")
_c2025, _csem, _cregime = _const
_fatia = lambda c: 100.0 * float(c["saude"]) / float(c["tot"])
# 🔴 O texto afirma que a fatia é a MESMA nas três janelas. Se uma safra nova
#    quebrar isso, a frase vira mentira sem erro nenhum — então o build para.
_fatias = [_fatia(c) for c in _const]
if max(_fatias) - min(_fatias) > 0.1:
    sys.exit(
        "🔴 a fatia da saúde deixou de ser constante entre as janelas: "
        + ", ".join(f"{f:.2f}%" for f in _fatias)
        + ".\n   O texto afirma que ela se repete. Reescreva antes de publicar."
    )

_periodo = _arr["_gerado"]["periodo"].split("-")
if len(_periodo) != 2:
    sys.exit(f"🔴 janela da arrecadação em formato inesperado: {_arr['_gerado']['periodo']!r}")
ARR_INI, ARR_FIM = (_mes_iso(x) for x in _periodo)

ref = [int(r["denuncias"]) for r in por_dia if r["fase"] == "referencia"]
dep = [int(r["denuncias"]) for r in por_dia if r["fase"] == "depois"]

# ── trava 2: amostra mínima para falar em razão ─────────────────────────────
# Sem isso, uma semana de referência curta produz multiplicador de qualquer
# tamanho. 30 dias é o piso para a mediana significar alguma coisa.
if len(ref) < 30:
    sys.exit(f"🔴 referência com {len(ref)} dias; o piso é 30. Não dá para publicar razão.")
if len(dep) < 1:
    sys.exit("🔴 janela pós-MP vazia.")

# ── trava 2b: o CSV tem de trazer o CALENDÁRIO, não só os dias com denúncia ──
# 🔴 `congela.py` preenche dia zerado com 0. Se um congelado antigo (ou uma
#    regressão) voltar a omitir esses dias, a mediana vira "mediana dos dias em
#    que houve denúncia" e `len(ref)` deixa de ser o número de dias do período —
#    e o relatório afirma uma base que não foi a medida. Confere contra o
#    calendário em vez de confiar na contagem de linhas.
def _cal(fase_alvo):
    d = sorted(r["data"] for r in por_dia if r["fase"] == fase_alvo)
    if not d:
        return 0
    return (datetime.date.fromisoformat(d[-1]) - datetime.date.fromisoformat(d[0])).days + 1

_por_fase = {}
for r in por_dia:
    _por_fase[r["fase"]] = _por_fase.get(r["fase"], 0) + 1
for f, n_linhas in sorted(_por_fase.items()):
    esperado = _cal(f)
    if n_linhas != esperado:
        sys.exit(
            f"🔴 fase '{f}': {n_linhas} linhas no CSV para {esperado} dias de calendário.\n"
            "   O congelado está omitindo dia sem denúncia. Rode congela.py de novo."
        )

ref_mediana = statistics.median(ref)
dep_media = statistics.mean(dep)
razao = dep_media / ref_mediana
pico = max(dep)
dia_pico = max((r for r in por_dia if r["fase"] == "depois"),
               key=lambda r: int(r["denuncias"]))["data"]
total_dep = sum(dep)

dom = {r["dominio"]: r for r in por_dom}
dep_fora = int(dom["fora_do_bet_br"]["depois"])
dep_sem = int(dom["sem_url"]["depois"])
dep_bet = int(dom["bet_br"]["depois"])
ref_fora = int(dom["fora_do_bet_br"]["referencia"])
ref_bet = int(dom["bet_br"]["referencia"])

# 🔴 O denominador é só quem TEM URL. Incluir "sem URL" no total faria a fatia
#    do não autorizado parecer menor por um motivo que não é sobre o mercado —
#    é sobre o formulário não exigir o campo.
com_url_dep = dep_fora + dep_bet
com_url_ref = ref_fora + ref_bet
if com_url_dep == 0 or com_url_ref == 0:
    sys.exit("🔴 nenhuma denúncia com URL em uma das janelas.")

pct_fora_dep = 100.0 * dep_fora / com_url_dep
pct_fora_ref = 100.0 * ref_fora / com_url_ref
# Razão não autorizado : autorizado, nas duas janelas.
# 🔴 GERADO E DELIBERADAMENTE NÃO PUBLICADO. Os denominadores são minúsculos —
#    16 denúncias contra casa autorizada na referência e 4 depois — e a razão
#    salta de 32 para 67 por conta de UMA denúncia a menos. Publicar isso como
#    "dobrou" seria um claim construído sobre ruído. A frase que o relatório usa
#    é a porcentagem sobre o total com endereço (97,0% → 98,5%), que tem base
#    de centenas. Mantido no JSON para quem quiser auditar, fora da copy de
#    propósito. [[feedback_limiar_de_alarme_sem_n]]
prop_dep = dep_fora / dep_bet if dep_bet else None
prop_ref = ref_fora / ref_bet if ref_bet else None

dias_dep = len(dep)

# ── a comparação INGÊNUA, publicada como contraste e não como achado ─────────
# 🔴 Este número existe para o relatório poder dizer "a conta óbvia daria X, e
#    está errada". Antes ele era digitado no texto como "cerca de 12 vezes".
#    Digitado, sobrevive a qualquer mudança de recorte: se a janela pós-MP
#    mudar de tamanho, a janela simétrica muda com ela e o 12 fica mentira sem
#    nada falhar. Medido aqui, acompanha.
serie = {r["data"]: int(r["denuncias"]) for r in por_dia}
mp_d = datetime.date.fromisoformat(MP_VIGENCIA)
simetrica = [serie[(mp_d - datetime.timedelta(days=k)).isoformat()]
             for k in range(1, dias_dep + 1)
             if (mp_d - datetime.timedelta(days=k)).isoformat() in serie]
if len(simetrica) != dias_dep:
    sys.exit(
        f"🔴 a janela simétrica tem {len(simetrica)} dos {dias_dep} dias no congelado.\n"
        "   Sem ela não dá para publicar o contraste com a conta ingênua."
    )
sim_media = statistics.mean(simetrica)
if sim_media == 0:
    sys.exit("🔴 janela simétrica com média zero.")
razao_ingenua = dep_media / sim_media

# ── a anomalia, medida e nomeada ────────────────────────────────────────────
# 🔴 Em vez de "caiu a um terço". Essa fração estava TROCADA de sujeito no
#    texto: um terço era a queda da DENÚNCIA; o acesso ao formulário caiu bem
#    mais. Publicamos as duas medianas e deixamos o leitor dividir.
anom = [(r["data"], int(r["denuncias"])) for r in por_dia if r["fase"] == "anomalia"]
if not anom:
    sys.exit("🔴 nenhuma linha na fase 'anomalia'; o congelado não bate com o texto.")
anom_mediana = statistics.median([v for _, v in anom])
zerados = [d for d, v in anom if v == 0]
# 🔴 O texto nomeia UM dia sem nenhuma denúncia. Se virarem dois, ou nenhum, a
#    frase deixa de descrever o dado — e a trava obriga a reescrevê-la.
if len(zerados) != 1:
    sys.exit(
        f"🔴 a fase 'anomalia' tem {len(zerados)} dia(s) sem denúncia: {zerados}.\n"
        "   O texto afirma exatamente um. Reescreva a frase antes de publicar."
    )

dias_ate_pico = (datetime.date.fromisoformat(dia_pico) - mp_d).days
# O congelado termina no último dia COM linha; o corte é o dia seguinte.
CORTE_DO_CONGELADO = (datetime.date.fromisoformat(por_dia[-1]["data"])
                      + datetime.timedelta(days=1)).isoformat()

# ── trava: "quatro dias" da Receita é prosa por extenso, e fica conferida ───
# 🔴 "quatro dias depois da MP" está escrito como PALAVRA nos três idiomas, de
#    propósito: é derivado de duas constantes (a data da resposta e a vigência),
#    não de dado que anda. Mas se qualquer uma mudar, a palavra fica errada em
#    silêncio — então o número é conferido aqui, e só a prosa fica no texto.
_gap = (datetime.date.fromisoformat(DECLARADO["nota_data"]) - mp_d).days
if _gap != 4:
    sys.exit(
        f"🔴 a resposta da Receita está {_gap} dias depois da vigência, não 4.\n"
        "   Os três textos dizem 'quatro dias' por extenso. Corrija a prosa."
    )
# 🔴 Mesma trava para o "cinco dias ANTES", que é a abertura da seção.
# 🔴 Publicar antes do fim da janela seria afirmar 14 dias contando dias que não
#    existem. A trava de `congela.py` olha o CORTE; esta olha o que a capa diz.
if datetime.date.fromisoformat(DECLARADO["publicacao"]) < datetime.date.fromisoformat(CORTE_DO_CONGELADO):
    sys.exit(
        f"🔴 a publicação está marcada para {DECLARADO['publicacao']}, antes do fim do "
        f"recorte congelado ({CORTE_DO_CONGELADO}). Capa e dados diriam coisas diferentes."
    )

# 🔴 O TÍTULO escreve "Zero" por extenso, porque "0 estudos" como manchete lê
#    como rótulo de gráfico. Palavra não quebra build: se o declarado deixar de
#    ser zero, o título fica mentindo em silêncio.
if DECLARADO["estudos_sobre_proibir"] != 0:
    sys.exit(
        f"🔴 estudos_sobre_proibir = {DECLARADO['estudos_sobre_proibir']}, não 0.\n"
        "   O título dos três idiomas diz 'Zero' por extenso. Corrija a manchete."
    )

_antes = (mp_d - datetime.date.fromisoformat(DECLARADO["pedido_data"])).days
if _antes != 5:
    sys.exit(
        f"🔴 os pedidos foram protocolados {_antes} dias antes da vigência, não 5.\n"
        "   Os três textos dizem 'cinco dias antes' por extenso. Corrija a prosa."
    )
# 🔴 E a nota 023 sai no dia seguinte à reunião que a encomendou. Se a distância
#    deixar de ser 1 dia, a frase "no dia seguinte" vira outra coisa.
_encomenda = (datetime.date.fromisoformat(DECLARADO["nota_023_data"])
              - datetime.date.fromisoformat(DECLARADO["nota_023_reuniao"])).days
if _encomenda != 1:
    sys.exit(
        f"🔴 a Nota 023 saiu {_encomenda} dias depois da reunião, não 1.\n"
        "   Os três textos dizem 'no dia seguinte'. Corrija a prosa."
    )

textos = {}
for i in IDIOMAS:
    textos[i] = {
        "mpDias": inteiro(dias_dep, i),
        "mpVigencia": data_longa(MP_VIGENCIA, i),
        "mpTotalDepois": inteiro(total_dep, i),
        "mpMediaDepois": num(dep_media, 1, i),
        "mpRefMediana": num(ref_mediana, 1, i),
        "mpRefDias": inteiro(len(ref), i),
        "mpRazao": num(razao, 1, i),
        "mpPico": inteiro(pico, i),
        "mpDiaPico": data_longa(dia_pico, i),
        "mpPctForaDepois": pct(pct_fora_dep, i),
        "mpPctForaRef": pct(pct_fora_ref, i),
        "mpPropDepois": num(prop_dep, 0, i) if prop_dep else None,
        "mpPropRef": num(prop_ref, 0, i) if prop_ref else None,
        "mpSemUrlDepois": inteiro(dep_sem, i),
        "mpComUrlDepois": inteiro(com_url_dep, i),
        "mpNotaData": data_longa(DECLARADO["nota_data"], i),
        "mpNota009Data": data_longa(DECLARADO["nota_009_data"], i),
        "mpNota023Data": data_longa(DECLARADO["nota_023_data"], i),
        "mpRazaoIngenua": num(razao_ingenua, 0, i),
        "mpAnomaliaIntervalo": intervalo(anom[0][0], anom[-1][0], i),
        "mpAnomaliaMediana": num(anom_mediana, 1, i),
        "mpDiaSemDenuncia": data_longa(zerados[0], i),
        "mpDiasAtePico": inteiro(dias_ate_pico, i),
        "mpEstudosProibir": inteiro(DECLARADO["estudos_sobre_proibir"], i),
        "mpPedidoData": data_longa(DECLARADO["pedido_data"], i),
        "mpProtocolo1": DECLARADO["nota_protocolos"][0],
        "mpProtocolo2": DECLARADO["nota_protocolos"][1],
        "mpNota023Reuniao": data_longa(DECLARADO["nota_023_reuniao"], i),
        # ⚠️ Rótulos do eixo do gráfico. Vêm DAQUI porque data também se
        #    formata por idioma: a página escrevia o ISO cru ("2026-07-01").
        "mpSerieIni": data_curta(por_dia[0]["data"], i),
        "mpSerieFim": data_curta(por_dia[-1]["data"], i),
        "mpPublicacao": data_longa(DECLARADO["publicacao"], i),
        # ── a escala do que foi proibido ──────────────────────────────────
        "mpLaiMeses": inteiro(len(lai_meses), i),
        "mpLaiIni": mes_longo(lai_meses[0], i),
        "mpLaiFim": mes_longo(lai_meses[-1], i),
        "mpAportes": bilhoes(tot_aportes, i),
        "mpRetiradas": bilhoes(tot_retiradas, i),
        "mpLiquido": bilhoes(tot_liquido, i),
        "mpGgr": bilhoes(tot_ggr, i),
        "mpGgrMeses": inteiro(len(ggr_mensal), i),
        "mpTributos": bilhoes(tot_tributos, i),
        "mpTributosMeses": inteiro(len({r["codigo"] for r in tributos}), i),
        "mpL14790": bilhoes(L14790, i),
        "mpCpfsMedia": milhoes(cpfs_media, i),
        "mpCpfsPico": milhoes(cpfs_pico, i),
        "mpCpfsPicoMes": mes_longo(cpfs_pico_mes, i),
        # ── a queda que já acontecia ──────────────────────────────────────
        "mpQuedaIni": mes_longo(q_ini["mes"], i),
        "mpQuedaFim": mes_longo(q_fim["mes"], i),
        "mpQuedaApIni": bilhoes(float(q_ini["aportado"]), i),
        "mpQuedaApFim": bilhoes(float(q_fim["aportado"]), i),
        "mpQuedaApPct": pct(q_ap_pct, i, 0),
        "mpQuedaCpIni": milhoes(int(q_ini["cpfs_unicos"]), i),
        "mpQuedaCpFim": milhoes(int(q_fim["cpfs_unicos"]), i),
        "mpQuedaCpPct": pct(q_cp_pct, i, 0),
        # ── o instrumento (relatório de bloqueio ed02, não remedido) ──────
        "mpUrls": inteiro(tot_urls, i),
        "mpUrlsMeses": inteiro(len(urls_mensal), i),
        "mpBloqVivo": BLOQ[i]["blkVivoPct"],
        "mpBloqClaro": BLOQ[i]["blkClaroPct"],
        "mpBloqDns": BLOQ[i]["blkDnsPct"],
        "mpBloqMedicao": BLOQ[i]["blkMedicaoMulti"],
        # ── para onde foi o dinheiro (relatório de arrecadação, não remedido) ─
        "mpArrIni": mes_longo(ARR_INI, i),
        "mpArrFim": mes_longo(ARR_FIM, i),
        "mpRepartido": ARR[i]["arrTotalRepartido"],
        "mpSaudePct": ARR[i]["arrSaudePct"],
        "mpSaude": ARR[i]["arrSaude"],
        "mpTurismo": ARR[i]["arrTurismo"],
        "mpTurismoX": ARR[i]["arrTurismoX"],
        "mpDru": ARR[i]["arrDru"],
        "mpSaudeCpf": ARR[i]["arrSaudeCpf"],
        "mpTurismoCpf": ARR[i]["arrTurismoCpf"],
        "mpSaudeAx": ARR[i]["arrSaudeAx"],
        "mpAxSaude": ARR[i]["arrAxSaude"],
        "mpSaudePct2025": pct(_fatia(_c2025), i, 2),
        "mpSaudePctRegime": pct(_fatia(_cregime), i, 2),
        # ⚠️ Valor abaixo de 1 bi: sai em milhões, com "R$" na frente — o acervo
        #    usa "R$" nos três idiomas, inclusive en-US.
        "mpSaudeRegime": "R$ " + milhoes(float(_cregime["saude"]), i, 1),
        "mpRepartidoRegime": bilhoes(float(_cregime["tot"]), i),
    }

# ── trava 3: nenhum texto pode sair com valor vazio ─────────────────────────
# O `g()` do prerender REMOVE placeholder desconhecido em silêncio: a frase iria
# para o Google sem o número e sem erro de build.
for i, t in textos.items():
    vazios = [k for k, v in t.items() if v is None or v == ""]
    if vazios:
        sys.exit(f"🔴 {i}: chave(s) sem valor → {vazios}. O prerender publicaria a frase sem o número.")

# ── trava 4: todo placeholder do texto tem de ter valor gerado ─────────────
# 🔴 A mais importante das quatro. O `g()` do prerender REMOVE placeholder
#    desconhecido em silêncio: `{{mpRazao}}` sem valor não quebra o build — sai
#    para o Google a frase "denúncias vezes mais", sem número e sem erro.
TEXTOS = RAIZ / "scripts/relatorio-mp1394/textos"
import re as _re

def _placeholders(o):
    if isinstance(o, str):
        return set(_re.findall(r"\{\{(\w+)\}\}", o))
    if isinstance(o, dict):
        return set().union(*(_placeholders(v) for v in o.values())) if o else set()
    if isinstance(o, list):
        return set().union(*(_placeholders(v) for v in o)) if o else set()
    return set()

for i in IDIOMAS:
    arq = TEXTOS / f"{i}.json"
    if not arq.exists():
        sys.exit(f"🔴 falta {arq.relative_to(RAIZ)}")
    usados = _placeholders(json.loads(arq.read_text(encoding="utf-8")))
    orfaos = sorted(usados - set(textos[i]))
    if orfaos:
        sys.exit(
            f"🔴 {i}: o texto usa placeholder que o gerador não produz → {orfaos}\n"
            "   O prerender removeria em silêncio e a frase sairia sem o número."
        )
    # ── o contrário é só aviso, mas o aviso MENTIA ─────────────────────────
    # 🔴 Nem todo número passa por texto do locale. Estes a página lê DIRETO de
    #    `textos[idioma]`, porque são rótulo de desenho (eixo do gráfico) ou
    #    número grande com unidade — não cabem numa frase. Sem esta lista o
    #    aviso os chamava de "não usados", e quem acreditasse apagaria o rótulo
    #    do eixo sem nada falhar.
    CONSUMIDOS_PELA_PAGINA = {"mpSerieIni", "mpSerieFim"}
    # 🔴 Gerados de propósito e NÃO publicados: a razão não autorizado:autorizado
    #    fica no JSON para auditoria, fora da copy, porque os denominadores são
    #    16 e 4 denúncias. [[feedback_limiar_de_alarme_sem_n]]
    AUDITORIA = {"mpPropDepois", "mpPropRef"}
    nao_usados = sorted(set(textos[i]) - usados - CONSUMIDOS_PELA_PAGINA - AUDITORIA)
    if nao_usados and i == IDIOMAS[0]:
        print(f"  ⚠️ gerados e não usados em lugar nenhum: {nao_usados}")

# ── trava 5: a fase é um conjunto fechado ──────────────────────────────────
# 🔴 O gráfico pinta por fase. Fase que o desenho não conhece sairia como coluna
#    sem cor — invisível, sem erro. A página NÃO pode falhar; aqui pode, então a
#    validação mora aqui. [[reference_enum_fechado_descarta_evento]]
FASES = ("referencia", "anomalia", "depois")
desconhecidas = sorted({r["fase"] for r in por_dia} - set(FASES))
if desconhecidas:
    sys.exit(f"🔴 fase desconhecida no congelado → {desconhecidas}. O gráfico não saberia pintar.")

saida = {
    "serie": [{"data": r["data"], "fase": r["fase"], "denuncias": int(r["denuncias"])}
              for r in por_dia],
    "dominio": [{"dominio": r["dominio"], "referencia": int(r["referencia"]),
                 "anomalia": int(r["anomalia"]), "depois": int(r["depois"])}
                for r in por_dom],
    # 🔴 O percentual da régua sai DAQUI, não da página. A página que divide é a
    #    página que publica número digitado: qualquer correção de dado deixaria a
    #    barra certa e o texto errado, ou o contrário. Denominador é só quem TEM
    #    endereço — o mesmo da copy.
    # 🔴 Número de DESENHO, não de texto: o gráfico precisa da mediana como
    #    float para posicionar a linha. A versão formatada por idioma é
    #    `mpRefMediana`, em `textos`. São usos diferentes do mesmo valor, e
    #    nenhum dos dois é digitado na página.
    # A página lê daqui em vez de ter a data escrita no componente.
    "publicadaEm": DECLARADO["publicacao"],
    "refMedianaDia": ref_mediana,
    # Série do fluxo para o gráfico da escala: valores de desenho, não de texto.
    "fluxo": [{"mes": r["mes"], "aportado": float(r["aportado"]),
               "retirado": float(r["retirado"]), "cpfs": int(r["cpfs_unicos"])}
              for r in fluxo],
    # 🔴 A régua da queda desenha APORTES EM BILHÕES, não percentual: o leitor
    #    tem de ver a altura cair. O rótulo de mês vem formatado por idioma —
    #    a página não formata data, pelo mesmo motivo que não formata número.
    "queda": [{"mes": r["mes"], "aportadoBi": round(float(r["aportado"]) / 1e9, 2)}
              for r in queda],
    "rotulosMes": {i: {r["mes"]: mes_curto(r["mes"], i) for r in queda} for i in IDIOMAS},
    "composicao": [
        {"k": "fora", "ref": round(pct_fora_ref, 1), "dep": round(pct_fora_dep, 1)},
        {"k": "bet_br", "ref": round(100.0 - pct_fora_ref, 1),
         "dep": round(100.0 - pct_fora_dep, 1)},
    ],
    "textos": textos,
    "_gerado": {
        "por": "scripts/relatorio-mp1394/dados.py",
        "congelado_em": str(DADOS.relative_to(RAIZ)),
        "mp_vigencia": MP_VIGENCIA,
        "dias_pos_mp": dias_dep,
        "referencia_dias": len(ref),
        "declarado": DECLARADO,
        "razao_ingenua": round(razao_ingenua, 2),
        "anomalia": {"de": anom[0][0], "a": anom[-1][0],
                     "mediana_dia": anom_mediana, "dias_sem_denuncia": zerados},
        "ressalvas": [
            f"A razão compara a média diária pós-MP ({dep_media:.1f}/dia) com a MEDIANA "
            f"diária do período estável de {len(ref)} dias ({ref_mediana:.1f}/dia). Os "
            f"{dias_dep} dias imediatamente anteriores à MP NÃO servem de baseline: de "
            f"{anom[0][0]} a {anom[-1][0]} a mediana caiu a {anom_mediana:.1f}/dia, e em "
            f"{zerados[0]} não houve nenhuma denúncia. Comparar com a janela simétrica "
            f"daria {razao_ingenua:.1f}x em vez de {razao:.1f}x.",
            f"{dep_sem} das {total_dep} denúncias pós-MP não trazem URL: o formulário "
            "não exige o campo. As porcentagens de domínio usam como denominador só "
            "quem tem URL.",
            "problem_type é multivalorado; a soma das categorias é maior que o total "
            "de denúncias.",
            f"A escala do mercado vem do acervo de LAI, congelado por congela-lai.py: "
            f"{len(lai_meses)} meses FECHADOS ({lai_meses[0]} a {lai_meses[-1]}). Mês em "
            "consolidação fica fora dos totais — dado parcial puxa o total para baixo sem "
            "erro nenhum. `cpfs_unicos` é MENSAL e não se soma: são os CPFs únicos naquele "
            "mês, e por isso o relatório publica média e pico, nunca um total de pessoas.",
            f"A arrecadação ({len({r['codigo'] for r in tributos})} grupos de tributo) é "
            "tributo federal LIGADO ao setor, não a outorga: a própria resposta da Receita "
            "diz que nenhuma linha é rotulada como a contribuição sobre GGR. A janela dela "
            "não é a mesma do fluxo.",
            f"Os números de repartição vêm do relatório de arrecadação (edição 01), janela "
            f"PRÓPRIA de {_arr['_gerado']['periodo']} e base própria: o percentual é do que "
            "foi REPARTIDO naquele semestre, não dos tributos federais de 18 meses desta "
            "página. As duas grandezas não se dividem uma pela outra.",
            "Os números de bloqueio por operadora vêm do relatório de bloqueio (edição 02), "
            "medidos na véspera da MP. NÃO foram remedidos aqui: dois números para o mesmo "
            "fato fariam os dois relatórios do site divergirem.",
            "Os fatos sobre a Receita Federal vêm de documento (Nota SIC CETAD/COEST "
            "186 e 187), não de contagem nossa. 'Desconhece outro órgão' é o alcance "
            "do CETAD, não negativa de existência no governo.",
            "O texto literal dos dois pedidos e das duas respostas está em "
            "docs/custodia/2026-10-05-pedidos-lai-receita-cetad.json, com sha256. As "
            "duas respostas são identicas, conferido. Dois itens dos pedidos ficaram "
            "sem resposta: se a Receita recebeu encomenda de estudo dessa natureza, e "
            "se existe documento interno atribuindo essa responsabilidade.",
        ],
    },
}

SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"  referência: {len(ref)} dias · mediana {ref_mediana:.1f}/dia")
print(f"  pós-MP:     {dias_dep} dias · média {dep_media:.1f}/dia · pico {pico} em {dia_pico}")
print(f"  razão:      {razao:.1f}x  (janela simétrica daria {razao_ingenua:.1f}x)")
print(f"  anomalia:   {anom[0][0]}→{anom[-1][0]} · mediana {anom_mediana:.1f}/dia · zero em {zerados[0]}")
print(f"  pico:       {dias_ate_pico} dias depois da vigência")
print(f"  com URL pós-MP: {com_url_dep} ({pct_fora_dep:.1f}% fora do .bet.br)")
print(f"  referência:     {com_url_ref} ({pct_fora_ref:.1f}% fora do .bet.br)")
print(f"  → {SAIDA.relative_to(RAIZ)}")
