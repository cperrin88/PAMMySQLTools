from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='PAMMySQLTools',
      version_format='{tag}',
      version='dev',
      description='A set of tools to manage users from pam_mysql',
      author='Christopher Perrin',
      author_email='perrin@uni-trier.de',
      url='https://gitlab.uni-trier.de/sad-team/PAMMySQL-Tools',
      license='MIT',
      packages=find_packages(),
      long_description=readme(),
      test_suite='tests',
      setup_requires=['setuptools-git-version', 'babel'],
      install_requires=['pymysql', 'click', 'babel'],
      entry_points={
          'console_scripts': [
              'myuseradd=pammysqltools.scripts:useradd',
              'myuserdel=pammysqltools.scripts:userdel',
              'myusermod=pammysqltools.scripts:usermod',
              'mygroupadd=pammysqltools.scripts:groupadd',
              'mygroupdel=pammysqltools.scripts:groupdel',
              'mygroupmod=pammysqltools.scripts:groupmod',
          ]
      },
      package_data={
          'pammysqltools': ['*.mo']
      },
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Environment :: Console"
      ])
