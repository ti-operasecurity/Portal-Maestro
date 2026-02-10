-- Atualiza o nome e descrição da aplicação do portal (key: app-8090)
-- Nome: De "Vinculação de ProductionOrders | SAP" para "Orquestrador de Ordens de Produção | SAP"
-- Descrição: De "Atribuição de locais no estoque para PA" para "Ordens de vendas X Ordens de Produção"

UPDATE maestro_portal_applications
SET name = 'Orquestrador de Ordens de Produção | SAP',
    description = 'Ordens de vendas X Ordens de Produção'
WHERE key = 'app-8090';

