import platform
from setuptools import setup, Extension
from Cython.Build import cythonize

extra_compile_args = []
if platform.system() == "Windows":
    extra_compile_args = ["/O2", "/Ox", "/fp:fast"]
else:
    extra_compile_args = ["-O3", "-ffast-math"]

extensions = [
    Extension(
        "engine.price_math",
        ["engine/price_math.pyx"],
        extra_compile_args=extra_compile_args,
    ),
    Extension(
        "engine.cython_matcher",
        ["engine/cython_matcher.pyx"],
        extra_compile_args=extra_compile_args,
    ),
]

setup(
    name="chronosmatch-cython",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "nonecheck": False,
            "initializedcheck": False,
        },
    ),
)
