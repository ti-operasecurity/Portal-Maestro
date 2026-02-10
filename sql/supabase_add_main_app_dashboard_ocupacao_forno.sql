-- Adiciona aplicação "Dash Ocupação Forno" na tabela de aplicações principais (tela inicial)
-- Esta aplicação aparecerá como card na tela principal do portal

-- Verificar se já existe e atualizar, caso contrário inserir
INSERT INTO maestro_applications (name, url_proxy, display_name, icon, color, active)
SELECT 
    'Dash Ocupação Forno',
    'dashboard-ocupacao-forno',
    'Dash Ocupação Forno',
    '🔥',
    '#f59e0b',
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM maestro_applications WHERE url_proxy = 'dashboard-ocupacao-forno'
);

-- Atualizar se já existir
UPDATE maestro_applications
SET 
    name = 'Dash Ocupação Forno',
    display_name = 'Dash Ocupação Forno',
    icon = '🔥',
    color = '#f59e0b',
    active = TRUE
WHERE url_proxy = 'dashboard-ocupacao-forno';

