# Congelado do relatório — MP 1.394

| campo | valor |
|---|---|
| tabela | `complaints` |
| vigência da MP (dia 0) | 2026-09-25 |
| janela ANTES | 2026-07-01 a 2026-09-17 (14 dias) |
| janela DEPOIS | 2026-09-25 a 2026-10-09 (14 dias) |
| denúncias antes | 1215 |
| denúncias depois | 682 |
| congelado em | 2026-10-14 |

🔴 As duas janelas têm **o mesmo número de dias**, de propósito. Medir só o
depois faz qualquer coisa parecer novidade: a denúncia contra casa não
autorizada já era a esmagadora maioria antes da MP, e só a comparação por dia
mostra isso.

🔴 **Nenhuma linha individual foi exportada.** Sem `description`, sem e-mail,
sem protocolo. Só contagem por dia, categoria e tipo de domínio.

⚠️ `problem_type` é multivalorado: a soma das categorias é maior que o total de
denúncias. O relatório diz isso onde usa a quebra.
