# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.4] - 2025-09-25

### Changed

- The signature of placing orders due to the latest change in Zex server.


## [0.4.3] - 2025-09-17

### Fixed

- The fields of `TradeInfo` data type to match the server response. It now includes: `amount, base_token, id, maker_order_id, name, price, quote_token, t, taker_order_id`.


## [0.4.2] - 2025-09-15

### Fixed

- The fields of `Order` data type to match the server response. It now includes: `amount, base_token, id, name, nonce, price, quote_token, t`.


## [0.4.1] - 2025-09-14

### Changed

- The name of the cancel batch order method to `cancel_batch_order`.
- The argument passed to `cancel_batch_order` method from signed order bytes to a `CancelOrderRequest` object.

## [0.4.0] - 2025-09-14

### Added

- Signing visitor classes to sign orders for Zex.

### Changed

- The signatures for development version of the Zex exchange.


## [0.3.0] - 2025-08-20

### Added

- Make possible to use both dev and main version of Zex exchange via `testnet` config.


## [0.2.0] - 2025-08-07

### Added

- `start` and `stop` methods for websockets to be able to manage in a more fine-tuned manner.


## [0.1.0] - 2025-07-26

### Added

- Place order and cancel order functionalities.
- Ability to register user accounts.
- Ability to query account balances and informations.
- Ability to deposit and withdraw assets.
- Live execution reports.
- Ability to retrieve market informations.
