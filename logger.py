"""Python 标准 logging，转发到 C# UI。"""

from __future__ import annotations
import logging


class UiHandler(logging.Handler):
    """把 logging 记录转发到 C# test_data.AppendLog。"""

    def __init__(self, test_data, level=logging.NOTSET):
        super().__init__(level=level)
        self._test_data = test_data

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            td = self._test_data
            if td is None:
                return

            # 优先用带 level 的重载
            try:
                td.AppendLog(record.levelname, msg)
            except Exception:
                # 兜底：只有 AppendLog(string)
                td.AppendLog(f"[{record.levelname}] {msg}")
        except Exception:
            self.handleError(record)


def make_logger(test_data, name: str = "ui") -> logging.Logger:
    """给每个 test_data 建一个独立的 logger，输出自动进 UI。"""
    logger = logging.getLogger(f"{name}.{id(test_data)}")
    logger.setLevel(logging.DEBUG)
    
    # ★ 必须保留：防止日志冒泡到全局 root，避免重复或串台
    logger.propagate = False 

    # ★ 关键修改：先清空可能残留的旧 Handler，防止重复点击导致日志成倍输出
    for h in list(logger.handlers):
        if isinstance(h, UiHandler):
            logger.removeHandler(h)

    # 重新挂载新的 Handler
    h = UiHandler(test_data)
    h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(h)

    return logger


def remove_logger(test_data, name: str = "ui") -> None:
    """
    ★ 新增：停止转发日志。
    在测试跑完或取消时调用，剥离 UI Handler，实现“不执行就不显示”。
    """
    logger = logging.getLogger(f"{name}.{id(test_data)}")
    for h in list(logger.handlers):
        if isinstance(h, UiHandler):
            logger.removeHandler(h)


# ❌ 绝对不要用这个！只要用了它，整个 Python 进程的日志都会涌进这个 Slot！
# 如果你非要保留，请确保只在调试时用，正式跑测时不要调。
# def install_global_logger(test_data, level: int = logging.DEBUG) -> None:
#     """把根 logger 也接到 UI，这样 logging.getLogger('any').info(...) 都会进 UI。"""
#     root = logging.getLogger()
#     root.setLevel(level)
# 
#     for h in list(root.handlers):
#         if isinstance(h, UiHandler):
#             root.removeHandler(h)
# 
#     root.addHandler(UiHandler(test_data))