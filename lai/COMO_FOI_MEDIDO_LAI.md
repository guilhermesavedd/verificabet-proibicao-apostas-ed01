# Congelado do acervo de LAI — escala do mercado proibido

| bloco | meses | janela |
|---|---|---|
| fluxo (aportes, retiradas, pessoas) | 18 | 2025-01 a 2026-06 |
| GGR | 18 | 2025-01 a 2026-06 |
| arrecadação | 20 | 2025-01 a 2026-08 |
| URLs bloqueadas | 19 | 2025-01 a 2026-07 |

🔴 **Safra por grão:** cada resposta de LAI reescreve meses antigos; fica a
linha de `captured_at` mais recente de cada mês.

🔴 **Mês em consolidação fica FORA dos totais** — dado parcial puxa o total
para baixo sem erro nenhum. Excluídos: 2026-07, 2026-08.

🔴 **`cpfs_unicos` é MENSAL e não se soma:** são os CPFs únicos naquele mês.
Somar os meses conta a mesma pessoa várias vezes. Só média e pico.

🔴 **As janelas não são a mesma.** O GGR tem menos meses consolidados que o
fluxo; comparar os dois totais exige citar as duas janelas.

## Fontes

- CGFA/SPA-MF via LAI 18800.126199/2026-92 (Acesso Concedido em 10/08/2026)
- Receita Federal via LAI 18800.130498/2026-21 (BETS 2025-2026, arrecadacao mensal por grupo de tributo; resposta 17/08/2026)
- Receita Federal via LAI 18800.144951/2026-87 (BETS 2025-2026, arrecadacao mensal por grupo de tributo; resposta 22/09/2026)
- SPA/MF via LAI 18800.142404/2026-67 (pedido_informacao_ggr_apostas_123155.xlsx, resposta 22/09/2026)
- SPA/MF via LAI 18800.145386/2026-75 (pedido_informacao_carteira_aposta_ggr.xlsx, resposta 30/09/2026)
