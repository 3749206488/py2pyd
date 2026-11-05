# """Measurement: 一个测量项。"""

from __future__ import annotations

import re
from typing import Any, Callable, List, Optional


class Measurement:
    def __init__(self, name: str):
        self.name = name
        self.min: Optional[float] = None
        self.max: Optional[float] = None
        self.rule: str = ""              # "lsl <= x <= usl" / "re.search"
        self.pattern: str = ""           # re.search 用

    def Limit(self, min_value=None, max_value=None) -> "Measurement":
        self.min = min_value
        self.max = max_value
        self.rule = "lsl <= x <= usl"
        return self

    def Regex(self, pattern: str) -> "Measurement":
        self.pattern = pattern
        self.rule = "re.search"
        return self

    def check(self, value: Any) -> bool:
        """返回 True / False。"""
        if value is None:
            return False
         
        if self.rule == "re.search":
            return bool(re.search(self.pattern, str(value)))
        elif self.rule.replace(" ", "") == "lsl<=x<=usl":
            if self.min is not None and value < self.min:
                return False
            if self.max is not None and value > self.max:
                return False
            return True
        elif self.rule == "is_true":
            return value is True
        else:
            return False
       

    def validator_text(self) -> str:
        """UI 上显示的 validator 文案。"""
        if self.rule == "re.search":
            return f"'x' matches {self.pattern}"
        if self.rule.replace(" ", "") == "lsl<=x<=usl":
            lo = "" if self.min is None else f"{self.min}"
            hi = "" if self.max is None else f"{self.max}"
            return f"{lo} <= x <= {hi}"
        if self.rule == "is_true":
            return "x is True"
        return ""

    def apply(self, lsl, usl, rule, pattern) -> None:
        """用 CSV 的值覆盖自己。"""
        self.min = lsl
        self.max = usl
        self.rule = rule or ""
        self.pattern = pattern or ""
