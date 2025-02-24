from web3 import Web3  # Importa a biblioteca Web3 para interagir com a blockchain
import time  # Importa a biblioteca time para usar a função sleep

ganache_url = "http://127.0.0.1:7545"  # Define a URL do Ganache
web3 = Web3(Web3.HTTPProvider(ganache_url))  # Conecta ao Ganache usando a URL definida

if web3.is_connected():  # Verifica se a conexão com o Ganache foi bem-sucedida
    print("Conectado ao Ganache")  # Imprime mensagem de sucesso
else:
    print("Falha na conexão com o Ganache")  # Imprime mensagem de falha

contract_abi = [  # Define a ABI (Application Binary Interface) do contrato
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "string",
          "name": "itemId",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "hash",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "address",
          "name": "registeredBy",
          "type": "address"
        }
      ],
      "name": "ItemRegistered",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "name": "items",
      "outputs": [
        {
          "internalType": "string",
          "name": "hash",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "registeredBy",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "itemId",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "hash",
          "type": "string"
        }
      ],
      "name": "registerItem",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "itemId",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "hash",
          "type": "string"
        }
      ],
      "name": "verifyItem",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    }
]
contract_address = "0x430DdD63bdBf319BB252A810e7264223DC576da6"  # Define o endereço do contrato

contract = web3.eth.contract(address=contract_address, abi=contract_abi)  # Cria uma instância do contrato

def handle_event(event):  # Define a função para lidar com eventos
    print(f"Novo Evento: {event}")  # Imprime o evento recebido

def log_loop(event_filter, poll_interval):  # Define a função para filtrar e processar eventos
    while True:  # Loop infinito
        for event in event_filter.get_new_entries():  # Obtém novos eventos
            handle_event(event)  # Chama a função para lidar com o evento
        time.sleep(poll_interval)  # Aguarda o intervalo de tempo definido

event_filter = contract.events.ItemRegistered.create_filter(from_block='latest')  # Cria um filtro para eventos do tipo ItemRegistered

log_loop(event_filter, 2)  # Inicia o loop de log com intervalo de 2 segundos
