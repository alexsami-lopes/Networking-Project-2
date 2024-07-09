from flask import Flask, request, jsonify
import threading
import datetime
import queue
import uuid
import requests

app = Flask(__name__)

# Classe para representar uma conta
class Conta:
    def __init__(self, id, saldo_inicial=0):
        self.id = id
        self.saldo = saldo_inicial
        self.lock = threading.Lock()
    
    def depositar(self, valor):
        with self.lock:
            self.saldo += valor
            return self.saldo
    
    def transferir(self, conta_destino, valor):
        with self.lock:
            if self.saldo >= valor:
                self.saldo -= valor
                conta_destino.depositar(valor)
                return True
            else:
                return False

# Criar contas iniciais
contas = {
    '1': Conta('1', 1000),
    '2': Conta('2', 1000),
    '3': Conta('3', 1000)
}

# Filas de operações para cada banco
filas = {
    '1': queue.PriorityQueue(),
    '2': queue.PriorityQueue(),
    '3': queue.PriorityQueue()
}

# Lógica do relógio
relogio_logico = {
    '1': 0,
    '2': 0,
    '3': 0
}

# Token Ring
token_ring = ['1', '2', '3']
token_index = 0
token_lock = threading.Lock()

# Função para processar operações na fila
def processar_fila(id_banco):
    while True:
        _, operacao = filas[id_banco].get()
        if operacao['tipo'] == 'deposito':
            contas[operacao['id_conta']].depositar(operacao['valor'])
        elif operacao['tipo'] == 'transferencia':
            conta_origem = contas[operacao['id_conta_origem']]
            conta_destino = contas[operacao['id_conta_destino']]
            conta_origem.transferir(conta_destino, operacao['valor'])
        filas[id_banco].task_done()

# Rota para depositar dinheiro
@app.route('/depositar', methods=['POST'])
def depositar():
    dados = request.get_json()
    id_conta = dados['id_conta']
    valor = dados['valor']
    timestamp = datetime.datetime.now().timestamp()
    operacao = {
        'id': str(uuid.uuid4()),
        'tipo': 'deposito',
        'id_conta': id_conta,
        'valor': valor,
        'timestamp': timestamp
    }
    filas[id_conta].put((timestamp, operacao))
    return jsonify({'status': 'ok'})

# Rota para transferir dinheiro
@app.route('/transferir', methods=['POST'])
def transferir():
    dados = request.get_json()
    id_conta_origem = dados['id_conta_origem']
    id_conta_destino = dados['id_conta_destino']
    valor = dados['valor']
    timestamp = datetime.datetime.now().timestamp()
    operacao = {
        'id': str(uuid.uuid4()),
        'tipo': 'transferencia',
        'id_conta_origem': id_conta_origem,
        'id_conta_destino': id_conta_destino,
        'valor': valor,
        'timestamp': timestamp
    }
    filas[id_conta_origem].put((timestamp, operacao))
    return jsonify({'status': 'ok'})

# Função para gerenciar o token ring
def gerenciar_token_ring():
    global token_index
    while True:
        with token_lock:
            id_banco = token_ring[token_index]
            processar_fila(id_banco)
            token_index = (token_index + 1) % len(token_ring)

# Iniciar threads para processamento das filas
for id_banco in filas.keys():
    threading.Thread(target=processar_fila, args=(id_banco,), daemon=True).start()

# Iniciar thread para gerenciar o token ring
threading.Thread(target=gerenciar_token_ring, daemon=True).start()

# Rodar o servidor
if __name__ == '__main__':
    app.run(port=5000)
