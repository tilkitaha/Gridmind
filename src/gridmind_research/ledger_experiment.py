"""Local EVM settlement and independently verifiable signed SQLite parity."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path

import numpy as np
import torch
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from eth_tester import EthereumTester, PyEVMBackend
from web3 import EthereumTesterProvider, Web3

from .battery import load_episodes
from .learned_control import Policy, rollout


def stream():
    s = torch.load("results/extension/models/MAPPO_seed11.pt", weights_only=True)
    m = Policy("MAPPO")
    m.load_state_dict(s["state_dict"])
    eps = load_episodes("test")
    _, records = rollout(m, eps)
    rows = []
    for k, ep in enumerate(eps):
        for t, d in enumerate(records):
            v = d["pin"][k].sum()
            if v <= 1e-9:
                continue
            for i in range(6):
                for j in range(6):
                    q = d["pout"][k, i] * d["pin"][k, j] / v
                    if q < 1e-6:
                        continue
                    amount = round(q * ((d["buy"][k] + 0.08) / 2 - 0.01) * 1e6)
                    if amount <= 0:
                        continue
                    r = {
                        "sequence": len(rows),
                        "start": ep["start"],
                        "interval": t,
                        "seller": i,
                        "buyer": j,
                        "micro_kwh": round(q * 1e6),
                        "amount": amount,
                        "fee": round(q * 0.02 * 1e6),
                    }
                    r["id"] = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
                    rows.append(r)
                    if len(rows) == 64:
                        return rows
    return rows


def main():
    out = Path("results/extension")
    rows = stream()
    assert len(rows) == 64
    (out / "settlement_stream.json").write_text(json.dumps(rows, indent=2))
    compiled = json.loads(Path("contracts/compiled.json").read_text())
    c = compiled["contract"]
    w = Web3(EthereumTesterProvider(EthereumTester(backend=PyEVMBackend())))
    op = w.eth.accounts[0]
    members = w.eth.accounts[1:7]
    treasury = w.eth.accounts[7]
    f = w.eth.contract(abi=c["abi"], bytecode=c["evm"]["bytecode"]["object"])
    deploy = w.eth.wait_for_transaction_receipt(
        f.constructor(members, treasury).transact({"from": op})
    )
    contract = w.eth.contract(address=deploy.contractAddress, abi=c["abi"])

    def call(r, who=op):
        return w.eth.wait_for_transaction_receipt(
            contract.functions.settle(
                bytes.fromhex(r["id"]),
                members[r["seller"]],
                members[r["buyer"]],
                r["micro_kwh"],
                r["amount"],
                r["fee"],
            ).transact({"from": who, "gas": 400000})
        )

    def balances():
        return [contract.functions.balance(a).call() for a in members + [treasury]]

    expected = [1000000000] * 6 + [0]
    receipts = []
    times = []
    for r in rows:
        start = time.perf_counter()
        receipt = call(r)
        times.append((time.perf_counter() - start) * 1000)
        assert receipt.status == 1
        expected[r["buyer"]] -= r["amount"] + r["fee"]
        expected[r["seller"]] += r["amount"]
        expected[6] += r["fee"]
        receipts.append(
            {
                "sequence": r["sequence"],
                "tx_hash": receipt.transactionHash.hex(),
                "block": receipt.blockNumber,
                "gas": receipt.gasUsed,
                "status": receipt.status,
            }
        )
    assert balances() == expected and sum(expected) == 6000000000
    tests = {}

    def reject(name, r, who=op):
        before = balances()
        rc = call(r, who)
        assert rc.status == 0 and balances() == before
        tests[name] = True

    base = rows[0]
    reject("duplicate", base)
    reject("unauthorized", {**base, "id": "aa" * 32}, members[0])
    reject("insufficient_funds", {**base, "id": "bb" * 32, "amount": 10**15})
    reject("self_trade", {**base, "id": "cc" * 32, "seller": base["buyer"]})
    reject("zero_energy", {**base, "id": "dd" * 32, "micro_kwh": 0})
    reject("zero_amount", {**base, "id": "ee" * 32, "amount": 0})
    assert not contract.functions.settled(bytes.fromhex("bb" * 32)).call()
    tests["failed_id_not_consumed"] = True
    p = out / "signed_settlements.sqlite"
    p.unlink(missing_ok=True)
    db = sqlite3.connect(p)
    db.execute("PRAGMA synchronous=FULL")
    db.execute("CREATE TABLE ledger(id TEXT PRIMARY KEY,payload TEXT,signature BLOB)")
    db.execute("CREATE TABLE balances(house INTEGER PRIMARY KEY,amount INTEGER CHECK(amount>=0))")
    db.executemany("INSERT INTO balances VALUES (?,?)", enumerate([1000000000] * 6 + [0]))
    db.commit()
    key = Ed25519PrivateKey.generate()
    public = key.public_key()
    (out / "ledger_public_key.hex").write_text(
        public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    )
    dt = []

    def store(r):
        payload = json.dumps(r, sort_keys=True)
        sig = key.sign(payload.encode())
        public.verify(sig, payload.encode())
        with db:
            if r["seller"] == r["buyer"] or r["micro_kwh"] <= 0 or r["amount"] <= 0:
                raise ValueError("Invalid trade")
            db.execute("INSERT INTO ledger VALUES (?,?,?)", (r["id"], payload, sig))
            db.execute(
                "UPDATE balances SET amount=amount-? WHERE house=?",
                (r["amount"] + r["fee"], r["buyer"]),
            )
            db.execute(
                "UPDATE balances SET amount=amount+? WHERE house=?", (r["amount"], r["seller"])
            )
            db.execute("UPDATE balances SET amount=amount+? WHERE house=6", (r["fee"],))

    for r in rows:
        start = time.perf_counter()
        store(r)
        dt.append((time.perf_counter() - start) * 1000)
    for _, payload, sig in db.execute("SELECT * FROM ledger"):
        public.verify(sig, payload.encode())
    try:
        store(rows[0])
        raise AssertionError("Duplicate accepted")
    except sqlite3.IntegrityError:
        tests["sqlite_duplicate"] = True
    try:
        store({**base, "id": "ff" * 32, "amount": 10**15})
        raise AssertionError("Overspend accepted")
    except sqlite3.IntegrityError:
        tests["sqlite_overspend_rollback"] = True
    payload, sig = db.execute("SELECT payload,signature FROM ledger LIMIT 1").fetchone()
    try:
        public.verify(sig, (payload + " ").encode())
        raise AssertionError("Tamper accepted")
    except InvalidSignature:
        tests["signature_tamper"] = True
    assert [r[0] for r in db.execute("SELECT amount FROM balances ORDER BY house")] == expected
    assert db.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 64
    db.close()
    result = {
        "stream_count": 64,
        "exact_balance_parity": True,
        "balances": expected,
        "deployment_gas": deploy.gasUsed,
        "settlement_gas_total": sum(r["gas"] for r in receipts),
        "gas_median": float(np.median([r["gas"] for r in receipts])),
        "evm_local_median_ms": float(np.median(times)),
        "sqlite_local_median_ms": float(np.median(dt)),
        "tests": tests,
        "compiler": compiled["compiler"],
        "scope": "Local single-process PyEVM; no distributed consensus or real money. Operator remains trusted for metering. Signatures need a separately trusted public key. Timings are one local pass, not public-chain finality or throughput.",
    }
    (out / "ledger_results.json").write_text(json.dumps(result, indent=2))
    (out / "ledger_receipts.json").write_text(json.dumps(receipts, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
