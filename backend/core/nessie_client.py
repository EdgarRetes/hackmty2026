"""
Thin client for the Nessie sandbox API (https://prod-api.nessieisreal.com).

Auth is a `key` query parameter on every request (confirmed live — see
NESSIE_EXPLORATION.md; the interactive docs don't reliably show this).
The key comes from the NESSIE_API_KEY env var — never hardcode it, never
log it, never include it in an exception message.

Per NESSIE_EXPLORATION.md, this sandbox is a shared pool already full of
duplicate/templated data from other users who weren't careful about
this. Calls here are deliberately minimal: create a customer/account
once and reuse the stored id on every re-seed rather than creating a new
one every run, and clean up deposits we created before recreating them.
"""

import os

import requests

BASE_URL = "https://prod-api.nessieisreal.com"
TIMEOUT = 15


def _key():
    key = os.environ.get("NESSIE_API_KEY", "")
    if not key:
        raise RuntimeError("NESSIE_API_KEY is not set in the environment.")
    return key


def _url(path):
    return f"{BASE_URL}{path}"


def create_customer(first_name, last_name, address):
    resp = requests.post(
        _url("/customers"),
        params={"key": _key()},
        json={"first_name": first_name, "last_name": last_name, "address": address},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["objectCreated"]["_id"]


def create_account(customer_id, account_type, nickname, balance, rewards=0):
    resp = requests.post(
        _url(f"/customers/{customer_id}/accounts"),
        params={"key": _key()},
        json={
            "type": account_type,
            "nickname": nickname,
            "rewards": rewards,
            "balance": balance,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["objectCreated"]["_id"]


def create_deposit(account_id, amount, transaction_date, description):
    # Nessie's Deposit.amount is documented as an integer — no cents.
    resp = requests.post(
        _url(f"/accounts/{account_id}/deposits"),
        params={"key": _key()},
        json={
            "medium": "balance",
            "transaction_date": transaction_date,
            "status": "completed",
            "amount": round(amount),
            "description": description,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["objectCreated"]["_id"]


def delete_deposit(deposit_id):
    resp = requests.delete(
        _url(f"/deposits/{deposit_id}"), params={"key": _key()}, timeout=TIMEOUT
    )
    if resp.status_code not in (200, 404):
        resp.raise_for_status()


def get_customer(customer_id):
    resp = requests.get(
        _url(f"/customers/{customer_id}"), params={"key": _key()}, timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def get_account(account_id):
    resp = requests.get(
        _url(f"/accounts/{account_id}"), params={"key": _key()}, timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()
