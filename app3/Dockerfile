# Dockerfile
FROM python:3.9

# Copia os arquivos de código para o container
WORKDIR /app
COPY . /app

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Flask usará
EXPOSE 9023

# Comando para rodar o aplicativo
CMD ["python", "app3.py"]
