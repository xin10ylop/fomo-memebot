def tax_bps_of_current(sel, words):
    if sel.hex() != "f85f8e41" or len(words) <= 13:
        return None
    v = int.from_bytes(words[13], "big")
    return v if v <= 2000 else None


def tax_bps_of(sel, words):
    """the token's own tax in basis points, from the creation calldata of selector f85f8e41: field 6 of the launch struct whose
    offset is word 0 (always 0xe0 = 224 so far, i.e. the struct head starts at word 7 and the tax is word 13). 0 = the 1% tier,
    100 = 2%, 200 = 3%. Matched the Buy event's tax word on 630 of 630 launches Sep 19-23. None for another selector or layout:
    the gates then fail closed."""
    if sel.hex() != "f85f8e41" or len(words) < 14:
        return None
    off = int.from_bytes(words[0], "big")
    if off % 32 or not 7 <= off // 32 <= len(words) - 7:
        return None
    v = int.from_bytes(words[off // 32 + 6], "big")
    return v if v <= 2000 else None


if __name__ == "__main__":
    import json
    C = json.load(open("txcache.json")); n = same = 0
    for h, t in C.items():
        data = bytes.fromhex(t["input"][2:]); sel = data[:4]
        if sel.hex() != "f85f8e41": continue
        words = [data[4 + 32 * i: 4 + 32 * (i + 1)] for i in range((len(data) - 4) // 32)]
        n += 1; same += tax_bps_of(sel, words) == tax_bps_of_current(sel, words)
    print("f85f8e41 creations", n, "identical output", same)
