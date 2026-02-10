-- Adiciona aplicação "Dashboard de Produção" na tabela de aplicações principais
-- Assim ela aparece na lista de seleção ao editar usuário (Grupo Operação) e pode ser permitida separadamente

INSERT INTO maestro_applications (name, url_proxy, display_name, icon, color, active)
SELECT
    'dashboard-producao',
    'dashboard-producao',
    'Dashboard de Produção',
    '📈',
    '#10b981',
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM maestro_applications WHERE url_proxy = 'dashboard-producao'
);

UPDATE maestro_applications
SET
    name = 'dashboard-producao',
    display_name = 'Dashboard de Produção',
    icon = '📈',
    color = '#10b981',
    active = TRUE
WHERE url_proxy = 'dashboard-producao';
