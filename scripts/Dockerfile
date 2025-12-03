# Imagem base Python (usando bookworm que é mais estável)
FROM python:3.11-slim-bookworm

# Instala dependências do sistema
# Múltiplas tentativas para lidar com Hash Sum mismatch do Fortinet
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    for i in 1 2 3 4 5; do \
        echo "Tentativa $i de instalação do gcc..." && \
        apt-get update && \
        apt-get install -y --fix-missing --no-install-recommends gcc python3-dev && \
        break || (echo "Tentativa $i falhou, aguardando..." && sleep 30); \
    done && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos da aplicação
# Verifica se está na estrutura nova (app/) ou antiga (raiz)
COPY app.py auth.py security.py http_pool.py monitoring.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY logo_opera.png ./

# Cria diretório para logs
RUN mkdir -p /app/logs

# Expõe a porta 8000
EXPOSE 8000

# Define variáveis de ambiente padrão
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/login').read()" || exit 1

# Comando para iniciar a aplicação
# Configurações otimizadas para performance e compatibilidade com Safari/macOS
# Workers: (2 x CPU cores) + 1 (fórmula recomendada para I/O bound)
# Threads: 4 por worker para melhor concorrência
# Timeout: 120s para requisições longas (proxy)
# Keep-alive: 10s para manter conexões abertas
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "5", "--threads", "4", "--timeout", "120", "--keep-alive", "10", "--worker-class", "gthread", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"]
