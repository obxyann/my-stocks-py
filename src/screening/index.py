"""Screening method index

This module provides a mapping of screening method names to their corresponding
list functions
"""

from screening.list_industrial import list_industrial
from screening.list_method_a import (
    list_method_long,
    list_method_short,
    list_method_sprint,
    list_method_steady,
    list_method_test,
)

# global mapping of screening methods
# format: {display_name: list_function}
SCREENING_METHODS = {
    '一般工商業': list_industrial,
    '測試': list_method_test,
    '穩定型': list_method_steady,
    '長期強勢': list_method_long,
    '短期強勢': list_method_short,
    '衝刺型': list_method_sprint,
}
