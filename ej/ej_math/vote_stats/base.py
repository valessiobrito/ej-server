import functools

import pandas as pd

from sidekick import lazy, placeholder as this


def cached(func):
    """
    Cache result of method in the _cache attribute of instance.
    """

    attribute = func.__name__

    @functools.wraps(func)
    def decorated(self, **kwargs):
        key = (attribute, *kwargs.items())
        try:
            return self._cache[key]
        except KeyError:
            self._cache[key] = result = func(self, **kwargs)
            return result

    return decorated


class VoteStats:
    """
    A class that gathers basic statistics about a Series object.
    """

    @lazy
    def filtered(self):
        data = self.data
        return data[data.index != self.skip_value]

    @lazy
    def skip(self):
        data = self.data
        filtered_data = data[data == self.skip_value]
        return self.total - self._pivot(filtered_data, aggfunc='count')

    missing = lazy(this.total - this.count)
    count = lazy(this._simple('count'))
    count_filtered = lazy(this._simple('count', True))
    average = lazy(this._simple('mean'))
    average_filtered = lazy(this._simple('mean', True))

    def __init__(self, data, *, total, cols=('item', 'value'), skip_value=0):
        self._cache = {}
        self.total = total
        self.skip_value = skip_value
        self.data = df = pd.DataFrame()

        item_col, value_col = cols
        df['item'] = data[item_col]
        df['value'] = data[value_col]

    def __len__(self):
        return len(self.data)

    def _get_data(self, filter=False):
        return self.filtered if filter else self.data

    def _pivot(self, data, **kwargs):
        return data.pivot_table('value', index='item', **kwargs)

    def _simple(self, aggfunc, filter=False):
        data = self._get_data(filter)
        return self._pivot(data, aggfunc=aggfunc)
