# Renovação automática do certificado SSL (Let's Encrypt)

O certificado do Let's Encrypt vale **90 dias**. Para não deixar vencer, configure a renovação automática no servidor.

## Como funciona

- O **Certbot** só renova quando o certificado está a **cerca de 30 dias** do vencimento.
- O script `scripts/renovar-certificado.sh` roda o `certbot renew` e reinicia o Nginx.
- Se ainda não estiver perto do vencimento, o script só confirma que está tudo OK e encerra.

## Configurar cron (recomendado)

1. **Dar permissão de execução ao script** (se ainda não tiver):
   ```bash
   chmod +x /opt/apps/maestro/scripts/renovar-certificado.sh
   ```

2. **Abrir o crontab do root**:
   ```bash
   crontab -e
   ```

3. **Incluir esta linha** (uma única linha; troque o caminho se o projeto estiver em outro lugar):
   ```cron
   0 3 * * * cd /opt/apps/maestro && ./scripts/renovar-certificado.sh
   ```
   Isso executa **todo dia às 03:00**. O Certbot só fará a renovação quando faltar ~30 dias para o certificado vencer.

4. **Salvar e sair** (no vi: `Esc`, depois `:wq` e Enter).

## Conferir se está agendado

```bash
crontab -l
```

Deve aparecer a linha com `renovar-certificado.sh`.

## Logs

O script grava log em:

```
/opt/apps/maestro/logs/certbot-renewal.log
```

Para ver as últimas execuções:

```bash
tail -50 /opt/apps/maestro/logs/certbot-renewal.log
```

## Testar manualmente

Para testar sem esperar o cron:

```bash
cd /opt/apps/maestro
./scripts/renovar-certificado.sh
```

Se o certificado ainda estiver longe do vencimento, o script termina rápido informando que está válido. Quando faltar ~30 dias, o Certbot renovará e o Nginx será reiniciado.

## Resumo

| O quê | Quando |
|------|--------|
| Certificado válido | 90 dias (ex.: 12/fev a 13/mai) |
| Certbot tenta renovar | Quando faltar ~30 dias |
| Cron sugerido | Todo dia às 03:00 |
| Log | `logs/certbot-renewal.log` |

Com o cron configurado, a renovação fica garantida antes do vencimento.
