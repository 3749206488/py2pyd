from setuptools import Extension, setup
from Cython.Build import cythonize
import glob

# 自动收集当前目录下所有 .py 文件（排除 setup.py）
py_files = [f for f in glob.glob("*.py") if f != "setup.py"]
extensions = [Extension(f[:-3], [f]) for f in py_files]

setup(
    name="pymodels",
    ext_modules=cythonize(extensions, language_level="3"),
)
