# Análise do relatório Shodan (186.227.125.170)

**Conclusão principal:** os riscos apontados pelo Shodan vêm **principalmente das portas abertas no firewall**, não do código do portal Maestro. O acesso direto a aplicações internas e ao PostgreSQL existe porque essas portas estão expostas na internet. Corrigir o firewall resolve a maior parte do problema.

---

## 1. Crítico: portas abertas na internet

O relatório mostra **várias portas além de 22, 80 e 443** acessíveis da internet:

| Porta | Serviço/Aplicação exposta | Risco |
|-------|---------------------------|--------|
| **5432** | **PostgreSQL** – "no password supplied" | **Crítico**: banco acessível da internet. |
| 2000, 4000, 4300 | Apps internos (Portal Jarinu, etc.) | Alto: acesso sem passar pelo Maestro. |
| 5000, 5003, 5123 | Werkzeug/gunicorn (Monitor Autoclaves, Menu Linhas, etc.) | Alto: mesmo motivo. |
| 5555 | Redirect para 10.150.16.45:9996 | Médio: expõe IP interno. |
| 8081, 8083, 8085, 8086, 8087 | Nginx/waitress (TVs, Plano de Controle, Certificados, etc.) | Alto: apps direto na internet. |
| 8090, 9020, 9051, 9991 | Outros sistemas | Alto. |

**Ação obrigatória (firewall, ex.: Fortinet):**

- Permitir na internet **apenas**: **22 (SSH), 80 (HTTP), 443 (HTTPS)**.
- **Bloquear** todas as outras portas para o IP público do servidor (5432, 4000, 4300, 5000, 5003, 5123, 5555, 8081, 8083, 8085, 8086, 8087, 8090, 9020, 9051, 9991, etc.).

Com isso, só o Nginx (80/443) do Maestro fica exposto; o resto continua acessível apenas na rede interna.

---

## 2. Crítico: PostgreSQL (5432) exposto

A mensagem `fe_sendauth: no password supplied` indica que o **PostgreSQL está aceitando conexões da internet**.

**Ações:**

1. **Firewall:** bloquear a porta **5432** para a internet.
2. Configurar o PostgreSQL para escutar apenas em **localhost** ou rede interna (`listen_addresses` no `postgresql.conf`).
3. Senhas fortes e, se possível, restringir `pg_hba.conf` a IPs internos.

O Maestro usa Supabase (na nuvem); esse PostgreSQL é de **outro serviço** na mesma máquina/rede. Quem administra esse serviço deve aplicar as ações acima.

---

## 3. Vazamento de informações (consequência das portas abertas)

O Shodan consegue listar **versões** (Nginx, Python, Flask, etc.) e **nomes de sistemas** ("Portal Jarinu", "Monitor de Autoclaves", "Sistema de TVs", etc.) porque **cada aplicação está respondendo em uma porta exposta**. Também aparecem IPs internos (ex.: 10.150.16.45) em redirects e headers quando se acessa essas portas.

**Ação:** fechar no firewall as portas das aplicações (item 1) elimina esse vazamento para a internet. No Maestro já foi aplicado `server_tokens off` no Nginx para não divulgar a versão no único ponto de entrada (80/443).

---

## Resumo: prioridade é o firewall

| Prioridade | Ação |
|------------|------|
| **1 – Imediato** | **Firewall:** abrir só **22, 80 e 443**; bloquear todas as outras portas. |
| **2 – Imediato** | **PostgreSQL:** garantir que 5432 não esteja acessível da internet e que escute só em localhost/rede interna. |
| **3 – Contínuo** | Manter sistema e pacotes atualizados (OS, Nginx, Python, OpenSSH, etc.). |

**Em resumo:** os erros do relatório Shodan estão ligados às **portas abertas**. Ajustar o firewall e a escuta do PostgreSQL resolve o cenário crítico. O código do portal Maestro já teve melhorias de segurança aplicadas (CORS, X-XSS-Protection, `server_tokens off` no Nginx), e o funcionamento do portal permanece o mesmo.
