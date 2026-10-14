# Relatório "Os primeiros dias da proibição" — edição 01

Rota `/relatorios/proibicao-apostas` · locale `relatorios.proibicao` · dados
`src/data/proibicao-apostas-ed01.json` · PDF e card em `public/`.

```bash
scripts/relatorio-mp1394/gerar.sh                      # tudo, na ordem
CORTE=2026-10-06 scripts/relatorio-mp1394/gerar.sh     # ensaio com recorte menor

rm -rf /tmp/kit && scripts/relatorio-mp1394/monta-kit-publico.sh /tmp/kit
KIT_TESTE=1 scripts/relatorio-mp1394/monta-kit-publico.sh /tmp/kit   # ensaio
```

⚠️ **Rodar os passos à mão esquece o `aplica_textos.py`**, e a página fica com a
prosa velha e os números novos. Use o `gerar.sh`.

---

## 🔴 Leia antes de mexer

### A prosa NÃO mora no JSON de `src/data/`

São três lugares, com papéis diferentes:

| onde | o quê | quem lê |
|---|---|---|
| `src/locales/{pt-BR,en-US,es}.json` → `relatorios.proibicao.*` | a **prosa**, com `{{placeholders}}` | a página React **e o prerender** |
| `scripts/relatorio-mp1394/textos/<idioma>.json` | a **mesma prosa**, revisada lado a lado | a fonte; `aplica_textos.py` a leva ao locale |
| `src/data/proibicao-apostas-ed01.json` → `textos[idioma]` | **só os números**, já formatados por idioma | injetados como variáveis em `t()` |

Revisão editorial acontece em `textos/`. O locale recebe o bloco pronto.

### Nenhum número é digitado, e há trava nos dois lados

O `g()` do prerender **remove placeholder desconhecido em silêncio**: uma frase
iria para o Google sem o número, sem erro de build. Por isso:

- `dados.py` recusa gerar se o texto usa placeholder que ele não produz;
- `aplica_textos.py` recusa aplicar sem paridade de chave, de lista e de
  placeholder nos três idiomas, e confere de novo contra o gerador.
- `aplica_textos.py` também lê o corpo da rota em `prerender-plugin.ts`, junta as
  54 chaves que ele chama e recusa aplicar se alguma não existir — **`g()`
  devolve string VAZIA para chave inexistente**, sem lançar e sem avisar.

Formatação de **número e de data** sai do gerador, nunca da página: separador de
milhar, nome de mês e as palavras "bi" e "milhões" mudam por idioma.

### A prosa que escreve número por extenso é conferida

"cinco dias antes", "quatro dias depois", "no dia seguinte" derivam de
constantes, não de dado que anda — mas palavra errada não quebra build. `dados.py`
confere os três intervalos e para se algum mudar.

---

## Os arquivos

| arquivo | o que faz |
|---|---|
| `congela.py` | denúncias → CSV agregado. **Só agregado**: nenhuma descrição, nenhum e-mail, nenhuma linha individual. |
| `congela-lai.py` | acervo `regulatory_*` → CSV. Safra por grão, mês em consolidação fora dos totais. |
| `dados.py` | lê os dois congelados → `src/data/proibicao-apostas-ed01.json` |
| `aplica_textos.py` | `textos/` → os três locales, exigindo paridade |
| `gera-og.py` | card social 1200×630 (pt-BR) |
| `gera-pdf.py` | PDF A4, espelhando as seções da página. **O idioma é argumento.** |
| `gerar.sh` | orquestra os cinco, e imprime o card e os três PDFs com o Chrome |
| `monta-kit-publico.sh` | kit público por allowlist, com três travas |

`formato.py` vem de `scripts/relatorio-bloqueio/` — **importado, não copiado**.
Duplicá-lo garantiria divergência na primeira correção.

---

### ⚠️ Trava que não acha nada reporta SUCESSO

A trava acima ancorava só no `canonical` da rota — texto que aparece **antes** em
`ITENS_HUB`. Pegava a entrada errada, achava **zero** chaves e imprimia "todas
existem". Conjunto vazio passa em qualquer `for`.

Por isso ela tem um piso: menos de dez chaves encontradas e o script para. Vale
para qualquer trava deste pipeline que dependa de **achar** alguma coisa — e
todas têm de ser testadas **disparando**, não só passando.

---

## O kit público

`monta-kit-publico.sh` monta por **allowlist** — nada entra por curinga, e
arquivo novo no congelado não vaza por acidente. Leva as contagens agregadas, as
séries de LAI, o texto dos pedidos com `sha256`, os scripts e o JSON.

🔴 **Nenhuma linha individual de denúncia**, e os PDFs anexados pela Receita não
são redistribuídos: são do órgão, já públicos na BuscaLAI, e o kit aponta para a
fonte em vez de hospedar uma cópia que pode divergir.

Três travas, **as três testadas disparando**:

1. o congelado tem de cobrir os 14 dias que o relatório promete — um kit com
   números de ensaio contradiria a página;
2. os números são **recalculados dentro do kit** e têm de bater com o JSON
   publicado, porque um kit que não reproduz o que promete prova o contrário;
3. varredura de dado pessoal e credencial, falha fechada.

A linha "Como citar" só mostra o kit quando `reportKit()` devolve não-nulo. O
slug fica **fora** de `KIT` em `report-pdfs.ts` até o repositório existir: link
morto é pior que silêncio.

---

## 🔴 As armadilhas que custaram medição

### O dia com zero não existia

`congela.py` montava o agregado por dia a partir dos registros, e 18/09 — que
teve zero denúncias — não tinha linha: **95 linhas para 96 dias**. A mediana
virava "mediana dos dias em que houve denúncia" e `len(ref)` deixava de ser o
número de dias do período. Hoje o calendário é preenchido com 0, e `dados.py`
confere a contagem contra o calendário **nas três fases**.

### A comparação simétrica infla por quase 3

Os dias imediatamente anteriores à MP estão contaminados: o acesso ao formulário
caiu naquela janela e um dia ficou sem nenhuma denúncia. A conta óbvia dá ~12×
contra 4,5× do período estável. A janela é **desenhada no gráfico, em cinza** —
não apagada: o leitor tem de ver por que foi excluída.

### Mês em consolidação puxa o total para baixo

`consolidado = false` é dado **parcial**. Em 05/10/2026 ago/2026 trazia R$ 7,0 bi
contra ~R$ 13 bi dos meses fechados. Somá-lo faria o relatório **subestimar** o
mercado que foi proibido, sem erro nenhum. O filtro é `is not False`, nunca
`is True`: linha antiga sem a coluna não pode sumir.

### `cpfs_unicos` é MENSAL e não se soma

São os CPFs únicos **naquele mês**. Somar 18 meses conta a mesma pessoa 18 vezes;
dividir um total de 18 meses por ele produz um "por pessoa" que não significa
nada. Só média e pico, e o texto diz "por mês".

### As janelas não são a mesma

O fluxo tem 18 meses fechados, o GGR tem a sua contagem, a arrecadação tem outra.
Texto que compara dois blocos cita as duas janelas.

---

### Dois defeitos que só existiam fora do português

Os dois passavam despercebidos no idioma que todo mundo olha.

- **A capa quebrava o título no primeiro ponto.** Em inglês o título começa com
  "1.18%", e o primeiro ponto é o separador DECIMAL: a capa saía com "1." numa
  linha e "18% went to health" na outra. A quebra agora é em `". "`, com trava se
  o título deixar de ter duas frases.
- **Duas réguas formatavam número com `replace(".", ",")`**, a vírgula do
  português, escrita quando o gerador só rodava em pt-BR.

E o endereço do PDF saía **sem o prefixo de idioma** — caminho que não existe no
`dist`. Como a SPA devolve 200 para qualquer rota, o erro não apareceria: daria
uma página que não é a canônica. Hoje sai de `route-slugs.ts`, com o prefixo.

---

## O que o relatório recusa publicar, de propósito

- **A razão não autorizado:autorizado.** Salta de 32 para 67 entre as janelas,
  mas os denominadores são 16 e 4 denúncias: uma a menos muda tudo. Fica no JSON
  para auditoria, fora da copy, com o motivo no código.
- **"Não existe estudo sobre proibir."** O que a Receita afirma é mais estreito —
  é o alcance do CETAD, não negativa de existência no governo —, e a ressalva
  fecha a seção.
- **A autoexclusão.** A tabela mistura grandezas (contas, CPFs, impedimentos), há
  linha com procedência não confirmada e quatro sem protocolo. Número que não se
  sabe somar não entra.

## Os números de bloqueio não são remedidos aqui

Vêm do JSON da ed02 do relatório de bloqueio. Remedir produziria um segundo
número para o mesmo fato, e os dois relatórios do site divergiriam sobre quanto
a Vivo bloqueia.

## A pergunta da LAI está em custódia

A seção da Receita afirma **o que nós perguntamos**. A custódia no R2 guarda os
anexos do órgão pelo portão do § 5º-A (`idTipoAnexo 2`) e **não o corpo do
pedido** — por isso o texto literal dos dois pedidos, a resposta verbatim e o
`sha256` de cada um estão em
`docs/custodia/2026-10-05-pedidos-lai-receita-cetad.json`, com o procedimento
para recuperá-los.
