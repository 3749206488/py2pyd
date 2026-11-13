# context.py
import os
import yaml
from types import MappingProxyType
class ReadOnlyProxy:
    """全局只读代理，拦截所有的 setattr 操作"""
    def __setattr__(self, key, value):
        # 允许在 __init__ 中设置内部私有变量
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            # 如果你需要严格只读，请把下面这行的注释解开
            pass
            # raise AttributeError(f"严禁修改配置！无法重写属性: '{key}'")


class IdentityProxy(ReadOnlyProxy):
    """映射 C# 的 ATSIdentity 类"""
    def __init__(self, csharp_identity):
        object.__setattr__(self, '_identity', csharp_identity)

    @property
    def station_id(self):
        return getattr(self._identity, "StationId", "DEFAULT")

    @property
    def station_name(self):
        return getattr(self._identity, "StationName", "DEFAULT")

    @property
    def project_id(self):
        return getattr(self._identity, "ProjectId", "DEFAULT")

    @property
    def line_id(self):
        return getattr(self._identity, "LineId", "DEFAULT")

    @property
    def line_type(self):
        raw_enum = getattr(self._identity, "LineType", None)
        return str(raw_enum) if raw_enum is not None else "DEFAULT"

    @property
    def mes_ip(self):
        raw_enum = getattr(self._identity, "MesIP", None)
        return str(raw_enum) if raw_enum is not None else "127.0.0.1"

    @property
    def mes_port(self):
        raw_enum = getattr(self._identity, "MesPort", None)
        return str(raw_enum) if raw_enum is not None else "8888"
    @property
    def oper_no(self):
        raw_enum = getattr(self._identity, "OperNo", None)
        return str(raw_enum) if raw_enum is not None else "123456"


class AutomationConfigProxy(ReadOnlyProxy):
    """映射 C# 的 ATSautomationConfig 类"""
    def __init__(self, csharp_config):
        object.__setattr__(self, '_automation', csharp_config)

    @property
    def enable(self):
        return getattr(self._automation, "Enable", False)

    @property
    def ip(self):
        return getattr(self._automation, "Ip", "")

    @property
    def port(self):
        return getattr(self._automation, "Port", "")
class TestInnerConfigProxy(ReadOnlyProxy):
    """映射 C# 的 TestInnerConfig 类（[ObservableProperty] 生成的 PascalCase 属性）"""

    # snake_case (JSON)  ->  PascalCase (C# 属性)
    _SNAKE_TO_PASCAL = {
        "working_dir":          "WorkingDir",
        "script_path":          "ScriptPath",
        "config_path":          "ConfigPath",
        "enable_scheme":        "EnableScheme",
        "scheme_path":          "SchemePath",
        "station_mode":         "StationMode",
        "scan_sn":              "ScanSn",
        "fail_stop":            "FailStop",
        "save_csv":             "SaveCsv",
        "upload_json":          "UploadJson",
        "upload_json_option":   "UploadJsonOption",
        "use_trigger":          "UseTrigger",
        "trigger_timeout_s":    "TriggerTimeoutS",
        "scan_auto_start":      "ScanAutoStart",
        "dynamic_phase":        "DynamicPhase",
        "scan_sn_auto_pop_up":  "ScanSnAutoPopUp",
        "blocking_dutr_upload": "BlockingDutrUpload",
        "trigger_auto_start":   "TriggerAutoStart",
        "async_mode_in_group":  "AsyncModeInGroup",
    }

    def __init__(self, csharp_config):
        object.__setattr__(self, '_config', csharp_config)

    def __getattr__(self, name):
        cfg = object.__getattribute__(self, '_config')
        if cfg is None:
            raise AttributeError(f"TestInnerConfig 为空，无法访问: '{name}'")
        pascal = self._SNAKE_TO_PASCAL.get(name, name)
        # 优先 PascalCase，再尝试原名（允许直接用 C# 属性名访问）
        for attr in (pascal, name):
            try:
                return getattr(cfg, attr)
            except AttributeError:
                continue
        raise AttributeError(f"TestInnerConfig 中不存在属性: '{name}'")

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __contains__(self, name):
        try:
            self.__getattr__(name)
            return True
        except AttributeError:
            return False

    def to_dict(self):
        """导出全部字段（snake_case 键），便于日志 / 调试"""
        cfg = object.__getattribute__(self, '_config')
        if cfg is None:
            return {}
        result = {}
        for snake, pascal in self._SNAKE_TO_PASCAL.items():
            try:
                result[snake] = getattr(cfg, pascal)
            except Exception:
                pass
        return result

    def __repr__(self):
        return f"TestInnerConfigProxy({object.__getattribute__(self, '_config')!r})"
class StationProxy(ReadOnlyProxy):
    def __init__(self, csharp_ats_config):
        object.__setattr__(self, '_aTSConfig', csharp_ats_config)
        
        # ★ 关键修复：pythonnet 需要访问大驼峰属性 Atsidentity，而不是 _atsidentity
        raw_identity = getattr(csharp_ats_config, "Atsidentity", None)
        object.__setattr__(self, '_identity', IdentityProxy(raw_identity) if raw_identity else None)

        # ★ 关键修复：pythonnet 需要访问大驼峰属性 Automationconfig，而不是 _automationconfig
        raw_automation = getattr(csharp_ats_config, "Automationconfig", None)
        object.__setattr__(self, '_automation', AutomationConfigProxy(raw_automation) if raw_automation else None)
        object.__setattr__(self, '_config_proxy', None)
    @property
    def identity(self):
        return self._identity

    @property
    def automation_config(self):
        return self._automation

    @property
    def active_test_config(self):
        return getattr(self._aTSConfig, "Activetestconfig", "DEFAULT.json")

    @property
    def no_popup(self):
        return getattr(self._aTSConfig, "Nopopup", False)

    @property
    def log_retention_days(self):
        return getattr(self._aTSConfig, "Logretentiondays", 1)

    @property
    def disk_usage_warning_threshold(self):
        return getattr(self._aTSConfig, "Diskusagewarningthreshold", 1)

    @property
    def disk_usage_error_threshold(self):
        return getattr(self._aTSConfig, "Diskusageerrorthreshold", 1)
    @property
    def config(self):
        """C# 注入的 TestInnerConfig（对应 __main__.config）"""
        return self._config_proxy

# =====================================================================
# 实例化代理
# =====================================================================
def _get_station():
    try:
        import __main__
        if hasattr(__main__, "station"):
            csharp_station = getattr(__main__, "station")
            proxy = StationProxy(csharp_station)
            # ★ 在构造 station 时一并注入 C# 的 TestInnerConfig
            test_cfg = _get_test_config()
            if test_cfg is not None:
                object.__setattr__(proxy, '_config_proxy', test_cfg)
            else:
                print("[Warning] config 未注入，station.config 将为 None")
            return proxy
        else:
            print("[Warning] 无法获取 C# station 对象，请确保 C# 端已注入 mainModule.station")
            return None
    except Exception as e:
        print(f"[Error] 获取 station 异常: {e}")
        return None
def _get_test_config():
    """从 C# 注入的 __main__.config 获取 TestInnerConfig"""
    try:
        import __main__
        if hasattr(__main__, "config"):
            csharp_cfg = getattr(__main__, "config")
            if csharp_cfg is not None:
                return TestInnerConfigProxy(csharp_cfg)
            print("[Warning] __main__.config 为 None")
            return None
        print("[Warning] 无法获取 C# config 对象，请确保 C# 端已注入 pyMainModule.config")
        return None
    except Exception as e:
        print(f"[Error] 获取 config 异常: {e}")
        return None
# ★ 导出实例，供 Python 脚本导入
station = _get_station()
 
# =====================================================================
# 读取 YAML 配置文件
# =====================================================================
def _load_conf_from_csharp():
    """从 C# 注入的 yaml_content 读取配置，包装为只读字典"""
    try:
        import __main__
        if hasattr(__main__, "yaml_content"):
            content = getattr(__main__, "yaml_content")
            if not content:
                return MappingProxyType({})

            # 解析 YAML 文本
            data = yaml.safe_load(content)
            
            # 使用 MappingProxyType 将普通字典变为不可修改的只读视图
            if isinstance(data, dict):
                return MappingProxyType(data)
            return MappingProxyType({})
        else:
            print("[Warning] C# 未注入 yaml_content")
            return MappingProxyType({})
    except Exception as e:
        print(f"[Error] 解析 YAML 异常: {e}")
        return MappingProxyType({})

# ★ 导出绝对只读的 conf 实例
conf = _load_conf_from_csharp()