-- Remove "Dash Ocupação Forno" apenas da aba Aplicações (maestro_portal_applications).
-- O dashboard continua na tela principal (maestro_applications).

-- 1) Remover permissões de usuário associadas a esse app na aba Aplicações
DELETE FROM maestro_user_portal_app_access
WHERE portal_app_id IN (
    SELECT id FROM maestro_portal_applications
    WHERE key = 'dashboard-ocupacao-forno'
);

-- 2) Remover o app da aba Aplicações
DELETE FROM maestro_portal_applications
WHERE key = 'dashboard-ocupacao-forno';
