# 🔁 zex-sdk

A **Python SDK for the Zex Exchange** – a decentralized exchange (DEX) designed to deliver the **speed, usability, and reliability of centralized exchanges (CEXs)** while preserving the **security and control of a DEX**.

`zex-sdk` provides a seamless interface to interact with Zex Exchange's API, including essential trading, balance management, and live socket streaming capabilities.

---

## 🚀 Features

- 📥 Place and cancel orders (single or batch)
- 🧾 Register user accounts
- 💰 Query account balances and user information
- 📈 Retrieve live market prices
- 🔄 Deposit and withdraw assets
- 🔔 Live execution reports via WebSocket stream

---

## 📦 Installation

Install directly from PyPI:

```bash
pip install zex-sdk
```

---

## ⚡ Quick Start

Here's how to get started with the async Zex client in just a few lines of code.

```python
import asyncio
from zex.sdk import AsyncClient

async def main():
    # Create a Zex client instance (testnet is True by default)
    client = await AsyncClient.create(api_key="your-api-key")

    # Example: get the price of ETH/USDT
    price = await client.get_price("ETH-USDT")
    print("Current price:", price)

asyncio.run(main())
```

> Note: Use `AsyncClient.create(...)` instead of the constructor. It handles registration and setup for you.

---

## 📘 Usage Examples

Here are some common usage examples using the `AsyncClient` and `ZexSocketManager`.

---

### ✅ Place a Batch of Orders

```python
from zex_sdk.models import PlaceOrderRequest, OrderSide

orders = [
    PlaceOrderRequest(
        base_token="ETH",
        quote_token="USDT",
        side=OrderSide.BUY,
        volume=0.5,
        price=1900.0
    ),
    PlaceOrderRequest(
        base_token="BTC",
        quote_token="USDT",
        side=OrderSide.SELL,
        volume=0.1,
        price=30000.0
    ),
]

await client.place_batch_order(orders)
```

---

### ❌ Cancel a Batch of Orders

```python

# Suppose you have stored signed orders
signed_orders = [...] # List[bytes]

await client.cancel_batch_order(signed_orders)
```

---

### 📈 Get Current Market Price

```python
price = await client.get_price("ETH-USDT")
print("ETH price:", price)
```

---

### 🔔 Listen to Execution Reports in Real-Time

```python
from zex_sdk.socket import ZexSocketManager

async def on_execution_report(message):
    print("Execution report received:", message)

socket_manager = ZexSocketManager(client)

# Use async context manager to open and manage the socket
async with await socket_manager.execution_report_socket(on_execution_report):
await asyncio.sleep(60) # keep listening for 60 seconds
```
