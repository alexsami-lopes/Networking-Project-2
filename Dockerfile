# Usar uma imagem base oficial do Python
FROM python:3.9

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copiar os arquivos de requisitos para o diretório de trabalho
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação para o diretório de trabalho
COPY . .

# Definir a variável de ambiente para que o Flask saiba que está sendo executado em produção
ENV FLASK_ENV=development

# Expor a porta em que a aplicação será executada
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "banco.py"]
