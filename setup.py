from setuptools import setup, find_packages

setup(
    name="dev-agents-v2",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Dependencies are listed in requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "firmware-agent=api.main:app",
        ],
    },
)
