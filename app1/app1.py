import socket
import threading
from flask import Flask, request, jsonify
import requests
import sys

app = Flask(__name__)

token_holder = False
servers = [{'address': 'http://app1:9021', 'token_holder': False},
           {'address': 'http://app2:9022', 'token_holder': False},
           {'address': 'http://app3:9023', 'token_holder': False}]

def send_message(server, message_type, payload=''):
    try:
        message = f'{message_type}|http://app1:9021|{payload}'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(server)
            s.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f'Erro ao enviar mensagem para {server}: {e}')

def handle_message(message):
    global token_holder
    global servers

    parts = message.split('|')
    if len(parts) < 3:
        print("Mensagem mal formatada:", message)
        return

    message_type = parts[0]
    sender_address = parts[1]
    payload = parts[2]

    if message_type == 'TOKEN':
        token_holder = True
        for server in servers:
            server['token_holder'] = (server['address'] == 'http://app1:9021')
        print('[TOKEN RECEIVED!]')

    elif message_type == 'HEARTBEAT':
        send_message(tuple(sender_address.split(':')), 'HEARTBEAT_RESPONSE', '')
        
    elif message_type == 'REGISTER':
        new_server = payload
        if new_server not in [server['address'] for server in servers]:
            servers.append({'address': new_server, 'token_holder': False})
            print(f'[NEW SERVER CONNECTED!] {new_server}')
    
    elif message_type == 'STATUS':
        status = 'TOKEN_HOLDER' if token_holder else 'NOT_TOKEN_HOLDER'
        send_message(tuple(sender_address.split(':')), 'STATUS_RESPONSE', status)

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', 9001))
        server_socket.listen()
        print("Servidor iniciado. Aguardando mensagens...")
        while True:
            client_socket, addr = server_socket.accept()
            with client_socket:
                message = client_socket.recv(1024).decode('utf-8')
                handle_message(message)

def get_next_server():
    global servers
    current_index = next((index for index, d in enumerate(servers) if d["address"] == 'http://app1:9021'), -1)
    for i in range(1, len(servers) + 1):
        next_index = (current_index + i) % len(servers)
        if check_server_alive(tuple(servers[next_index]['address'].split(':'))):
            return tuple(servers[next_index]['address'].split(':'))
    regenerate_token()

def check_server_status():
    global token_holder
    global servers
    active_servers = []
    
    for server in servers:
        if server['address'] != 'http://app1:9021':
            if check_server_alive(tuple(server['address'].split(':'))):
                active_servers.append(server)
            else:
                print(f"{server['address']} está fora e será removido.")
                if token_holder and server['token_holder']:
                    regenerate_token()

    servers = active_servers

    threading.Timer(5.0, check_server_status).start()

def check_server_alive(server):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(server)
            s.sendall(b'HEARTBEAT|http://app1:9021|')
            return True
    except socket.error:
        return False

def regenerate_token():
    global token_holder
    global servers
    print('Regenerando token...')
    token_holder = True
    for server in servers:
        server['token_holder'] = (server['address'] == 'http://app1:9021')
    print('[NEW TOKEN CREATED]')
    threading.Timer(5.0, lambda: send_message(get_next_server(), 'TOKEN')).start()

def register_with_existing_services():
    global servers
    for server in servers:
        if server['address'] != 'http://app1:9021':
            try:
                response = requests.post(f'{server["address"]}/check_registration', json={'address': 'http://app1:9021'})
                if response.status_code == 200:
                    registered = response.json().get('registered', False)
                    if not registered:
                        requests.post(f'{server["address"]}/register', json={'address': 'http://app1:9021'})
                else:
                    requests.post(f'{server["address"]}/register', json={'address': 'http://app1:9021'})
            except requests.RequestException as e:
                print(f'Erro ao registrar com {server["address"]}: {e}')

@app.route('/token', methods=['POST'])
def receive_token():
    global token_holder
    token_holder = True
    print('[TOKEN RECEIVED!]')
    return jsonify({'status': 'Token recebido'})

@app.route('/pass_token', methods=['POST'])
def pass_token():
    global token_holder
    if token_holder:
        token_holder = False
        try:
            send_message(get_next_server(), 'TOKEN')
            print('[TOKEN PASSED]')
            return jsonify({'status': 'Token passado'})
        except Exception as e:
            print('Erro ao passar token:', e)
            return jsonify({'status': 'Erro ao passar token'}), 500
    else:
        return jsonify({'status': 'Não possuo o token'}), 400

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return jsonify({'status': 'alive'})

@app.route('/register', methods=['POST'])
def register():
    global servers
    new_server = request.json['address']
    if new_server not in [server['address'] for server in servers]:
        servers.append({'address': new_server, 'token_holder': False})
        print(f'[NEW SERVER CONNECTED!] {new_server}')
    return jsonify({'status': 'Registrado'})

@app.route('/check_registration', methods=['POST'])
def check_registration():
    address = request.json['address']
    is_registered = any(server['address'] == address for server in servers)
    return jsonify({'registered': is_registered})

if __name__ == '__main__':
    print("Instruções:")
    print("1. Certifique-se de que todos os servidores estão configurados e rodando.")
    print("2. Quando todos os servidores estiverem prontos e conectados, digite qualquer tecla e pressione Enter para iniciar.")
    input("Pressione Enter para iniciar...")
    threading.Thread(target=start_server).start()
    threading.Timer(5.0, check_server_status).start()
    register_with_existing_services()
    app.run(host='0.0.0.0', port=9021)
