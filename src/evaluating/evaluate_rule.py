# import numpy as np
import pandas as pd

"""
Rule Config Schema
------------------
The `config` is a hierarchical dictionary that defines how raw time-series
data is transformed, aggregated, and evaluated against specific thresholds.

config (dict):
    transforms (list[dict]): Data transformation pipeline (chain), applied in order
        {'type': 'ma',   'window': N}        - Simple moving average (SMA/MA)
        {'type': 'ema',  'window': N}        - Exponential moving average (EMA)
        {'type': 'pct_change'}               - Percentage change (growth rate)
        {'type': 'diff'}                     - Difference (delta between periods)
        {'type': 'abs'}                      - Absolute value
        {'type': 'bias', 'baseline': series} - Bias ratio vs. baseline series

    window_n   (int): Main observation window (recent N periods)
    lookback_m (int, optional): Reference window (lookback M periods = past (M-N)
                                + recent N), defaults to window_n if omitted

    aggregate (str): Method applied to windowed data
        - Scalars:
          'latest' - Latest (most recent) value (in window N)
          'mean'   - Mean (average) of the values (in window N)
          'max'    - Maximum value (in window N)
          'min'    - Minimum value (in window N)
          'sum'    - Summation of all values (in window N)
          'std'    - Standard deviation (in window N)
        - Custom metrics:
          'min_max_ratio' - Min/max ratio within window N
          'vs_past_mean'  - Growth rate of recent mean (of window N) vs. past
                            mean (of lookback M exclude window N)
        - Consecutive inspection:
          'all'   - All periods satisfy the condition (in window N)
          'any'   - At least one period satisfies the condition (in window N)
          'count' - Some periods satisfy the condition (in window N)
                    If min_matches specified and matches count < min_matches,
                    considered as failed (scores 0)
        - Signals:
          'rank'  - New high or new low (in window N) relative to lookback window M
          'cross' - Crossover signal (golden / death cross) (in window N)

    operator (str): Comparison operator
        '>', '>=', '<', '<=', '=='
    threshold (float): Comparison value (use 0.1 for 10%), scores 0 if failed
    min_matches (int, optional): Minimum number of matches required to pass (only
                                 used for 'count' aggregate)
    saturation (float, optional): Full-score threshold,
                                  Values exceeding this threshold scores 100,
                                  otherwise performs linear interpolation scoring
                                  If omitted, any passed comparison scores 100
"""


# Helpers
def _compare(value, op, threshold):
    """Apply a comparison operator between a value and a threshold.

    Centralises all operator logic so every aggregation and scoring path
    uses a single, consistent implementation.

    Args:
        value (float):
        op (str):
        threshold (float):

    Returns:
        bool:
    """
    if op == '>':
        return value > threshold
    if op == '>=':
        return value >= threshold
    if op == '<':
        return value < threshold
    if op == '<=':
        return value <= threshold
    if op == '==':
        return value == threshold

    raise ValueError(f'Error: Unknown operator: {op!r}')


# Data transformation pipeline
def _apply_transforms(series, transforms):
    """Execute data transformations in sequence

    NOTE: Data is time-indexed numeric series, sorted ascending by time.

    Args:
        series (pd.Series): Series data
        transforms (list[dict]): Transformation pipeline, see 'Rule Config Schema: transforms'

    Returns:
        pd.Series: Transformed series data
    """
    # copy data to avoid mutating source
    data = series.copy()

    # if only single transform is provided, convert to list
    if isinstance(transforms, dict):
        transforms = [transforms]

    # transform pipeline
    for step in transforms:
        tr_type = step.get('type')

        # simple moving average (SMA/MA)
        if tr_type == 'ma':
            n = step.get('window', 5)
            data = data.rolling(window=n).mean()

        # exponential moving average (EMA)
        elif tr_type == 'ema':
            n = step.get('window', 5)
            data = data.ewm(span=n, adjust=False).mean()

        # percentage change (growth rate)
        elif tr_type == 'pct_change':
            n = step.get('period', 1)
            data = data.pct_change(periods=n)

        # difference (delta between periods)
        elif tr_type == 'diff':
            n = step.get('period', 1)
            data = data.diff(periods=n)

        # sbsolute value
        elif tr_type == 'abs':
            data = data.abs()

        # bias ratio vs. baseline series
        elif tr_type == 'bias':
            base = step.get('baseline')

            # bias ratio requires a baseline; skip if absent
            if base is not None:
                # conform index
                base = base.reindex(data.index)
                data = (data - base) / base

        else:
            raise ValueError(f'Error: Unknown transform type: {tr_type!r}')

        # drop NaNs produced by transformations (e.g., rolling window) to prevent downstream errors
        data = data.dropna()

    return data


# Data aggregation
def _calc_aggregate_scalar(recent_data, lookback_data, config):
    """Reduce the windowed series to a single numeric value according to rule config

    For scalar/custom aggregates the value is later passed to the scorer.

    Args:
        recent_data (pd.Series): Series data for evaluation
        lookback_data (pd.Series, optional): Reference series data (= past_data + recent_data)
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        Optional[float]: Numeric value, or None if the computation is undefined
                         (caller will treat None as score 0)
    """
    # get rule
    agg = config.get('aggregate', 'latest')

    n = len(recent_data)

    if n == 0:
        return None

    # 1. scalar aggregates -> raw numeric value (fed to scorer later)

    # latest (most recent) value
    if agg == 'latest':
        return recent_data.iloc[-1]

    # mean (average) of the values
    if agg == 'mean':
        return recent_data.mean()

    # maximum value
    if agg == 'max':
        return recent_data.max()

    # minimum value
    if agg == 'min':
        return recent_data.min()

    # summation of all values
    if agg == 'sum':
        return recent_data.sum()

    # standard deviation
    if agg == 'std':
        return recent_data.std()

    # 2. custom aggregates -> derived numeric value (fed to scorer later)

    # range compression ratio (min/max ratio within window)
    if agg == 'min_max_ratio':
        min_v, max_v = recent_data.min(), recent_data.max()

        return 0.0 if max_v == 0 else min_v / max_v

    # comparison with past mean (growth rate of recent mean vs. past mean)
    if agg == 'vs_past_mean':
        past_only = lookback_data.iloc[: max(0, len(lookback_data) - n)]

        if past_only.empty or past_only.mean() == 0:
            return None

        recent_mean = recent_data.mean()
        past_mean = past_only.mean()

        return (recent_mean - past_mean) / abs(past_mean)

    raise ValueError(f'Error: Unknown aggregate type: {agg!r}')
    # or
    # return None


def _calc_aggregate_score(recent_data, lookback_data, config):
    """Reduce the windowed series to a single score according to rule config

    For consecutive/signal aggregates the value IS the final 0-100 score

    Args:
        recent_data (pd.Series): Series data for evaluation
        lookback_data (pd.Series, optional): Reference series data (= past_data + recent_data)
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        Optional[float]: Numeric value, or None if the computation is undefined
                         (caller will treat None as score 0)
    """
    agg = config.get('aggregate', 'latest')
    op = config.get('operator', '>')
    threshold = config.get('threshold', 0.0)

    n = len(recent_data)

    if n == 0:
        return None

    # 3. Consecutive aggregates -> 0-100 score

    # consecutive, presence, or partial (all, any, count)
    if agg in ('all', 'any', 'count'):
        matches = sum(_compare(float(x), op, threshold) for x in recent_data)

        if agg == 'all':
            return 100.0 if matches == n else 0.0

        elif agg == 'any':
            return 100.0 if matches > 0 else 0.0

        elif agg == 'count':
            min_matches = config.get('min_matches', 0)

            if matches < min_matches:
                return 0.0  # less than the minimum

            return (matches / n) * 100.0

    # 4. signal aggregates -> 0 or 100 score

    # new high/low signals (rank)
    if agg == 'rank':
        if op in ('>', '>=', 'high'):
            is_high = recent_data.max() >= lookback_data.max()

            return 100.0 if is_high else 0.0

        elif op in ('<', '<=', 'low'):
            is_low = recent_data.min() <= lookback_data.min()

            return 100.0 if is_low else 0.0

        raise ValueError(f'Error: Unknown operator type: {agg!r}')

    # crossover signals (cross)
    if agg == 'cross':
        if n < 2:
            return None

        prev_val, curr_val = recent_data.iloc[-2], recent_data.iloc[-1]

        if op in ('>', '>='):  # crossover from below (golden cross)
            is_cross = (prev_val <= threshold) and (curr_val > threshold)

            return 100.0 if is_cross else 0.0

        elif op in ('<', '<='):  # crossover from above (death cross)
            is_cross = (prev_val >= threshold) and (curr_val < threshold)

            return 100.0 if is_cross else 0.0

        raise ValueError(f'Error: Unknown operator type: {agg!r}')

    raise ValueError(f'Error: Unknown aggregate type: {agg!r}')
    # or
    # return None


# Scoring logic (value -> 0-100)
def _calc_score(val, config):
    """Linearly map aggregated value to 0-100 scores

    Args:
        val (float): Value to score
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        float: Score between 0 and 100
    """
    op = config.get('operator', '>')
    threshold = config.get('threshold', 0.0)  # pass threshold
    saturation = config.get('saturation', None)  # saturation threshold (optional)

    if val is None:
        return 0.0

    # case A: no saturation -> binary scoring (100 if passed)
    if saturation is None:
        passed = _compare(val, op, threshold)

        return 100.0 if passed else 0.0

    # case B: saturation set -> linear interpolation
    if op in ('>', '>='):
        # higher is better (e.g., revenue growth; threshold usually < saturation)
        if val <= threshold:
            return 0.0

        if val >= saturation:
            return 100.0

        # linear mapping for val between
        return (val - threshold) / (saturation - threshold) * 100.0

    elif op in ['<', '<=']:
        # lower is better (e.g., P/E ratio, debt ratio; threshold usually > saturation)
        if val >= threshold:
            return 0.0

        if val <= saturation:
            return 100.0

        # linear mapping for val between
        return (threshold - val) / (threshold - saturation) * 100.0

    # '==' with saturation is ambiguous – fall back to binary
    return 100.0 if _compare(val, op, threshold) else 0.0


# these aggregates whose output is already a final 0-100 score
# and should bypass _calc_score()
_SCORE_DIRECT_AGGS = frozenset({'all', 'any', 'count', 'rank', 'cross'})


# Main Coordinator: stock rule evaluation
def evaluate_stock_rule(series, config):
    """General stock rule evaluation function (0-100 scale).

    Step:
        1. Transform – execute configured transform pipeline (chain)
        2. Slice     – extract recent (window_n) and reference (lookback_m) windows
        3. Aggregate – reduce to a single value (or direct score)
        4. Score     – map value to [0, 100] via threshold / saturation

    Args:
        series (pd.Series): Series data (index: time, value: numeric, sorted by time)
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        float: Score between 0.0 and 100.0
    """
    # 1. execute transformation pipeline
    data = _apply_transforms(series, config.get('transforms', []))
    if data.empty:
        return 0.0

    # 2. data slicing
    n = config.get('window_n', 1)
    m = config.get('lookback_m', n)  # use window_n as default for lookback_m if absent

    if len(data) < n:
        return 0.0

    recent_data = data.iloc[-n:]
    lookback_data = data.iloc[-max(n, m) :]

    # 3. perform aggregation
    agg = config.get('aggregate', 'latest')

    if agg in _SCORE_DIRECT_AGGS:
        val = _calc_aggregate_score(recent_data, lookback_data, config)

        # direct score
        final_score = val if val is not None else 0.0
    else:
        val = _calc_aggregate_scalar(recent_data, lookback_data, config)

        # 4. scoring
        final_score = _calc_score(val, config)

    return round(final_score, 2)
