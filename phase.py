"""@measures / @TestPhase 装饰器 + 运行时 MeasurementSet。"""

from __future__ import annotations

import functools
import re
from typing import Any, Callable, List

from measurement import Measurement


class MeasurementProxy:
    def __init__(self, ui, phase_name, limits, property_limits,DevicePropertyName=None,test_data=None):
        object.__setattr__(self, "_ui", ui)
        object.__setattr__(self, "_phase", phase_name)
        object.__setattr__(self, "_limits", limits)
        object.__setattr__(self, "_property_limits", property_limits)
        object.__setattr__(self, "_written", set())
        object.__setattr__(self, "_abandoned", False)
        object.__setattr__(self, "_test_data", test_data)
        object.__setattr__(self, "_DevicePropertyName", DevicePropertyName)
    def __setitem__(self, key, value):
            self.__setattr__(key, value)
    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return

        ui      = object.__getattribute__(self, "_ui")
        phase   = object.__getattribute__(self, "_phase")
        limits  = object.__getattribute__(self, "_limits")
        prop_lims = object.__getattribute__(self, "_property_limits")
        written = object.__getattribute__(self, "_written")
        test_data = object.__getattribute__(self, "_test_data")
        DevicePropertyName = object.__getattribute__(self, "_DevicePropertyName")
        if object.__getattribute__(self, "_abandoned"):
            return

        if ui is None:
            raise RuntimeError("test_data.measurements is None")
        written.add(key)


        # ★ 1. 尝试获取专属规则
        lim = None
        current_prop = DevicePropertyName
        if test_data is not None:
            test_data.logger.info(f"[PROP] {phase}.{key}: current_prop={current_prop!r}")
        # current_prop = object.__getattribute__(self, "_get_prop")() or ""
        
        props_for_key = prop_lims.get((phase, key))
        
        if props_for_key:
            if not current_prop:
                pass
                # # 有专属规则但 DeviceProperty 为空 —— 大概率是 SetDevicePropertyLimitRules 还没调
                # test_data.logger.info(f"[PROP] {phase}.{key}: 有专属规则 {list(props_for_key)}，"
                #       f"但 current_prop 为空，回退默认规则")
            else:
                cur = current_prop.strip().lower()
                for csv_prop_str, target_lim in props_for_key.items():
                    targets = [p.strip().lower() for p in csv_prop_str.split(",") if p.strip()]
                    if cur in targets:
                        lim = target_lim
                        break
                # if lim is None:
                #     test_data.logger.info(f"[PROP] {phase}.{key}: current_prop={current_prop!r} "
                #           f"未匹配任何规则 {list(props_for_key)}，回退默认规则")
       

        # ★ 2. 如果专属规则里没找到（或者没设置属性），优雅回退到默认规则
        if lim is None:
            lim = limits.get((phase, key))


        status, validator, mn, mx = self._evaluate(value, lim)
        
       

        ui.Record(
            str(phase), str(key), value,
            str(status or ""), str(validator or ""),
            float(mn) if mn is not None else None,
            float(mx) if mx is not None else None,
            None, True,
        )

    def __getattr__(self, key):
        if key.startswith("_"):
            raise AttributeError(key)
        names = object.__getattribute__(self, "_names")
        if key not in names:
            raise AttributeError(
                f"measurement '{key}' 未在 @measures 中声明"
            )
        return None

    @staticmethod
    def _evaluate(value, lim):
        import re
        if lim is None:
            return "P", "", None, None
        if lim.rule == "re.search":
            if lim.pattern is None or lim.pattern=="":
                raise TypeError(f"Limit type error: rule 're.search' requires a string input, but received (value: {lim.rule})")
            if not isinstance(value, str)  :
                raise TypeError(f"Value type error: rule 're.search' requires a string input, but received {type(value).__name__} (value: {value})")
            # safe_pattern = re.escape(lim.pattern)
            ok = bool(re.search(lim.pattern, str(value)))
            return ("P" if ok else "F"), f"'x' matches {lim.pattern}", None, None
        elif lim.rule.replace(" ", "") == "lsl<=x<=usl":
            lo, hi = lim.min, lim.max
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Value type error: rule 'lsl <= x <= usl' requires a numeric input, but received {type(value).__name__} (value: {value})")
            if lo is None and hi is None:
                raise TypeError(f"Value type error: Limit is None")
            ok = True
            if lo is not None and value < lo: ok = False
            if hi is not None and value > hi: ok = False
            return ("P" if ok else "F"), f"{lo} <= x <= {hi}", lo, hi
        elif lim.rule == "is_true":
            if not isinstance(value, bool):
                raise TypeError(f"Value type error: rule 'is_true' requires a boolean input, but received {type(value).__name__} (value: {value})")
            ok = value is True
            return ("P" if ok else "F"), f"x is True", None, None
        else:
            raise TypeError(f"Value type error: rule 'lsl <= x <= usl' or 're.search' or 'is_true' is required, but received {lim.rule} (value: {value})")
             
# def measures(*measurements: Measurement) -> Callable:
#     def decorator(func: Callable) -> Callable:
#         func._measurements = list(measurements)

#         @functools.wraps(func)
#         def wrapper(test_data, *args, **kwargs):
#             return func(test_data, *args, **kwargs)

#         wrapper._measurements = func._measurements
#         return wrapper

#     return decorator

def measures(*measurements):
    def decorator(func):
        func._measurements = list(measurements)

        @functools.wraps(func)
        def wrapper(test_data, *args, **kwargs):
            return func(test_data, *args, **kwargs)

        wrapper._measurements = func._measurements
        return wrapper
    return decorator
class phase_options:
    """@TestPhase(timeout_s=...)。"""
    def __init__(self, timeout_s=600, name=None):
        self.timeout_s = timeout_s
        self.name = name

    def __call__(self, func):
        func._phase_name = self.name or func.__name__
        func._timeout_s = self.timeout_s

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._phase_name = func._phase_name
        wrapper._timeout_s = func._timeout_s
        wrapper._measurements = getattr(func, "_measurements", [])
        return wrapper