from dataclasses import dataclass


@dataclass
class WithdrawRequest:
    token_chain: str
    token_name: str
    amount: str
    destination: str
