from setuptools import setup, find_packages

setup(
    name="scrubmeta",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.0.0",
        "piexif>=1.1.3",
        "pikepdf>=8.0.0",
        "textual>=0.40.0",
    ],
    entry_points={
        "console_scripts": [
            "scrubmeta=scrubmeta.cli:main",
            "scrubmeta-tui=scrubmeta.tui.app:main",
        ],
    },
    python_requires=">=3.8",
)
