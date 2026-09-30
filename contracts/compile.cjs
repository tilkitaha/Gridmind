const fs=require('fs'),solc=require('solc');
const input={language:'Solidity',sources:{'EnergySettlement.sol':{content:fs.readFileSync('contracts/EnergySettlement.sol','utf8')}},settings:{optimizer:{enabled:true,runs:200},evmVersion:'prague',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
const r=JSON.parse(solc.compile(JSON.stringify(input)));
if((r.errors||[]).some(x=>x.severity==='error'))throw Error(JSON.stringify(r.errors));
fs.writeFileSync('contracts/compiled.json',JSON.stringify({compiler:solc.version(),input,contract:r.contracts['EnergySettlement.sol'].EnergySettlement},null,2));
