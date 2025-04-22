from setuptools import setup, find_packages

setup(
    name="milda_support_bot",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'src': ['assets/*.png'],
    },
    install_requires=[
        "python-telegram-bot>=20.7",
        "google-api-python-client>=2.108.0",
        "google-auth-httplib2>=0.1.1",
        "google-auth-oauthlib>=1.1.0",
        "gspread>=5.12.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
) 