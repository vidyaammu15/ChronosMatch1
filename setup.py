from setuptools import setup, Extension
from Cython.Build import cythonize


extensions = [
    Extension(
        "engine.price_math",
        ["engine/price_math.pyx"],
    )
]


setup(
    name="chronosmatch-cython",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
        },
    ),
)
