#!/bin/bash
# Script para reorganizar a estrutura de pastas da aplicação
# Uso: ./organizar-estrutura.sh

set -e

echo "📁 Reorganizando estrutura de pastas..."

# Criar estrutura de pastas
mkdir -p app
mkdir -p config/nginx
mkdir -p config/ssl
mkdir -p scripts
mkdir -p docs
mkdir -p logs/nginx

# Mover arquivos Python principais
echo "📦 Movendo arquivos Python..."
mv app.py app/ 2>/dev/null || true
mv auth.py app/ 2>/dev/null || true
mv security.py app/ 2>/dev/null || true
mv http_pool.py app/ 2>/dev/null || true
mv monitoring.py app/ 2>/dev/null || true

# Mover templates e static
echo "🎨 Movendo templates e static..."
if [ -d "templates" ]; then
    mv templates app/ 2>/dev/null || true
fi
if [ -d "static" ]; then
    mv static app/ 2>/dev/null || true
fi

# Mover imagens
echo "🖼️ Movendo imagens..."
mv logo_opera.png app/ 2>/dev/null || true
mv Opera.png app/ 2>/dev/null || true
mv background.png app/ 2>/dev/null || true

# Mover scripts para pasta scripts
echo "🔧 Organizando scripts..."
mv *.sh scripts/ 2>/dev/null || true
mv *.py scripts/ 2>/dev/null || true

# Mover documentação
echo "📚 Organizando documentação..."
mv *.md docs/ 2>/dev/null || true
mv *.sql docs/ 2>/dev/null || true

# Manter arquivos importantes na raiz
echo "✅ Estrutura organizada!"
echo ""
echo "📋 Nova estrutura:"
echo "  app/          - Código da aplicação"
echo "  config/       - Configurações (nginx, ssl)"
echo "  scripts/      - Scripts de deploy e manutenção"
echo "  docs/         - Documentação"
echo "  logs/         - Logs da aplicação"
echo ""
echo "⚠️  IMPORTANTE: Atualize o Dockerfile se necessário!"

