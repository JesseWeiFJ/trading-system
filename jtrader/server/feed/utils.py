#!/usr/bin/env python
# -*- coding: utf-8 -*-


def transform_bar_frequency(bar_df, sample_frequency):
    def trans_rule(freq):
        if freq.endswith('m'):
            return freq[:-1] + 'T'
        return freq

    symbol = bar_df['symbol'].iloc[0]
    bar_df.index = bar_df['datetime']
    bar_resample = bar_df['close'].resample(trans_rule(sample_frequency)).ohlc()
    bar_resample['volume'] = bar_df['volume'].resample(trans_rule(sample_frequency)).sum()
    bar_resample['symbol'] = symbol
    bar_resample['datetime'] = bar_resample.index
    bar_resample['frequency'] = sample_frequency
    bar_resample = bar_resample.dropna(how='any', axis=0)
    return bar_resample
