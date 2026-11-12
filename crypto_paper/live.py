"""Kraken public transport and host acceptance gates."""
import asyncio
import random
import socket
import struct
import threading
import time
import urllib.request

from .data import D, MAX_FRAME, NANO, SYMBOL, dump, load
from .runtime import check, versions

WS = "wss://ws.kraken.com/v2"
REST = "https://api.kraken.com/0/public/"
PAIR = "XXBTZUSD"
NTP_HOSTS = ("time.cloudflare.com", "time.google.com", "time.windows.com")


def public(path):
    with urllib.request.urlopen(REST + path, timeout=5) as stream:
        data = stream.read(2*MAX_FRAME+1)
    if len(data) > 2*MAX_FRAME:
        raise ValueError("oversized public REST payload")
    return data


def ntp(host):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(3)
        sock.connect((host, 123))
        t0, m0 = time.time_ns(), time.monotonic_ns()
        seconds, ns = divmod(t0, NANO)
        token = struct.pack("!II", seconds + 2208988800, ns*2**32//NANO)
        sock.send(bytes([0x23])+bytes(39)+token)
        data = sock.recv(512)
        t3, m3 = time.time_ns(), time.monotonic_ns()
    if (len(data) < 48 or data[0] >> 6 == 3 or data[0]&7 != 4 or
            not 1 <= data[1] <= 15 or data[24:32] != token or
            abs((t3-t0)-(m3-m0)) > 500_000_000 or m3-m0 > 500_000_000):
        raise ValueError("invalid NTP reply or round trip")
    def timestamp(start):
        seconds, fraction = struct.unpack_from("!II", data, start)
        if not seconds:
            raise ValueError("missing NTP timestamp")
        return (seconds-2208988800)*NANO + fraction*NANO//2**32
    return D((timestamp(32)-t0)+(timestamp(40)-t3))/2_000_000


async def network(call, *args):
    loop = asyncio.get_running_loop()
    result = loop.create_future()

    def deliver(value, error):
        if not result.done():
            if error:
                result.set_exception(value)
            else:
                result.set_result(value)

    def worker():
        try:
            value = call(*args)
            error = False
        except Exception as exc:
            value, error = exc, True
        if not loop.is_closed():
            loop.call_soon_threadsafe(deliver, value, error)

    # DNS lookup can outlive a socket timeout. Bound the host gate independently.
    threading.Thread(target=worker, daemon=True).start()
    return await asyncio.wait_for(result, 8)


async def clock_sample(emit):
    results = await asyncio.gather(*(network(ntp, host) for host in NTP_HOSTS),
                                   return_exceptions=True)
    samples = [str(value) for value in results if not isinstance(value, BaseException)]
    emit("clock", offset_ms=samples,
         references={host: repr(result) for host, result in zip(NTP_HOSTS, results)})
    return [D(value) for value in samples]


def preflight(session, capture):
    from queue import Empty, Queue
    queue = Queue()
    calls = {host:(ntp,host) for host in NTP_HOSTS} | {"Time":(public,"Time")}

    def probe(key, call, arg):
        try:
            queue.put((key,call(arg)))
        except Exception as exc:
            queue.put((key,exc))

    for key,(call,arg) in calls.items():
        threading.Thread(target=probe,args=(key,call,arg),daemon=True).start()
    results = {}
    deadline = time.monotonic()+8
    for _ in calls:
        try:
            key,value = queue.get(timeout=max(0,deadline-time.monotonic()))
            results[key] = value
        except Empty:
            break
    samples = [str(results[host]) for host in NTP_HOSTS if isinstance(results.get(host),D)]
    session.handle(capture.put("clock",offset_ms=samples,
                               references={host:repr(results.get(host,"timeout")) for host in NTP_HOSTS}))
    problems = []
    try:
        from .engine import Ledger
        probe_path = capture.out/"storage-probe.sqlite3"
        probe = Ledger(probe_path)
        probe.close()
        probe = Ledger(probe_path)
        try:
            if not probe.reconcile():
                raise ValueError("storage reconciliation")
        finally:
            probe.close()
    except Exception as exc:
        problems.append(f"local SQLite close/reopen rejected: {exc}")
    if not session.clock:
        problems.append("independent UTC reference rejected: " + str(samples))
    wire = results.get("Time")
    try:
        if not isinstance(wire,bytes):
            raise ValueError(repr(wire) if wire else "timeout")
        answer = load(wire)
        if answer["error"] or type(answer["result"]["unixtime"]) is not int:
            raise ValueError("invalid Kraken Time")
        session.handle(capture.put("time",wire))
    except (ValueError,KeyError) as exc:
        session.handle(capture.put("rest_error",reason=str(exc),request="Time"))
        problems.append(f"Kraken public Time: {exc}")
    env = versions()
    if env["websockets"] != "15.0.1":
        problems.append("websockets==15.0.1 missing from current environment")
    if env["python"].split(".")[:2] != ["3","12"]:
        problems.append("Python 3.12 required")
    return problems


async def wait_utc(target):
    while (now := time.time_ns()) < target:
        # asyncio's monotonic timer can pause while the host is suspended.
        await asyncio.sleep(min(1, (target-now)/NANO))
    return now


async def sample_window(start, finish, emit):
    tick = start
    while tick < finish:
        utc = await wait_utc(tick)
        if utc >= finish:
            return
        emit(utc)
        tick = start + ((utc-start)//NANO+1)*NANO
    await wait_utc(finish)


async def candle_window(interval, started, finish, boundaries, fetch, emit):
    span = interval*60
    end = (started//(span*NANO)+1)*span
    while end*NANO <= finish:
        due, deadline = (end+2)*NANO, (end+60)*NANO
        while due <= deadline and (interval, end) not in boundaries:
            utc = await wait_utc(due)
            if utc > deadline:
                break
            await fetch(end)
            due += ((utc-due)//(5*NANO)+1)*5*NANO
        if (interval, end) not in boundaries:
            utc = await wait_utc(deadline)
            emit("deadline", interval=interval, end=end, utc=utc)
        end += span


async def live(session, capture, duration, forced_at):
    def emit(kind, wire=b"", **fields):
        frame = capture.put(kind, wire, **fields)
        session.handle(frame)

    from websockets.asyncio.client import connect
    from websockets.exceptions import WebSocketException

    started = time.time_ns()
    finish = started + duration*NANO
    emit("run_begin", utc=started, duration=duration)
    force_due = started + forced_at*NANO if forced_at is not None else None
    forced = False
    warm = asyncio.Event()
    epoch = session.book.epoch
    stop_file = capture.out / "STOP"

    async def periodic_clock():
        while True:
            await asyncio.sleep(50)
            await clock_sample(emit)

    def sample(utc):
        emit("sample", utc=utc)
        if stop_file.exists():
            emit("operator", action="stop", note=stop_file.read_text(encoding="utf-8").strip() or "STOP file")
            stop_file.unlink()

    async def candles(interval):
        async def fetch(end=None):
            try:
                wire = await network(public, f"OHLC?pair=XBTUSD&interval={interval}")
            except (OSError, ValueError) as exc:
                emit("rest_error", reason=str(exc), request="OHLC", interval=interval, end=end)
            else:
                emit("ohlc", wire, interval=interval, end=end, pair=PAIR)

        await fetch()
        await candle_window(interval, started, finish, session.boundaries, fetch, emit)

    async def rewarm():
        while True:
            await warm.wait()
            warm.clear()
            for interval in (240, 1440):
                try:
                    wire = await network(public, f"OHLC?pair=XBTUSD&interval={interval}")
                except (OSError, ValueError) as exc:
                    emit("rest_error", reason=str(exc), request="warmup", interval=interval)
                else:
                    emit("ohlc", wire, interval=interval, end=None, pair=PAIR)

    async def connection():
        nonlocal epoch, forced
        failures = 0
        while True:
            epoch += 1
            emit("connect", epoch=epoch)
            trigger = {}
            had_ready = False
            try:
                async with connect(WS, max_size=MAX_FRAME, max_queue=16, open_timeout=8,
                                   ping_interval=None, close_timeout=1) as ws:
                    for params in ({"channel": "instrument", "snapshot": True},
                                   {"channel": "book", "symbol": [SYMBOL], "depth": 10, "snapshot": True}):
                        await ws.send(dump({"method": "subscribe", "params": params}))
                    if epoch > 1:
                        warm.set()
                    queue = asyncio.Queue(4096)
                    pending_bytes = 0

                    async def read_frames():
                        nonlocal pending_bytes
                        while True:
                            wire = await asyncio.wait_for(ws.recv(decode=False), 5)
                            if queue.full() or pending_bytes+len(wire) > 32*MAX_FRAME:
                                raise OverflowError("WS queue overflow")
                            pending_bytes += len(wire)
                            queue.put_nowait((wire, time.monotonic_ns(), time.time_ns()))
                            await asyncio.sleep(0)

                    reader = asyncio.create_task(read_frames())
                    try:
                        while True:
                            if reader.done():
                                reader.result()
                            if force_due is not None and not forced and (utc := time.time_ns()) >= force_due:
                                trigger = {"force_utc":utc, "force_mono":time.monotonic_ns()}
                                forced = True
                                break
                            try:
                                wire, queued, queued_utc = await asyncio.wait_for(queue.get(), .25)
                            except TimeoutError:
                                continue
                            pending_bytes -= len(wire)
                            if time.monotonic_ns()-queued > 500_000_000:
                                raise OverflowError("WS queue too old")
                            try:
                                obj = load(wire)
                                channel = obj.get("channel","control")
                                event_time = obj["data"][0]["timestamp"] if channel == "book" else None
                            except (ValueError,KeyError,IndexError,TypeError,AttributeError):
                                channel,event_time = "unknown",None
                            emit("ws", wire, epoch=epoch, channel=channel,
                                 queue_received_mono=queued, queue_received_utc=queued_utc, exchange_utc=event_time)
                            had_ready |= session.ready(session.last)
                            if session.book.state == "STALE":
                                raise ValueError("book STALE")
                            # A ready queue.get() need not yield while synchronous commits drain a burst.
                            await asyncio.sleep(0)
                    finally:
                        reader.cancel()
                        await asyncio.gather(reader, return_exceptions=True)
                reason = "induced disconnect"
            except (OSError, ValueError, TimeoutError, WebSocketException, OverflowError) as exc:
                if isinstance(exc, OverflowError):
                    emit("overflow", epoch=epoch, reason=str(exc))
                reason = str(exc) or type(exc).__name__
            emit("disconnect", epoch=epoch, reason=reason, forced=bool(trigger), **trigger)
            if had_ready:
                failures = 0
            delay = min(30, 2**min(failures, 5)*random.uniform(1, 1.25))
            failures += 1
            await asyncio.sleep(delay)

    async with asyncio.TaskGroup() as tasks:
        background = [tasks.create_task(task()) for task in (connection, periodic_clock, rewarm)]
        sampler = tasks.create_task(sample_window(started, finish, sample))
        candle_tasks = [tasks.create_task(candles(i)) for i in (240, 1440)]
        await sampler
        await asyncio.gather(*candle_tasks)
        for task in background:
            task.cancel()
    return "DONE", "collection finished"


def host_checks(session, status, reason, duration, forced_at):
    metrics = session.metrics()
    expected = {"duration_sec": 86400, "forced_at_sec": 21600, "ready_fraction_min": ".99",
                "p95_age_ms_max": 1000, "p99_age_ms_max": 2000, "resync_ms_max": 15000,
                "timely_bars_min": 5, "bar_boundaries": 6}
    force_due = session.run_begin + 21600*NANO if session.run_begin is not None else None
    force_on_time = (force_due is not None and session.force_utc is not None
                     and force_due <= session.force_utc < force_due+NANO)
    status = ("BLOCKED" if status != "DONE" or duration != 86400 or forced_at != 21600 else
              "PASS" if force_on_time and metrics["expected_seconds"] == 86400 and
              metrics["ready_seconds"] >= 86400*.99 and
              metrics["p95_age_ms"] is not None and metrics["p95_age_ms"] <= 1000 and
              metrics["p99_age_ms"] <= 2000 and metrics["resync_ms"] is not None and
              metrics["resync_ms"] <= 15000 and metrics["bar_boundaries"] == 6 and
              metrics["timely_bars"] >= 5 else "FAIL")
    return check("T01", status, expected, metrics | {"collection": reason, "force_on_time":force_on_time})
