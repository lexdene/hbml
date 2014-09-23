from functools import lru_cache


def memoized_property(func):
    'memoize property'
    return property(lru_cache(maxsize=None)(func))
