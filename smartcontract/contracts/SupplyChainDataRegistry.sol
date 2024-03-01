// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

contract SupplyChainDataRegistry {
    // Estrutura para representar um item na cadeia de suprimentos
    struct SupplyChainItem {
        string hash; // Hash dos dados armazenados off-chain
        uint256 timestamp; // Timestamp do registro
        address registeredBy; // Quem registrou o item
    }

    // Mapping de identificadores de itens para seus respectivos registros
    mapping(string => SupplyChainItem) public items;

    // Evento emitido quando um novo item é registrado
    event ItemRegistered(string itemId, string hash, uint256 timestamp, address registeredBy);

    // Função para registrar um novo item
    function registerItem(string memory itemId, string memory hash) public {
        require(bytes(items[itemId].hash).length == 0, "Item already registered.");

        SupplyChainItem memory newItem = SupplyChainItem({
            hash: hash,
            timestamp: block.timestamp,
            registeredBy: msg.sender
        });

        items[itemId] = newItem;

        emit ItemRegistered(itemId, hash, block.timestamp, msg.sender);
    }

    // Função para verificar a integridade de um item
    function verifyItem(string memory itemId, string memory hash) public view returns (bool) {
        if(keccak256(abi.encodePacked(items[itemId].hash)) == keccak256(abi.encodePacked(hash))) {
            return true;
        } else {
            return false;
        }
    }
}
