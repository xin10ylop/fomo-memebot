// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// BuyOnce: a relay that buys on a Pons V2 curve at most once per curve, for the engine's burst send.
///
/// The engine fires several shots at one launch because the next block's opening is not known to the millisecond.
/// Every shot goes through this contract: the first one to reach the curve past the tax second buys, every later one
/// reverts here on `bought[curve]` and costs only gas. A shot that reaches the curve too early reverts inside the
/// curve (the tax second's minOut), the whole call reverts, and `bought` stays clear for the next shot.
/// Tokens go straight to the owner wallet (the curve's recipient argument), so the exit is unchanged.
/// The owner can pull back any ETH or token that ends up here.
contract BuyOnce {
    address public immutable owner;
    mapping(address => bool) public bought;

    error NotOwner();
    error AlreadyBought(address curve);

    constructor() {
        owner = msg.sender;
    }

    /// One buy per curve. amountIn and minOut are the curve's own arguments; msg.value funds it.
    function buy(address curve, uint256 amountIn, uint256 minOut) external payable {
        if (msg.sender != owner) revert NotOwner();
        if (bought[curve]) revert AlreadyBought(curve);
        bought[curve] = true;
        (bool ok, bytes memory ret) = curve.call{value: msg.value}(abi.encodeWithSelector(0x59a87bc1, amountIn, minOut, owner));
        if (!ok) {
            assembly {
                revert(add(ret, 32), mload(ret))      // the curve's own error, unchanged (0x71c4efed(offered, minOut) in the tax second)
            }
        }
        if (address(this).balance > 0) {              // a capped buy refunded part of the value: back to the wallet
            (bool s, ) = owner.call{value: address(this).balance}("");
            require(s, "refund");
        }
    }

    receive() external payable {}

    /// Pull back ETH (token = 0) or any ERC20 that ended up here.
    function sweep(address token) external {
        if (msg.sender != owner) revert NotOwner();
        if (token == address(0)) {
            (bool s, ) = owner.call{value: address(this).balance}("");
            require(s, "sweep");
        } else {
            uint256 bal = IERC20(token).balanceOf(address(this));
            (bool s, bytes memory r) = token.call(abi.encodeWithSelector(0xa9059cbb, owner, bal));
            require(s && (r.length == 0 || abi.decode(r, (bool))), "sweep");
        }
    }
}

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
}
