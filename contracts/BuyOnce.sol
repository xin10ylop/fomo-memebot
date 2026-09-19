// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// BuyOnce (third relay): buys on a Pons V2 curve at most once per curve, from ETH it holds, on the order of any of the
/// owner's shooter wallets, in a block whose clock second is at or before a deadline.
///
/// The engine fires several shots at one launch because the next block's opening is not known to the millisecond. One
/// wallet's consecutive nonces on parallel sockets can be refused as "nonce too high" when the sequencer is under load
/// (Sep 19 08:53: 29 of 35 shots), so every shot now comes from its own shooter wallet, which holds gas only: no shot
/// depends on another. The stake sits in this contract (deposit: plain transfer; withdraw: owner). The first shot to reach
/// the curve past the tax second buys with the contract's ETH and sends the tokens to the owner wallet; every later shot
/// reverts here (`bought`) or on the deadline (`TooLate`) for a cent of gas. The exit (approve, sell) is the owner
/// wallet's as before. The owner can pull back any ETH or token.
contract BuyOnce {
    address public immutable owner;
    mapping(address => bool) public bought;
    mapping(address => bool) public shooters;

    error NotOwner();
    error NotShooter(address sender);
    error AlreadyBought(address curve);
    error TooLate(uint256 blockTime, uint256 deadline);
    error Insufficient(uint256 balance, uint256 needed);

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {}

    function setShooters(address[] calldata list, bool on) external {
        if (msg.sender != owner) revert NotOwner();
        for (uint256 i = 0; i < list.length; i++) {
            shooters[list[i]] = on;
        }
    }

    /// One buy per curve, from this contract's ETH, only in a block whose clock second is at or before `deadline` (0 = none).
    function buy(address curve, uint256 amountIn, uint256 minOut, uint256 deadline) external {
        if (msg.sender != owner && !shooters[msg.sender]) revert NotShooter(msg.sender);
        if (deadline != 0 && block.timestamp > deadline) revert TooLate(block.timestamp, deadline);
        if (bought[curve]) revert AlreadyBought(curve);
        if (address(this).balance < amountIn) revert Insufficient(address(this).balance, amountIn);
        bought[curve] = true;
        (bool ok, bytes memory ret) = curve.call{value: amountIn}(abi.encodeWithSelector(0x59a87bc1, amountIn, minOut, owner));
        if (!ok) {
            assembly {
                revert(add(ret, 32), mload(ret))      // the curve's own error, unchanged (0x71c4efed(offered, minOut) in the tax second)
            }
        }
    }

    /// ETH back to the owner (amount 0 = everything).
    function withdraw(uint256 amount) external {
        if (msg.sender != owner) revert NotOwner();
        (bool s, ) = owner.call{value: amount == 0 ? address(this).balance : amount}("");
        require(s, "withdraw");
    }

    /// Any ERC20 that ended up here, back to the owner.
    function sweep(address token) external {
        if (msg.sender != owner) revert NotOwner();
        uint256 bal = IERC20(token).balanceOf(address(this));
        (bool s, bytes memory r) = token.call(abi.encodeWithSelector(0xa9059cbb, owner, bal));
        require(s && (r.length == 0 || abi.decode(r, (bool))), "sweep");
    }
}

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
}
