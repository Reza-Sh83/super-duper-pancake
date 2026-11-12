"""Diagnostics run separately from the product's acceptance criteria."""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import socket
import sqlite3
import time
import unittest

from crypto_paper.data import Book, D, dump, load
from crypto_paper.engine import Ledger
from crypto_paper.live import NTP_HOSTS, WS, ntp, public
from crypto_paper.runtime import CAP, MIB, check, report, versions
from crypto_paper.verify import Fixtures


def wss():
    from websockets.asyncio.client import connect

    async def subscribe():
        async with asyncio.timeout(12):
            async with connect(WS, open_timeout=8, close_timeout=1) as ws:
                await ws.send(dump({"method":"subscribe","params":{"channel":"book",
                                    "symbol":["BTC/USD"],"depth":10,"snapshot":True}}))
                book = Book()
                book.connect(1)
                while True:
                    message = load(await ws.recv())
                    if message.get("success") is False:
                        raise ValueError(str(message))
                    if message.get("channel") == "book" and message.get("type") == "snapshot":
                        book.apply(1,1,message)
                        return {"endpoint":WS,"checksum":message["data"][0]["checksum"],
                                "state":book.state}
    return asyncio.run(subscribe())


def storage(path, *, create=False):
    db = sqlite3.connect(path)
    try:
        mode = db.execute("PRAGMA journal_mode=PERSIST").fetchone()[0]
        db.execute("PRAGMA synchronous=FULL")
        if create:
            db.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY, amount INTEGER NOT NULL)")
            db.execute("INSERT INTO probe VALUES (1, 42)")
            db.commit()
            db.execute("UPDATE probe SET amount=0")
            db.rollback()
        value, = db.execute("SELECT amount FROM probe WHERE id=1").fetchone()
        integrity, = db.execute("PRAGMA integrity_check").fetchone()
        if (mode, value, integrity) != ("persist",42,"ok"):
            raise ValueError((mode,value,integrity))
        return {"journal":mode,"committed":value,"integrity":integrity}
    finally:
        db.close()


def preflight(out, started):
    out.mkdir(parents=True,exist_ok=False)
    checks = []

    def test(identity, expected, call):
        try:
            observed = call()
            return check(identity,"PASS",expected,observed)
        except Exception as exc:
            return check(identity,"BLOCKED",expected,repr(exc))

    def dns():
        return {host:sorted({item[4][0] for item in socket.getaddrinfo(host,443)})
                for host in ("api.kraken.com","ws.kraken.com",*NTP_HOSTS)}

    def rest():
        value = load(public("Time"))
        if value["error"] or not isinstance(value["result"]["unixtime"],int):
            raise ValueError(str(value))
        return value

    def clocks():
        def reference(host):
            try:
                return ntp(host)
            except Exception as exc:
                return repr(exc)
        with ThreadPoolExecutor(max_workers=3) as pool:
            offsets = dict(zip(NTP_HOSTS,pool.map(reference,NTP_HOSTS),strict=True))
        samples = sorted(v for v in offsets.values() if isinstance(v,D))
        if len(samples) != 3 or abs(samples[1]) > 500 or samples[-1]-samples[0] > 250:
            raise ValueError(f"reference offsets in ms: {offsets}")
        return offsets

    def disk():
        available = shutil.disk_usage(out).free
        if available < CAP + 2048*MIB + 16*MIB:
            raise OSError(f"{available} bytes free")
        return {"free_bytes":available}

    def deps():
        actual = versions()
        if not actual["python"].startswith("3.12.") or actual["websockets"] != "15.0.1":
            raise ValueError(str(actual))
        return actual

    def sqlite():
        path = out/"independent.sqlite3"
        storage(path,create=True)
        return storage(path)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(test,*spec) for spec in (
            ("docker_dns","resolve Kraken and clock hosts",dns),
            ("docker_https","verified TLS and Kraken Time response",rest),
            ("docker_wss","verified TLS and CRC-valid BTC/USD snapshot",wss),
            ("docker_clock","three independent offsets, median ≤500 ms and span ≤250 ms",clocks),
            ("docker_disk","at least 7 GiB + 16 MiB free",disk),
            ("docker_dependency","Python 3.12 and hash-installed websockets 15.0.1",deps),
            ("docker_sqlite","transaction, rollback, close and reopen on the local volume",sqlite),
        )]
        checks = [future.result() for future in futures]
    return report(out/"report.json","docker-preflight",checks,started,{})


def seed(out):
    out.mkdir(parents=True,exist_ok=False)
    fixture = Fixtures("test_X02")
    fixture.out = out
    # Exercise the same fixture and leave its capture, manifest and filled ledger on the volume.
    fixture.capture_recovery()


def inspect(out, phase, started):
    storage_result = storage(out.parent/"preflight"/"independent.sqlite3")
    ledger = Ledger(out/"restart"/"ledger.sqlite3")
    try:
        observed = {k:ledger.state[k] for k in ("cash","btc","manual","daily","drawdown")}
        fills = ledger.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0]
        observed.update(fills=fills,reconciled=ledger.reconcile(),independent_sqlite=storage_result)
        expected = {"cash":"9848.7496","btc":"1.5","manual":True,"daily":None,
                    "drawdown":False,"fills":2,"reconciled":True}
        valid = all(observed[k] == v for k,v in expected.items())
    finally:
        ledger.close()
    return report(out/f"{phase}.json","docker-recovery",
                  [check("docker_recovery","PASS" if valid else "FAIL",expected,observed)],started,{})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase",choices=("preflight","seed","before","after"))
    parser.add_argument("out",type=Path)
    args = parser.parse_args()
    started = time.time_ns()
    if args.phase == "preflight":
        raise SystemExit(preflight(args.out,started))
    if args.phase == "seed":
        seed(args.out)
    else:
        raise SystemExit(inspect(args.out,args.phase,started))
