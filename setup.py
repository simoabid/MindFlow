from setuptools import setup, find_packages

setup(
    name="mindflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-genai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mindflow-engine=mindflow.engine:main",
        ],
    },
    python_requires=">=3.10",
)
