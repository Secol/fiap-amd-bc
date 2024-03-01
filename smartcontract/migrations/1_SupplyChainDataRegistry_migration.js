const SupplyChainDataRegistry = artifacts.require("SupplyChainDataRegistry");

module.exports = function(deployer) {

deployer.deploy(SupplyChainDataRegistry);
};
