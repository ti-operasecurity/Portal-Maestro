# Maestro - Portal de Aplicações

Portal centralizado para acesso às aplicações internas da empresa.

## Estrutura do Projeto

```
Maestro/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── Dockerfile            # Configuração Docker
├── templates/
│   └── index.html        # Template HTML principal
└── static/
    ├── css/
    │   └── style.css     # Estilos CSS
    └── images/
        └── logo_opera.png # Logo do portal
```

## Execução Local

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute a aplicação:
```bash
python app.py
```

3. Acesse no navegador:
```
http://localhost:5000
```

## Execução com Docker

### Construir a imagem:
```bash
docker build -t maestro-portal .
```

### Executar o container:
```bash
docker run -d -p 5000:5000 --name maestro maestro-portal
```

### Executar com variáveis de ambiente customizadas:
```bash
docker run -d -p 8080:5000 -e PORT=5000 -e HOST=0.0.0.0 --name maestro maestro-portal
```

## Aplicações Disponíveis

- Painel de Monitoração Produtiva
- Dashboard de Perdas
- Monitoramento de Fornos
- Robô Logistica
- Monitoramento Autoclaves
- Aging de Estoque

## Tecnologias Utilizadas

- Flask 3.0.0
- Gunicorn (para produção)
- HTML5/CSS3
- Docker

