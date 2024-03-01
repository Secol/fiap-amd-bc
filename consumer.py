import pika
from web3 import Web3
import json
import hashlib

# Conectar ao provedor Ethereum (pode ser um nó local, Infura, Alchemy, etc.)
web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

# Endereço do contrato Storage (substitua pelo seu)
contract_address = "0x743Efd1d0beaD80333bC5EE9cE95Ec8df0609b06"
from_address = "0x09954f862B58F93D4EC58B438778Be461D80b2f8"
private_key = "0xefce32d11b68482b235242a67c8c83ea9de0c4462c92853a1117279e37dd4dc2"
# ABI do contrato Storage (substitua pelo seu)
contract_abi = [
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

nonce = web3.eth.get_transaction_count(from_address)

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

def register_item(item_id, hash):
    # Preparar a transação
    txn = contract.functions.registerItem(item_id, hash).build_transaction({
        'chainId': web3.eth.chain_id,  # Substitua pelo ID correto da sua rede
        'gas': 2000000,
        'gasPrice': web3.to_wei('50', 'gwei'),
        'nonce': web3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
    })

    # Assinar a transação
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=private_key)
    # Enviar a transação
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Aguardar a confirmação da transação
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    # retorna apenas o hash da transação
    return tx_receipt.transactionHash.hex()

# Conectar ao RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', credentials=pika.PlainCredentials('user', 'password')))
channel = connection.channel()

# Declarar a fila
channel.queue_declare(queue='produtos.lote.update')

# Callback para processar mensagens
def callback(ch, method, properties, body):
    dicionario = json.loads(body)
    string = f'Item: {dicionario["numero_do_lote"]}, Status: {dicionario["status"]}, Data: {dicionario["dt_update"]}'
    # Criar um objeto hash SHA256
    hash_obj = hashlib.sha256()
    # Atualizar o objeto hash com a string (necessário codificar a string para bytes)
    hash_obj.update(string.encode())
    # Obter o hash hexadecimal
    hash_hex = hash_obj.hexdigest()
    print("[x] Received %r" % body)
    # Registrar o item na blockchain
    tx_receipt = register_item(dicionario["_id"], hash_hex)
    # retorna o recibo da transação
    print(print("[x] Tx hash %r" % tx_receipt))

channel.basic_consume(queue='produtos.lote.update', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
