# Kit de reprodução — "1,18% foi para a saúde. Zero estudos sobre o custo de proibir."

Dados, scripts e procedência de cada número do relatório do VerificaBet sobre os
primeiros dias da proibição das apostas de quota fixa (MP 1.394, de 25/09/2026).

**O relatório:** https://verificabet.com.br/pt-br/relatorios/proibicao-apostas

Tudo o que a página afirma sai dos arquivos deste repositório. O
`MANIFEST.sha256` congela esta edição: se um arquivo mudar, o hash denuncia.

---

## O que tem aqui

```
denuncias/      o que chegou ao canal do VerificaBet, AGREGADO
lai/            o acervo oficial obtido por Lei de Acesso à Informação
scripts/        o código que produziu os dois
proibicao-apostas-ed01.json    os números já formatados que a página lê
```

### `denuncias/`

Contagem por dia, por categoria e por tipo de endereço.

🔴 **Nenhuma denúncia individual está aqui, e isso não é descuido.** Não há
descrição, e-mail, protocolo nem qualquer campo que identifique quem denunciou ou
sobre quem. O relatório não precisa deles para afirmar o que afirma. O
`COMO_FOI_MEDIDO.md` da pasta descreve o recorte.

### `lai/`

Séries mensais do SIGAP (aportes, retiradas, pessoas, GGR), arrecadação federal
por grupo de tributo e ordens de bloqueio, obtidas da Secretaria de Prêmios e
Apostas e da Receita Federal por pedidos de acesso à informação.

`2026-10-05-pedidos-lai-receita-cetad.json` traz o **texto literal dos dois
pedidos** que fizemos à Receita e a resposta verbatim, com `sha256` de cada um e o
id da manifestação na BuscaLAI. Os PDFs dos anexos **não** são redistribuídos
aqui: são documentos do órgão e já estão públicos na BuscaLAI, e o arquivo traz o
link e o procedimento para baixá-los.

### `scripts/`

`congela.py` e `congela-lai.py` produzem os CSVs; `dados.py` transforma em
números formatados por idioma. Não rodam sem acesso ao nosso banco — estão aqui
para mostrar **o método**, não para serem executados por terceiros. O
`README.md` da pasta lista as armadilhas que a medição pegou.

---

## 🔴 As quatro regras que estes números seguem

**Safra por grão.** Cada resposta de LAI reescreve meses antigos. A leitura fica
com a linha mais recente de cada mês, nunca a soma de todas.

**Mês em consolidação fica fora dos totais.** Dado parcial puxa o total para
baixo sem erro nenhum: agosto de 2026 trazia R$ 7,0 bi contra ~R$ 13 bi dos meses
fechados.

**`cpfs_unicos` é MENSAL e não se soma.** São os CPFs únicos naquele mês. Somar
os meses conta a mesma pessoa várias vezes. Por isso o relatório publica média e
pico, nunca um total de apostadores.

**As janelas não são a mesma.** A fatia da saúde, o fluxo, o GGR e a arrecadação
têm bases e períodos próprios. Dividir uma pela outra erra por uma ordem de
grandeza — e é por isso que cada bloco declara a sua.

---

## O que o relatório recusou publicar

Está aqui para quem quiser conferir que a recusa foi justificada:

- **A comparação simétrica.** Os dias imediatamente anteriores à MP estão
  contaminados por uma queda de tráfego ao nosso formulário, com um dia sem
  nenhuma denúncia. A conta óbvia dá mais do que o dobro da razão correta. Os
  dias estão no CSV, marcados como fase `anomalia`.
- **A razão não autorizado:autorizado.** Os denominadores são pequenos demais
  (16 e 4 denúncias) para sustentar a comparação. O número está no JSON, fora da
  copy.

---

## Licença

Código: MIT (`LICENSE`). Dados produzidos pelo VerificaBet: CC BY 4.0
(`LICENSE-DADOS.md`). Documentos e séries dos órgãos públicos seguem o regime
deles — veja `LICENSE-DADOS.md`.

Crédito sugerido:

> VerificaBet, "1,18% foi para a saúde. Zero estudos sobre o custo de proibir",
> edição 01, https://verificabet.com.br/pt-br/relatorios/proibicao-apostas

## Erro, dúvida ou pedido de correção

Abra uma issue neste repositório, ou use
https://verificabet.com.br/pt-br/correcao-de-informacoes
