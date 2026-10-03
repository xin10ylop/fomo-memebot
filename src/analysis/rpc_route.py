"""rpc_route.py: the readings' second endpoint (runbook 5av). When ALCHEMY_READ_URL is set (a free Alchemy key of its own, never the
engine's, in the cloud environment's settings, never in the chat), the per-block and per-transaction reads go there under a shared
client-side rate limit (ALCHEMY_RPS, default 20 a second, the free plan allowing 25); the log searches stay on the public node,
whose block ranges Alchemy's free plan limits. Unset, everything goes to the public node exactly as before."""
import os, threading, time, contextlib
PUBLIC = "https://rpc.mainnet.chain.robinhood.com"
READ = os.environ.get("ALCHEMY_READ_URL") or None
RPS = float(os.environ.get("ALCHEMY_RPS", "20") or 20)
_lock = threading.Lock(); _next = [0.0]


_bad = [0]


LOGS_MAX = int(os.environ.get("ALCHEMY_LOGS_MAX", "1500") or 1500)   # a log search spanning more blocks than this stays on the public node (the free plan's range limit is 2,000)
public_gate = threading.Semaphore(3); nogate = contextlib.nullcontext()   # the public node throttles past three requests in flight: every call to it waits here


def _span(params):
    try:
        f = params[0]; lo = f.get("fromBlock"); hi = f.get("toBlock")
        if isinstance(lo, str) and isinstance(hi, str) and lo.startswith("0x") and hi.startswith("0x"):
            return int(hi, 16) - int(lo, 16) + 1
    except Exception:
        pass
    return 10 ** 9                                                    # 'latest', a tag, or no range: not routed


def routed(method, params=None):
    """True when this call goes to the second endpoint: every block and transaction read; a log search only when its block range
    is short (the per-launch searches), never the long factory scans"""
    if not READ or _bad[0] >= 3:
        return False
    if method != "eth_getLogs":
        return True
    return params is not None and _span(params) <= LOGS_MAX


def failed():
    """a request to the second endpoint failed; after three in a row the rest of the run uses the public node (a rotated key,
    a quota spent: the reading still completes)"""
    _bad[0] += 1
    if _bad[0] == 3:
        import sys
        print("rpc_route: the second endpoint failed three times in a row; the public node for the rest of this run", file=sys.stderr, flush=True)


def worked():
    if _bad[0] < 3:
        _bad[0] = 0


def url(method, default, params=None):
    return READ if routed(method, params) else default


def params_of(payload):
    return (payload[0] if isinstance(payload, list) and payload else payload).get("params")


def throttle(n=1):
    """reserve n requests on the second endpoint's budget, sleeping until they fit"""
    if not READ:
        return
    with _lock:
        now = time.monotonic(); at = max(now, _next[0]); _next[0] = at + n / RPS
    if at > now:
        time.sleep(at - now)


def method_of(payload):
    return (payload[0] if isinstance(payload, list) and payload else payload).get("method", "")
