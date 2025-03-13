import pika # Biblioteca usada para se conectar e interagir com o RabbitMQ.
from web3 import Web3 # Biblioteca web3.py, que é utilizada para interagir com a blockchain Ethereum.
import json # Módulo usado para manipular dados no formato JSON.
import hashlib # Módulo hashlib fornece implementações de algoritmos de hash, como SHA-256.
from dotenv import load_dotenv
import os

load_dotenv()

rabbitmq_url = os.environ.get("RABBITMQ_HOST", "localhost")

# Estabelece uma conexão com um nó Ethereum usando o provedor HTTP. Neste caso, está conectando-se a um nó local Ganache.
web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

# Especifica o endereço do contrato inteligente implantado na blockchain.
contract_address = os.environ.get("CONTRACT_ADDRESS")
# Endereço da conta que será usada para enviar transações para o contrato inteligente
from_address = os.environ.get("ACCOUNT_ADDRESS")
# Chave privada associada ao endereço acima. Esta chave é usada para assinar transações antes de enviá-las para a blockchain.
private_key = os.environ.get("PRIVATE_KEY")

# Define a ABI (Application Binary Interface) do contrato, que é necessária para interagir com ele.
# A ABI descreve os métodos e eventos do contrato, incluindo seus parâmetros e tipos de retorno.
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

# Obtém o número de transações já enviadas pelo endereço `from_address`.
# Esse número (nonce) é usado para garantir que cada transação tenha um identificador único.
nonce = web3.eth.get_transaction_count(from_address)

# Cria uma instância do contrato inteligente no endereço especificado e com a ABI fornecida,
# permitindo chamadas de funções e eventos.
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Define uma função para registrar um item na blockchain com um ID e um hash.
def register_item(item_id, hash):
    # Constrói uma transação para chamar a função `registerItem` no contrato inteligente.
    # A transação inclui o ID do item e o hash. Outros parâmetros incluem o chainId, limite de gas, preço do gas, e nonce.
    txn = contract.functions.registerItem(item_id, hash).build_transaction({
        'chainId': web3.eth.chain_id,
        'gas': 1000000,
        'gasPrice': web3.to_wei('1', 'gwei'),
        'nonce': web3.eth.get_transaction_count(Web3.to_checksum_address(from_address)),
    })

    # Assina a transação com a chave privada, o que é necessário para autorizar a transação.
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=private_key)
    # Envia a transação assinada para a rede Ethereum e retorna o hash da transação.
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    # Espera até que a transação seja incluída em um bloco e receba a confirmação da rede.
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    # Retorna o hash da transação em formato hexadecimal.
    return tx_receipt.transactionHash.hex()

# Estabelece uma conexão com um servidor RabbitMQ rodando localmente e autentica-se com um usuário e senha.
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_url, credentials=pika.PlainCredentials('user', 'password')))
# Cria um canal de comunicação dentro da conexão RabbitMQ.
channel = connection.channel()

# Declara uma fila chamada 'produtos.lote.update'. Se a fila não existir, ela será criada.
channel.queue_declare(queue='produtos.lote.update')

# Define uma função de callback que será chamada toda vez que uma mensagem for recebida na fila 'produtos.lote.update'.
def callback(ch, method, properties, body):
    # Converte a mensagem recebida (em formato JSON) em um dicionário Python.
    dicionario = json.loads(body)
    # Cria uma string formatada contendo o número do lote, status e data de atualização extraídos da mensagem.
    string = f'Item: {dicionario["numero_do_lote"]}, Status: {dicionario["status"]}, Data: {dicionario["dt_update"]}'
    # Criar um objeto hash SHA256
    hash_obj = hashlib.sha256()
    # Atualizar o objeto hash com a string (necessário codificar a string para bytes)
    hash_obj.update(string.encode())
    # Obter o hash hexadecimal
    hash_hex = hash_obj.hexdigest()
    print("Received %r" % body)
    # Chama a função `register_item` para registrar o ID do item e o hash na blockchain.
    tx_receipt = register_item(dicionario["_id"], hash_hex)
    # retorna o recibo da transação
    print("Tx hash %r" % tx_receipt)

# Informa ao RabbitMQ que o canal deseja consumir mensagens da fila 'produtos.lote.update' usando a função de callback definida.
# O parâmetro `auto_ack=True` confirma automaticamente as mensagens assim que são recebidas.
channel.basic_consume(queue='produtos.lote.update', on_message_callback=callback, auto_ack=True)

# Imprime uma mensagem no console indicando que o programa está esperando por mensagens.
print('Aguardando mensagens. CTRL+C para finalizar.')
# Inicia o loop de consumo de mensagens, aguardando novas mensagens na fila e chamando a função de callback para processá-las.
channel.start_consuming()
