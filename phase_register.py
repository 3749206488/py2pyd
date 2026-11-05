"""Test: 收集 phase + 加载 CSV + 分步执行。"""

from __future__ import annotations

import csv
import os,sys
import time
from typing import Callable, Dict, List, Optional, Tuple
from phase import MeasurementProxy
import traceback
import concurrent.futures
import inspect
import re
# ----------------------------------------------------------------------
# 一行 CSV limit
# ----------------------------------------------------------------------
class Limit:
    def __init__(self, phase, name, lsl=None, usl=None, rule=None, pattern=None):
        self.phase = phase
        self.name = name
        self.min = lsl
        self.max = usl
        self.rule = rule or ""
        self.pattern = pattern or ""


# ----------------------------------------------------------------------
# Test
# ----------------------------------------------------------------------
class PhaseRegister:
    def __init__(self, *phases: Callable,
                 test_version: str = "",
                 test_description: str = ""):
        self.phases = list(phases)
        self.test_version = test_version
        self.test_description = test_description
        self.limits_file_name:str = ""
        # 从 phase 函数上读出所有 measurement 名字
        self.phase_list: List[str] = []              # phase 名字顺序
        self.measure_names: Dict[str, List[str]] = {}  # phase -> measurement 名
        for p in self.phases:
            name = getattr(p, "_phase_name", p.__name__)
            self.phase_list.append(name)
            self.measure_names[name] = [
                m.name for m in getattr(p, "_measurements", [])
            ]

        # CSV 解析结果 {(phase, name): Limit}
        self.limits: Dict[Tuple[str, str], Limit] = {}
        # ★ 带条件的规则字典 (phase, name) -> [("hazemidnight", Limit), ...]
        self.property_limits: Dict[Tuple[str, str], Dict[str, Limit]] = {}

        # 回调
        self.init_fn = None
        self.setup_fn = None
        self.setup_scan_fn = None
        self.teardown_fn = None
        self.clean_fn = None
        self.trigger_fn = None

    # ------------------------------------------------------------------
    def Configure(self, test_trigger=None, init_function=None,
                  teardown_function=None, clean_function=None):
        self.trigger_fn = test_trigger
        self.init_fn = init_function
        self.teardown_fn = teardown_function
        self.clean_fn = clean_function
        return self

    # ------------------------------------------------------------------
    # 读 CSV
    # ------------------------------------------------------------------
    def SetLimitFile(self, limit_file=None):
        self.limits_file_name=limit_file
        return self
    def readLimitFile(self, limit_file=None):
        if not limit_file:
            raise ValueError("limit_file 不能为空")
     

        if not os.path.isfile(limit_file):
            raise FileNotFoundError(f"找不到 limit 文件: {limit_file}")
        header = None
        with open(limit_file, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                row = [c.strip() for c in next(csv.reader([line]))]
                if header is None:
                    header = [c.lower() for c in row]
                    continue
                row += [""] * (len(header) - len(row))
                rec = dict(zip(header, row))

                phase = rec.get("phase_name", "")
                name = rec.get("measurement_name", "")
                if not phase or not name:
                    continue

                def num(v):
                    v = (v or "").strip()
                    return float(v) if v else None
                 # 获取纯字符串条件
                dev_prop = (rec.get("device_property") or "").strip()
                new_lim = Limit(
                    phase, name,
                    lsl=num(rec.get("lsl")),
                    usl=num(rec.get("usl")),
                    rule=(rec.get("validator_rule") or "").strip() or None,
                    pattern=(rec.get("search_pattern") or "").strip() or None,
                )
                if dev_prop:
                    if (phase, name) not in self.property_limits:
                        self.property_limits[(phase, name)] = {}
                    self.property_limits[(phase, name)][dev_prop] = new_lim
                else:
                    self.limits[(phase, name)] = new_lim

                # self.limits[(phase, name)] = Limit(
                #     phase, name,
                #     lsl=num(rec.get("lsl")),
                #     usl=num(rec.get("usl")),
                #     rule=(rec.get("validator_rule") or "").strip() or None,
                #     pattern=(rec.get("search_pattern") or "").strip() or None,
                # )
         
        self._validate()#检查注册名称和CSV是否一致
        return self
    def StartExecution(self, test_start=None, test_start_scan=None):
        self.setup_fn = test_start
        self.setup_scan_fn = test_start_scan
        return self
    # def _validate(self):
    #     """所有 @measures 声明的名字必须在 CSV 里。"""
    #     missing = []
    #     for phase, names in self.measure_names.items():
    #         for n in names:
    #             if (phase, n) not in self.limits:
    #                 missing.append(f"{phase}.{n}")
    #     if missing:
    #         raise ValueError(f"CSV 缺少 measurement: {missing}")
    def _validate(self):
        """检查 @measures 声明的名字是否在 CSV 中，支持正则匹配（如 RED_R_\d）。"""
        missing = []
        invalid = []
        
        # 用于存储动态展开的新 Limit，避免在循环里修改字典
        new_limits = {}
       
        
        for phase, names in self.measure_names.items():
            for n in names:
                lim = None
                # 1. 如果在 CSV 中找到了准确的测项名字，直接通过
                if (phase, n) in self.limits:
                    lim = self.limits[(phase, n)]
                     
                else:
                # 2. 如果没找到，去 CSV 里找有没有带 \d 的正则配置
                    matched_regex_key = None
                    for (csv_phase, csv_name) in self.limits.keys():
                        if csv_phase == phase and r"\d" in csv_name:
                             
                            # 注意：这里把字符串里的 \d 替换为正则的 \d+ 以便匹配 1, 28 等多位数字
                            pattern_str = "^" + csv_name.replace(r"\d", r"\d+") + "$"
                            if re.match(pattern_str, n):
                                matched_regex_key = (csv_phase, csv_name)
                                break
                    
                    # 3. 根据正则匹配结果处理
                    if matched_regex_key:
                        # 匹配成功！说明这个 n 是动态生成的，需要基于模板创建新的 Limit 给 C#
                        lim_template = self.limits[matched_regex_key]
                        lim = Limit(
                        phase, n,
                        lsl=lim_template.min,
                        usl=lim_template.max,
                        rule=lim_template.rule,
                        pattern=lim_template.pattern )
                        new_limits[(phase, n)] = lim
                    if lim is None:
                        # 既没有精确配置，也没有匹配的正则
                        missing.append(f"{phase}.{n}")
                        continue
                        
                # 4. 校验 Limit 的内容是否合法
                rule = (lim.rule or "").replace(" ", "").lower()
                if rule == "re.search":
                    if not lim.pattern or lim.pattern.strip() == "":
                        invalid.append(f"{phase}.{n} (re.search miss pattern)")
                elif rule == "lsl<=x<=usl":
                    if lim.min is None and lim.max is None:
                        invalid.append(f"{phase}.{n} (miss lsl 和 usl)")
                elif rule=="is_true":
                    pass
                else:
                    invalid.append(f"{phase}.{n} (Error: '{lim.rule}')")

 
                    
        # 将展开生成的新 Limit 合并进主字典，供 C# 读取
        if new_limits:
            self.limits.update(new_limits)

        if missing or invalid:
            error_msg = []
            if missing:
                error_msg.append(f"CSV 缺少配置: {missing}")
            if invalid:
                error_msg.append(f"Limit 内容无效: {invalid}")
            raise ValueError("\n".join(error_msg))
        
    def _sync_measurements_with_csv(self):
        """
        自动将 CSV 中存在，但 @measures 中没有声明的测项动态添加到 phase 中。
        """
        for (phase, name) in self.limits.keys():
            # 如果 CSV 里的 phase 存在
            if phase in self.measure_names:
                # 如果 CSV 里有这个测项，但静态声明里没有，就动态加进去
                if name not in self.measure_names[phase]:
                    self.measure_names[phase].append(name)
            else:
                # 如果 CSV 里的 phase 完全没在代码里，也可以选择动态创建
                self.phase_list.append(phase)
                self.measure_names[phase] = [name]
    def _auto_expand_regex_limits(self):
        """
        扫描 CSV 中的正则配置（如 RED_R_\\d），假定硬件通道为 1 到 32，
        自动将其展开为具体的 Limit 并加入到 measure_names 中。
        """
        # 收集需要新增的配置
        new_limits = {}
        
        for (phase, name), lim in list(self.limits.items()):
            if r"\d" in name:  # 如果 CSV 里含有 \d 占位符
                # 假设最大通道数为 32（你可以根据实际硬件调整）
                for i in range(1, 1000):
                    # 将 RED_R_\d 替换为 RED_R_1, RED_R_2...
                    actual_name = re.sub(r"\\d", str(i), name)
                    
                    # 创建具体的 Limit 项
                    new_limits[(phase, actual_name)] = Limit(
                            phase, actual_name,
                            lsl=lim.min, usl=lim.max,
                            rule=lim.rule, pattern=lim.pattern, 
                            mp_intent=lim.mp_intent # ★ 必须加上，否则展开后会丢失
                        )
                    
                    # 如果这个 phase 在代码里有，自动加到 measure_names 里供 UI 显示
                    if phase in self.measure_names:
                        if actual_name not in self.measure_names[phase]:
                            self.measure_names[phase].append(actual_name)
                    else:
                        # 如果代码里没写这个 phase，也动态创建
                        if phase not in self.phase_list:
                            self.phase_list.append(phase)
                            self.measure_names[phase] = []
                        self.measure_names[phase].append(actual_name)

        # 将展开后的配置合并回主字典
        self.limits.update(new_limits)
    # ------------------------------------------------------------------
    # 给 C# 读的元信息
    # ------------------------------------------------------------------
    def list_phases(self) -> List[Dict]:
        result = []
        for phase in self.phase_list:
            measures = []
            for name in self.measure_names[phase]:
                lim = self.limits.get((phase, name))

                validator = ""
                if lim:
                    if lim.rule == "re.search":
                        validator = f"'x' matches {lim.pattern}"
                    elif lim.rule == "lsl <= x <= usl":
                        validator = f"{lim.min} <= x <= {lim.max}"
                    elif lim.rule == "is_true":
                        validator = "x is True"

                measures.append({
                    "name": name,
                    "min": lim.min if lim else None,
                    "max": lim.max if lim else None,
                    "validator": validator,
                })

            result.append({
                "name": phase,
                "measurements": measures,
            })
        return result

    # ------------------------------------------------------------------
    # 步骤 1：把所有 phase/measurement 以空值推给 UI
    # ------------------------------------------------------------------
    def LoadPhases(self, test_data):
        ui = getattr(test_data, "measurements", None)
        if ui is None:
            return self

        for phase in self.phase_list:
            for name in self.measure_names[phase]:
                lim = self.limits.get((phase, name))
                validator = ""
                if lim:
                    if lim.rule == "re.search":
                        validator = f"'x' matches {lim.pattern}"
                    elif lim.rule == "lsl <= x <= usl":
                        validator = f"{lim.min} <= x <= {lim.max}"
                ui.Record(phase, name, None, "", validator,
                          lim.min if lim else None,
                          lim.max if lim else None,
                          None, True)
        return self

    

    # ------------------------------------------------------------------
    # 步骤 3：setup / setup_scan
    # ------------------------------------------------------------------
    def RunSetup(self, test_data, scan: bool = False):
        fn = self.setup_scan_fn if scan else self.setup_fn
        if fn is None:
            return "sn_0"
        sn = fn(test_data)
        return sn

    # ------------------------------------------------------------------
    # 步骤 4：执行所有 phase
    # ------------------------------------------------------------------
    # def RunPhases(self, test_data):
    #     # ① 把 limits 挂到 test_data，供 @measures wrapper 用
    #     try:
    #         from logger import make_logger, install_global_logger

    #         # ① 给当前 test_data 建 logger，赋给 C# 的 logger 字段
    #         test_data.logger = make_logger(test_data)

    #         # ② 可选：全局 logging 也进 UI
    #         install_global_logger(test_data)
    #         templates = getattr(phase, "_measurements", [])
    #         test_data._limits = self.limits
    #         total = len(self.phases)          # ★ 总 phase 数
    #         if total == 0:
    #             test_data.SetProgress(100)
    #             return self
    #         from phase import MeasurementProxy
    #         import traceback
            
    #         for i, phase in enumerate(self.phases):
    #             start_time = time.time()
    #             test_data.logger.info(f"========= {phase.__name__} =========")
    #             name = getattr(phase, "_phase_name", phase.__name__)
    #             templates = getattr(phase, "_measurements", [])
    #             ui = test_data.measurements
    #             test_data._orig_measurements = ui
    #             test_data.measurements = MeasurementProxy(
    #                 ui, name, test_data._limits, templates
    #             )
                 
    #             try:
    #                 phase(test_data)
    #             except Exception as e:
    #                 test_data.logger.info(f"[RunPhases] phase '{name}' failed:{e}")
    #                 traceback.print_exc()   # ★ 把异常栈打出来
    #             finally:
    #                 test_data.measurements = test_data._orig_measurements
    #                 percent = int((i + 1) * 100 / total)
    #                 test_data.SetProgress(percent)
    #                 duration = time.time() - start_time
    #                 test_data.logger.info(f"========= [PHASE DURATION] {phase.__name__} {duration:.2f}s=========")
    #     except Exception as e:
    #         test_data.logger.error(f"failed: {e}")
    #         raise
    #     finally:
    #         if self.teardown_fn:
    #             self.teardown_fn(test_data)

    def setLogger(self,test_data): # C#端执行将test_data 传递给python
        from logger import make_logger
        test_data.logger = make_logger(test_data)
        # install_global_logger(test_data)
    def RunPhases(self, test_data,fail_stop: bool = False):
    

        test_data._limits = self.limits
        test_data._property_limits = self.property_limits
        total = len(self.phases)
        if total == 0:
            test_data.SetProgress(100)
            return self
        try:
            if test_data.IsEnabled:
                for i, phase in enumerate(self.phases):
                    start_time = time.time()
                    name = getattr(phase, "_phase_name", phase.__name__)
                    timeout_s = getattr(phase, "_timeout_s", None)
                    templates = getattr(phase, "_measurements", [])
                    ui = test_data.measurements
                    test_data._orig_measurements = ui
                    DevicePropertyName=test_data.DeviceProperty
                    proxy = None
                    outcome = "P"  # 默认通过
                    
                    try:
                        # 1. 初始化 phase 状态
                        test_data.logger.info(f"========= {name} =========")
                        proxy = MeasurementProxy(ui, name, test_data._limits, test_data._property_limits,DevicePropertyName)
                        test_data.measurements = proxy
                        test_data.SetCurrentPhaseName(name)

                        # 2. 执行 phase
                        if timeout_s is not None and timeout_s > 0:
                            ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                            future = ex.submit(phase, test_data)
                            try:
                                future.result(timeout=timeout_s)
                            except concurrent.futures.TimeoutError:
                                outcome = "F"
                                test_data.logger.error(f"phase '{name}' timeout after {timeout_s}s")
                                
                                # ★ 核心修复 2：标记 Proxy 为抛弃状态，阻断后台线程
                                proxy._abandoned = True 
                                
                                # ★ 核心修复 3：让线程池“裸奔”，绝对不等待卡死的线程！
                                ex.shutdown(wait=False) 
                                
                                raise TimeoutError(f"phase '{name}' timeout after {timeout_s}s")
                            else:
                                # 如果正常执行完了，就干净地关掉线程池
                                ex.shutdown(wait=False)
                        else:
                            phase(test_data)

                    except Exception as e:
                        # ★ 只要发生异常，一律判为 F
                        outcome = "F"
                        test_data.logger.error(f"phase '{name}' failed: {e}")
                        test_data.logger.error(traceback.format_exc())
                        try:
                            test_data.SetPhaseStatus(name, outcome)
                        except Exception:
                            pass # 防止底层 UI 异常导致彻底崩溃
                            
                    finally:
                        # ★ 补 F：如果有 proxy 且未完成记录的，补 F
                        if proxy is not None:
                            written = proxy._written
                            for m in templates:
                                if m.name not in written:
                                    outcome = "F"
                                    try:
                                        ui.Record(name, m.name, None, "F", "not measured",
                                                  None, None, None, True)
                                    except Exception as ex:
                                        test_data.logger.warning(f"补 F 失败 {name}.{m.name}: {ex}")

                        # ★ 恢复原始 measurements
                        test_data.measurements = test_data._orig_measurements

                        # ★ 最终的 F 判定：检查 C# UI 中该 Phase 是否确实有 F
                        try:
                            for p in test_data.Phases:
                                if p.PhaseName == name:
                                    for m in p.Measurements:
                                        if m.Status == "F" or m.Status == "U":
                                            outcome = "F"
                        except Exception:
                            pass # 防止 test_data.Phases 异常打断流程

                        # ★ 更新 Phase 状态
                        try:
                            test_data.SetPhaseStatus(name, outcome)
                        except Exception:
                            pass

                        # ★ 进度 + 耗时
                        percent = int((i + 1) * 100 / total)
                        test_data.SetProgress(percent)
                        duration = time.time() - start_time
                        test_data.logger.info(f"========= [PHASE DURATION] {name} {duration:.2f}s =========")

                        # ★ 失败停止（Stop On Failure）
                        if outcome == "F" and fail_stop :
                            test_data.logger.error(
                                f"phase '{name}' failed, stop execution due to Stop On Failure=True"
                            )
                            break
                 
        finally:
            test_data.SetCurrentPhaseName("")
            if self.teardown_fn:
                self.teardown_fn(test_data)

        return self

        # ------------------------------------------------------------------
    # 步骤 2：init
    # ------------------------------------------------------------------
    def RunInit(self, logger,async_index: int = 0) -> bool:
        if self.init_fn:
            return bool(self.init_fn(logger, async_index))
        return True    

    # ------------------------------------------------------------------
    # 步骤 5：cleanup
    # ------------------------------------------------------------------
    def RunCleanup(self,logger, async_index: int = 0):
        if self.clean_fn:
            self.clean_fn(logger, async_index)
        return self
    def RunTrigger(self,logger, async_index: int = 0):
        if self.trigger_fn:
            return bool(self.trigger_fn(logger, async_index))
        return self