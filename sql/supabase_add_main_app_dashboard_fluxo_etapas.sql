-- Adiciona aplicação "Dashboard de Fluxo por Etapas" na tabela de aplicações principais (tela inicial)
-- Esta aplicação aparecerá como card na tela principal do portal

-- Verificar se já existe e atualizar, caso contrário inserir
INSERT INTO maestro_applications (name, url_proxy, display_name, icon, color, active)
SELECT 
    'dashboard-fluxo-etapas',
    '/proxy/dashboard-fluxo-etapas',
    'Dashboard de Fluxo por Etapas',
    '🔀',
    '#8b5cf6',
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM maestro_applications WHERE url_proxy = '/proxy/dashboard-fluxo-etapas'
);

-- Atualizar se já existir
UPDATE maestro_applications
SET 
    name = 'dashboard-fluxo-etapas',
    display_name = 'Dashboard de Fluxo por Etapas',
    icon = '🔀',
    color = '#8b5cf6',
    active = TRUE
WHERE url_proxy = '/proxy/dashboard-fluxo-etapas';
