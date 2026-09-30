// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;
/// Research accounting credits only. Operator remains responsible for meter truth.
contract EnergySettlement {
 address public immutable operator; address public immutable treasury;
 mapping(address=>bool) public member; mapping(address=>uint256) public balance;
 mapping(bytes32=>bool) public settled;
 event Settled(bytes32 indexed id,address indexed seller,address indexed buyer,uint256 microKwh,uint256 amount,uint256 fee);
 constructor(address[] memory members,address feeAccount){
  operator=msg.sender;treasury=feeAccount;require(feeAccount!=address(0),"treasury");
  for(uint256 i;i<members.length;i++){address m=members[i];require(m!=address(0)&&m!=feeAccount&&!member[m],"member");member[m]=true;balance[m]=1000000000;}
 }
 function settle(bytes32 id,address seller,address buyer,uint256 microKwh,uint256 amount,uint256 fee) external {
  require(msg.sender==operator,"operator");require(!settled[id],"duplicate");
  require(member[seller]&&member[buyer]&&seller!=buyer,"participants");
  require(microKwh>0&&amount>0,"zero");require(balance[buyer]>=amount+fee,"funds");
  settled[id]=true;balance[buyer]-=amount+fee;balance[seller]+=amount;balance[treasury]+=fee;
  emit Settled(id,seller,buyer,microKwh,amount,fee);
 }
}
