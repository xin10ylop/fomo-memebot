"""rpc_route.py: the readings' second endpoint (runbook 5av). When ALCHEMY_READ_URL is set (a free Alchemy key of its own, never the
engine's, in the cloud environment's settings, never in the chat), the per-block and per-transaction reads go there under a shared
client-side rate limit (ALCHEMY_RPS, default 20 a second, the free plan allowing 25); the log searches stay on the public node,
whose block ranges Alchemy's free plan limits. Unset, everything goes to the public node exactly as before."""
import os, threading, time
PUBLIC = "https://rpc.mainnet.chain.robinhood.com"
READ = os.environ.get("ALCHEMY_READ_URL") or None
RPS = float(os.environ.get("ALCHEMY_RPS", "20") or 20)
_lock = threading.Lock(); _next = [0.0]


_bad = [0]


def routed(method):
    """True when this method goes to the second endpoint"""
    return bool(READ) and _bad[0] < 3 and method != "eth_getLogs"


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


def url(method, default):
    return READ if routed(method) else default


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
