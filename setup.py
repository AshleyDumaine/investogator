from setuptools import setup

setup(
        name='investogator',
        version='0.1',
        description='A CLI tool used to query and cross-reference data on stock-tracking sites based on ETF symbols',
        author='Ashley Dumaine',
        author_email='ashley.dumaine@gmail.com',
        packages=['investogator_cli', 'investogator_cli.exceptions'],
        install_requires=['beautifulsoup4', 'requests', 'Click'],
        entry_points={
            'console_scripts': [
                'investogator=investogator_cli.investogator_cli:cli',
            ],
        },
)
