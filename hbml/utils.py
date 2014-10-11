from functools import lru_cache
import html


def memoized_property(func):
    'memoize property'
    return property(lru_cache(maxsize=None)(func))


def html_escape(s):
    return html.escape(s)
