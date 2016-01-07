from setuptools import setup, find_packages

setup(name='PAMMysqlTools',
      version='{tag}',
      description='A set of tools to manage users from pam_mysql',
      author='Christopher Perrin',
      author_email='perrin@uni-trier.de',
      url='https://gitlab.uni-trier.de/sad-team/PAMMySQL-Tools',
      packages=find_packages(),
      test_suite='tests',
      install_requires=['pymysql', 'click', 'setuptools-git-version'],
      entry_points={
          'console_scripts': [
              'myuseradd=pammymanager.scripts:useradd',
              'myuserdel=pammymanager.scripts:userdel',
              'myusermod=pammymanager.scripts:usermod',
              'mygroupadd=pammymanager.scripts:groupadd',
              'mygroupdel=pammymanager.scripts:groupdel',
              'mygroupmod=pammymanager.scripts:groupmod',
          ]
      },
      package_data= {
          'pammymanager': ['*.mo']
      })
