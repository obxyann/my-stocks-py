from typing import Optional, Tuple

# import numpy as np
import pandas as pd

"""
Rule Config Schema
------------------
The `config` is a hierarchical dictionary that defines how raw time-series
data is transformed, aggregated, and evaluated against specific thresholds.

config (dict):
    transforms (list[dict]): Data transformation pipeline (steps), applied in order
        {'type': 'ma',   'window': N}        - Simple moving average (SMA/MA)
        {'type': 'ema',  'window': N}        - Exponential moving average (EMA)
        {'type': 'pct_change'}               - Percentage change (growth rate)
        {'type': 'diff'}                     - Difference (delta between periods)
        {'type': 'abs'}                      - Absolute value
        {'type': 'bias', 'baseline': series} - Bias ratio vs. baseline series

    window_n   (int): Main observation window (recent N periods)
    lookback_m (int, optional): Reference window (lookback M periods), defaults
                                to window_n if omitted

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


# Data transformation
def _apply_transforms(series: pd.Series, transforms: list) -> pd.Series:
    """Execute data transformations in sequence (MA, EMA, differences, growth rates, etc.).

    Args:
        series (pd.Series): Series data (index: time, value: numeric, sorted by time)
        transforms (list[dict]): Data transformation pipeline, see 'Rule Config Schema: transforms'

    Returns:
        pd.Series: Transformed series data (index: time, value: numeric, sorted by time)
    """
    # copy data to avoid mutating source
    data = series.copy()

    # if only single transform is provided, convert to list
    if isinstance(transforms, dict):
        transforms = [transforms]

    # transform pipeline
    for step in transforms:
        t_type = step.get('type')

        if t_type == 'ma':
            n = step.get('window', 5)
            data = data.rolling(window=n).mean()
        elif t_type == 'ema':
            n = step.get('window', 5)
            data = data.ewm(span=n, adjust=False).mean()
        elif t_type == 'pct_change':
            n = step.get('period', 1)
            data = data.pct_change(periods=n)
        elif t_type == 'diff':
            n = step.get('period', 1)
            data = data.diff(periods=n)
        elif t_type == 'abs':
            data = data.abs()
        elif t_type == 'bias':
            base = step.get('baseline')

            # bias ratio requires a baseline; skip if absent
            if base is not None:
                # conform index
                base = base.reindex(data.index)
                data = (data - base) / base

        # drop NaNs produced by transformations (e.g., rolling window) to prevent downstream errors
        data = data.dropna()

    return data


# Data aggregation and score in special cases
def _calculate_aggregate(
    recent_data: pd.Series, lookback_data: pd.Series, config: dict
) -> Tuple[Optional[float], Optional[float]]:
    """Calculate aggregate value according to rule config.

    Args:
        recent_data (pd.Series): Series data for evaluation
        lookback_data (pd.Series, optional): Reference series data
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        Tuple[Optional[float], Optional[float]]: (value val, score direct_score)
            - For "value-based" rules (e.g., mean, latest), returns (val, None) for subsequent scoring
            - For "score-based" rules (e.g., all, rank, cross), returns (None, score) as final result
    """
    # get rule
    agg_type = config.get('aggregate', 'latest')
    op = config.get('operator', '>')
    threshold = config.get('threshold', 0.0)

    n = len(recent_data)

    if n == 0:
        return None, 0.0

    # 1. scalar aggregation (requires subsequent linear scoring)
    if agg_type == 'latest':
        return recent_data.iloc[-1], None

    if agg_type == 'mean':
        return recent_data.mean(), None

    if agg_type == 'max':
        return recent_data.max(), None

    if agg_type == 'min':
        return recent_data.min(), None

    if agg_type == 'std':
        return recent_data.std(), None

    if agg_type == 'sum':
        return recent_data.sum(), None

    # 2. custom aggregation (requires subsequent linear scoring)

    # range compression ratio (min/max ratio within window)
    if agg_type == 'min_max_ratio':
        min_v, max_v = recent_data.min(), recent_data.max()

        return (0.0 if max_v == 0 else min_v / max_v), None

    # comparison with past mean (growth rate of recent mean vs. past mean)
    if agg_type == 'vs_past_mean':
        past_only = lookback_data.iloc[: max(0, len(lookback_data) - n)]

        if past_only.empty or past_only.mean() == 0:
            return None, 0.0

        recent_mean = recent_data.mean()
        past_mean = past_only.mean()

        val = (recent_mean - past_mean) / abs(past_mean)

        return val, None

    # 3. consecutive aggregation (calculates 0-100 score directly)

    # consecutive, presence, or partial (all, any, count)
    if agg_type in ['all', 'any', 'count']:
        # if op == '>':
        #     matches = sum(x > threshold for x in recent_data)
        # if op == '>=':
        if op in ['>', '>=']:
            matches = sum(x >= threshold for x in recent_data)
        # elif op == '<':
        #     matches = sum(x < threshold for x in recent_data)
        # elif op == '<=':
        elif op in ['>', '>=']:
            matches = sum(x <= threshold for x in recent_data)
        elif op == '==':
            matches = sum(x == threshold for x in recent_data)
        else:
            matches = 0

        if agg_type == 'all':
            return None, 100.0 if matches == n else 0.0

        elif agg_type == 'any':
            return None, 100.0 if matches > 0 else 0.0

        elif agg_type == 'count':
            min_matches = config.get('min_matches', 0)

            # if matches is less than the minimum, return 0 points
            if matches < min_matches:
                return None, 0.0

            return None, (matches / n) * 100.0

    # 4. signal aggregation (calculates 0 or100 score directly)

    # new high/low signals (rank)
    if agg_type == 'rank':
        if op in ['>', '>=', 'high']:
            is_high = recent_data.max() >= lookback_data.max()

            return None, 100.0 if is_high else 0.0

        elif op in ['<', '<=', 'low']:
            is_low = recent_data.min() <= lookback_data.min()

            return None, 100.0 if is_low else 0.0

    # crossover signals (cross)
    if agg_type == 'cross':
        if n < 2:
            return None, 0.0

        prev_val, curr_val = recent_data.iloc[-2], recent_data.iloc[-1]

        if op in ['>', '>=']:  # crossover from below (golden cross)
            is_cross = (prev_val <= threshold) and (curr_val > threshold)

            return None, 100.0 if is_cross else 0.0

        elif op in ['<', '<=']:  # crossover from above (death cross)
            is_cross = (prev_val >= threshold) and (curr_val < threshold)

            return None, 100.0 if is_cross else 0.0

    # unrecognized aggregation type
    return None, 0.0


# Scoring logic
def _calculate_score(val: float, config: dict) -> float:
    """Linearly map values to 0-100 scores based on threshold and saturation.

    Args:
        val (float): Value to score
        config (dict): Rule configuration dictionary, see 'Rule Config Schema'

    Returns:
        float: Score between 0 and 100
    """
    op = config.get('operator', '>')
    threshold = config.get('threshold', 0.0)  # pass threshold
    saturation = config.get('saturation', None)  # saturation threshold (optional)

    # case A: no saturation threshold -> binary scoring (100 if passed)
    if saturation is None:
        if op in ['>', '>=']:
            return 100.0 if val >= threshold else 0.0
        if op in ['<', '<=']:
            return 100.0 if val <= threshold else 0.0
        return 0.0

    # case B: saturation threshold set -> linear interpolation
    if op in ['>', '>=']:
        # higher is better (e.g., revenue growth)
        if val <= threshold:
            return 0.0

        if val >= saturation:
            return 100.0

        # linear mapping: (actual - threshold) / (saturation - threshold) * 100
        return (val - threshold) / (saturation - threshold) * 100.0

    elif op in ['<', '<=']:
        # lower is better (e.g., P/E ratio, debt ratio; threshold usually > saturation)
        if val >= threshold:
            return 0.0

        if val <= saturation:
            return 100.0

        # linear mapping: (threshold - actual) / (threshold - saturation) * 100
        return (threshold - val) / (threshold - saturation) * 100.0

    return 0.0


# Main Coordinator: Stock rule evaluation
def evaluate_stock_rule(series: pd.Series, config: dict) -> float:
    """General stock rule evaluation function (0-100 scale).

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
    val, direct_score = _calculate_aggregate(recent_data, lookback_data, config)

    # 4. scoring and return
    # for score-based rules (e.g., hit rate, crossover), return directly
    if direct_score is not None:
        return round(direct_score, 2)

    # for value-based rules (e.g., mean, sum), perform linear scoring
    if val is not None:
        final_score = _calculate_score(val, config)

        return round(final_score, 2)

    return 0.0
