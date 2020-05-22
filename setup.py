import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dbmigrate-treebo",  # Replace with your own username
    version="0.0.1",
    author="Rohit Jain",
    author_email="rohit.jain@treebohotels.com",
    description="Package to manage database migration",
    long_description="""This package is to manage database migration of a Python project. It includes:
        - Command to generate blank migration file
        - Command to initialize the migration one or more fresh databases
        - Command to apply the unapplied migrations on one or more databases.
        
    This package takes care of generating a migration file in a specific template, which is understood by the package,
    to apply the migration. It's suggested to not generate a migration file manually, or tweak the migration file 
    template that is generated.
    """,
    long_description_content_type="text/markdown",
    url="git@bitbucket.org:treebo/dbmigrate.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['dbmigrate=dbmigrate.cli:main']
    }
)
