-- Atualiza o nome/descrição da aplicação do portal (key: app-8090)

UPDATE maestro_portal_applications
SET name = 'Vinculação de ProductionOrders | SAP',
    description = NULL,
    url = '/proxy/app-8090'
WHERE key = 'app-8090';

