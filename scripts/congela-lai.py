#!/usr/bin/env python3
# @vertical denuncia
"""
Congela, em CSV versionado, o recorte do acervo de LAI que mede O QUE FOI
PROIBIDO — a escala do mercado de quota fixa antes da MP 1.394.

🔴 POR QUE UM SEGUNDO CONGELADOR, e não uma consulta na hora da geração: o
mesmo motivo de `congela.py`. As tabelas `regulatory_*` recebem safra nova a
cada resposta de LAI, e um relatório que consulta o banco na geração muda de
número entre o PDF, o card e a landing. O CSV é o artefato que prova o que foi
publicado.

─── AS QUATRO REGRAS QUE ESTE ARQUIVO EXISTE PARA SEGURAR ──────────────────

🔴 1. SAFRA POR GRÃO. Cada resposta de LAI reescreve meses antigos. A leitura
   fica com a linha de `captured_at` MAIS RECENTE de cada grão — nunca a soma
   de todas, que contaria o mesmo mês várias vezes.

🔴 2. MÊS EM CONSOLIDAÇÃO NÃO ENTRA EM TOTAL. `consolidado = false` é dado
   PARCIAL. Em 05/10/2026 ago/2026 trazia R$ 7,0 bi contra ~R$ 13 bi dos meses
   fechados: somá-lo ao total o PUXA PARA BAIXO e o relatório subestimaria o
   mercado que foi proibido, sem erro nenhum. O filtro é `is not False`, não
   `is True`: linha antiga sem a coluna não pode sumir.

🔴 3. `cpfs_unicos` É MENSAL, E NÃO SE SOMA. São os CPFs únicos NAQUELE mês.
   Somar 20 meses conta a mesma pessoa 20 vezes; dividir um total de 20 meses
   por ele produz um "por pessoa" que não significa nada. Só média e pico, e o
   texto tem de dizer "por mês".

🔴 4. AS JANELAS NÃO SÃO A MESMA. O GGR tem menos meses consolidados que
   aportes e retiradas. Cada bloco carrega a sua própria contagem de meses, e
   quem escrever texto comparando dois blocos tem de citar as duas janelas.

Precisa de SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY em .env.local.
Uso: python3 scripts/relatorio-mp1394/congela-lai.py
"""
import csv
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[2]
SAIDA = RAIZ / ".lovable/research/mp1394-2026-10/datasets"

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


def consulta(tabela):
    # ⚠️ PostgREST corta em 1.000 linhas SEM erro. Paginamos sempre.
    todas, passo, inicio = [], 1000, 0
    while True:
        url = BASE + tabela + "?" + urllib.parse.urlencode({"select": "*", "limit": passo, "offset": inicio})
        lote = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=CAB), timeout=120).read())
        todas.extend(lote)
        if len(lote) < passo:
            return todas
        inicio += passo


def safra(linhas, grao):
    """🔴 Regra 1: por grão, fica a linha de `captured_at` mais recente."""
    melhor = {}
    for r in linhas:
        k = tuple(r[c] for c in grao)
        if k not in melhor or r["captured_at"] > melhor[k]["captured_at"]:
            melhor[k] = r
    return list(melhor.values())


def fechados(linhas):
    """🔴 Regra 2: mês em consolidação fica FORA de total."""
    return [r for r in linhas if r.get("consolidado") is not False]


def mes(r, campo="ano_mes"):
    return r[campo][:7]


# ── leitura ─────────────────────────────────────────────────────────────────
ap_todos = safra(consulta("regulatory_aportes_mensal"), ("ano_mes",))
ret_todos = safra(consulta("regulatory_retiradas_mensal"), ("ano_mes",))
ggr_todos = safra(consulta("regulatory_ggr_mensal"), ("ano_mes", "modalidade"))
arr = safra(consulta("regulatory_arrecadacao_mensal"), ("ref_mes", "codigo_tributo"))
urls = safra(consulta("regulatory_urls_bloqueadas_mensal"), ("ref_mes",))

ap, ret, ggr = fechados(ap_todos), fechados(ret_todos), fechados(ggr_todos)
parciais = sorted({mes(r) for r in ap_todos + ret_todos + ggr_todos
                   if r.get("consolidado") is False})
if parciais:
    print(f"  ⚠️ fora dos totais, em consolidação: {', '.join(parciais)}")

# ── trava: as duas séries do fluxo têm de cobrir os MESMOS meses ───────────
# 🔴 O líquido é `aportes - retiradas`. Se uma série tiver um mês que a outra não
#    tem, o líquido some um mês de entrada sem a saída correspondente e infla.
meses_ap, meses_ret = {mes(r) for r in ap}, {mes(r) for r in ret}
if meses_ap != meses_ret:
    sys.exit(
        f"🔴 aportes e retiradas cobrem meses diferentes.\n"
        f"   só em aportes: {sorted(meses_ap - meses_ret)}\n"
        f"   só em retiradas: {sorted(meses_ret - meses_ap)}\n"
        "   O líquido sairia errado."
    )
if not meses_ap:
    sys.exit("🔴 nenhum mês consolidado de aportes. Nada a publicar.")

SAIDA.mkdir(parents=True, exist_ok=True)


def escreve(nome, cabecalho, linhas_csv):
    with open(SAIDA / nome, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas_csv)
    print(f"  {nome}: {len(linhas_csv)} linhas")


# 1. fluxo mensal: aporte, retirada e pessoas
por_mes = {mes(r): {"aportado": float(r["vl_aportado"] or 0),
                    "cpfs": int(r["cpfs_unicos"] or 0)} for r in ap}
for r in ret:
    por_mes[mes(r)]["retirado"] = float(r["vl_retirado"] or 0)
escreve("lai_fluxo_mensal.csv", ["mes", "aportado", "retirado", "liquido", "cpfs_unicos"],
        [[m, f"{v['aportado']:.2f}", f"{v['retirado']:.2f}",
          f"{v['aportado'] - v['retirado']:.2f}", v["cpfs"]]
         for m, v in sorted(por_mes.items())])

# 2. GGR mensal — janela PRÓPRIA, menor que a do fluxo
ggr_mes = {}
for r in ggr:
    ggr_mes[mes(r)] = ggr_mes.get(mes(r), 0.0) + float(r["vl_ggr"] or 0)
escreve("lai_ggr_mensal.csv", ["mes", "ggr"],
        [[m, f"{v:.2f}"] for m, v in sorted(ggr_mes.items())])

# 3. arrecadação por grupo de tributo
# ⚠️ A nota da própria resposta diz que NENHUMA linha é rotulada como a
#    contribuição sobre GGR. Isto é "tributo federal ligado ao setor", não
#    "o que o setor pagou de outorga". O texto tem de dizer isso.
por_trib = {}
for r in arr:
    k = (r["codigo_tributo"], r["tributo"])
    por_trib[k] = por_trib.get(k, 0.0) + float(r["vl_arrecadado"] or 0)
escreve("lai_arrecadacao_tributo.csv", ["codigo", "tributo", "total"],
        [[c, t, f"{v:.2f}"] for (c, t), v in sorted(por_trib.items(), key=lambda kv: -kv[1])])

# 4. URLs bloqueadas por mês
escreve("lai_urls_bloqueadas.csv", ["mes", "urls"],
        [[mes(r, "ref_mes"), int(r["urls"] or 0)] for r in sorted(urls, key=lambda r: r["ref_mes"])])

# 5. procedência do congelado
fontes = sorted({r.get("fonte", "") for r in ap + ret + ggr + arr + urls if r.get("fonte")})
(SAIDA / "COMO_FOI_MEDIDO_LAI.md").write_text(
    "# Congelado do acervo de LAI — escala do mercado proibido\n\n"
    "| bloco | meses | janela |\n|---|---|---|\n"
    f"| fluxo (aportes, retiradas, pessoas) | {len(por_mes)} | {min(por_mes)} a {max(por_mes)} |\n"
    f"| GGR | {len(ggr_mes)} | {min(ggr_mes)} a {max(ggr_mes)} |\n"
    f"| arrecadação | {len({r['ref_mes'][:7] for r in arr})} | "
    f"{min(r['ref_mes'][:7] for r in arr)} a {max(r['ref_mes'][:7] for r in arr)} |\n"
    f"| URLs bloqueadas | {len(urls)} | {min(r['ref_mes'][:7] for r in urls)} a "
    f"{max(r['ref_mes'][:7] for r in urls)} |\n\n"
    "🔴 **Safra por grão:** cada resposta de LAI reescreve meses antigos; fica a\n"
    "linha de `captured_at` mais recente de cada mês.\n\n"
    "🔴 **Mês em consolidação fica FORA dos totais** — dado parcial puxa o total\n"
    f"para baixo sem erro nenhum. Excluídos: {', '.join(parciais) if parciais else 'nenhum'}.\n\n"
    "🔴 **`cpfs_unicos` é MENSAL e não se soma:** são os CPFs únicos naquele mês.\n"
    "Somar os meses conta a mesma pessoa várias vezes. Só média e pico.\n\n"
    "🔴 **As janelas não são a mesma.** O GGR tem menos meses consolidados que o\n"
    "fluxo; comparar os dois totais exige citar as duas janelas.\n\n"
    "## Fontes\n\n" + "".join(f"- {f}\n" for f in fontes),
    encoding="utf-8",
)

tot_ap = sum(v["aportado"] for v in por_mes.values())
tot_ret = sum(v["retirado"] for v in por_mes.values())
cpfs = [v["cpfs"] for v in por_mes.values() if v["cpfs"]]
print(f"\n  fluxo:      {len(por_mes)} meses · aportes R$ {tot_ap/1e9:.2f} bi · "
      f"retiradas R$ {tot_ret/1e9:.2f} bi · líquido R$ {(tot_ap-tot_ret)/1e9:.2f} bi")
print(f"  pessoas:    média {sum(cpfs)/len(cpfs):,.0f}/mês · pico {max(cpfs):,}".replace(",", "."))
print(f"  GGR:        {len(ggr_mes)} meses · R$ {sum(ggr_mes.values())/1e9:.2f} bi")
print(f"  tributos:   R$ {sum(por_trib.values())/1e9:.2f} bi")
print(f"  URLs:       {sum(int(r['urls'] or 0) for r in urls):,} em {len(urls)} meses".replace(",", "."))
print(f"  congelado em {SAIDA.relative_to(RAIZ)}")
