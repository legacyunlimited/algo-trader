import random

def orb_signal():
    return random.choice(["LONG", "SHORT", None])

def vwap_signal():
    return random.choice(["LONG", "SHORT", None])
