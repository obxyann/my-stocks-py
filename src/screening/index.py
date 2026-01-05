"""Screening method index

This module provides a mapping of screening method names to their corresponding
list functions
"""

from screening.list_industrial import list_industrial
from screening.list_method_a import list_method_a

# global mapping of screening methods
# format: {display_name: list_function}
SCREENING_METHODS = {
    '一般工商業': list_industrial,
    '方法A': list_method_a,
}
