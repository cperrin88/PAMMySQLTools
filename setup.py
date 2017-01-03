from setuptools import setup, find_packages

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    read_md = lambda f: open(f, 'r').read()


setup(name='PAMMySQLTools',
      version_format='{tag}',
      version='dev',
      description='A set of tools to manage users from pam_mysql',
      author='Christopher Perrin',
      author_email='perrin@uni-trier.de',
      url='https://github.com/cperrin88/PAMMySQLTools',
      license='MIT',
      packages=find_packages(),
      long_description=read_md('README.md'),
      test_suite='tests',
      setup_requires=['setuptools-git-version', 'babel', 'pypandoc'],
      install_requires=['pymysql', 'click', 'future', 'six', 'configparser>=3.5.0b2'],
      entry_points={
          'console_scripts': [
              'myuseradd=pammysqltools.scripts:useradd',
              'myuserdel=pammysqltools.scripts:userdel',
              'myusermod=pammysqltools.scripts:usermod',
              'mygroupadd=pammysqltools.scripts:groupadd',
              'mygroupdel=pammysqltools.scripts:groupdel',
              'mygroupmod=pammysqltools.scripts:groupmod',
              'myimportusers=pammysqltools.scripts:importusers',
              'myimportgroups=pammysqltools.scripts:importgroups',
          ]
      },
      package_data={
          'pammysqltools': ['*.mo']
      },
      include_package_data=True,
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Environment :: Console"
      ])
