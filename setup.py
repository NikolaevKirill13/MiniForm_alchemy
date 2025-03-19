import setuptools
# Открытие README.md и присвоение его long_description.
with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setuptools.setup(
    name="MiniForm_alchemy",
    version="0.1.3",
    author="st",
    author_email="storm_ne@inbox.ru",
    description="ModelForm и Form для FastAPI и SQLAlchemy моделей",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    package_data={
        "model_form_alchemy": [
            "static/*",
            "static/*/*",
            "static/*/*/*",
        ]
    },
    install_requires=required,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
