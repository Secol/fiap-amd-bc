from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import uvicorn
from datetime import datetime
from web3 import Web3
import json
import hashlib
import pika
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Conectar ao provedor Ethereum (pode ser um nó local, Infura, Alchemy, etc.)
web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

mongodb_url = os.environ.get("MONGODB_HOST", "localhost")
rabbitmq_url = os.environ.get("RABBITMQ_HOST", "localhost")

# Endereço do contrato Storage (substitua pelo seu)
contract_address = os.environ.get("CONTRACT_ADDRESS")
from_address = os.environ.get("ACCOUNT_ADDRESS")
private_key = os.environ.get("PRIVATE_KEY")

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

def verify_item(object):
    string = f'Item: {object["numero_do_lote"]}, Status: {object["status"]}, Data: {object["dt_update"]}'
    # Criar um objeto hash SHA256
    hash_obj = hashlib.sha256()
    # Atualizar o objeto hash com a string (necessário codificar a string para bytes)
    hash_obj.update(string.encode())
    # Obter o hash hexadecimal
    hash_hex = hash_obj.hexdigest()
    # Chamada de função de leitura; não requer transação
    is_valid = contract.functions.verifyItem(object["_id"], hash_hex).call()
    print (is_valid)
    return is_valid

def objectid_is_valid(oid):
    try:
        oid = ObjectId(oid)
        return True
    except:
        return False

class UpdateModel(BaseModel):
    numero_do_lote: str
    status: str

client = MongoClient(f'mongodb://user:password@{mongodb_url}:27017/')
db = client['main_db']
collection = db['lotes']

def json_encoder(o):
    if isinstance(o, ObjectId):
        return str(o)
    elif isinstance(o, datetime):
        return o.isoformat()
    return o.__str__

def publish_message(message):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_url, credentials=pika.PlainCredentials('user', 'password'))
    )
    channel = connection.channel()
    channel.queue_declare(queue='produtos.lote.update')
    channel.basic_publish(exchange='', routing_key='produtos.lote.update', body=message)
    connection.close()

@app.post("/update/")
async def update(update_model: UpdateModel):
    result = update_model.model_dump()
    result['dt_update'] = datetime.now().isoformat()
    insert_result = collection.insert_one(result)
    if insert_result.inserted_id:
        # Incluir _id no objeto
        result['_id'] = insert_result.inserted_id
        # Converter o resultado para JSON
        json_result = json.dumps(result, default=json_encoder)
        publish_message(json_result)
        return json.loads(json_result)
    else:
        raise HTTPException(status_code=500, detail="Erro ao inserir o documento.")

@app.get("/{_id}")
async def get_document(_id: str):
    if not objectid_is_valid(_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    
    document = collection.find_one({"_id": ObjectId(_id)})
    
    if document:
        # Como o find_one retorna um objeto PyMongo que pode conter um ObjectId,
        # usamos json.dumps com um método default modificado para converter corretamente
        # o ObjectId para string.
        return json.loads(json.dumps(document, default=json_encoder))
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.get("/verify/{_id}")
async def get_document(_id: str):
    if not objectid_is_valid(_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    
    document = collection.find_one({"_id": ObjectId(_id)})
    
    if document:
        # Como o find_one retorna um objeto PyMongo que pode conter um ObjectId,
        # usamos json.dumps com um método default modificado para converter corretamente
        # o ObjectId para string.
        retorno = verify_item(json.loads(json.dumps(document, default=json_encoder)))

        return {'result': retorno}
    else:
        raise HTTPException(status_code=404, detail="Document not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)