from setuptools import setup #关于setuptools https://setuptools.pypa.io/en/latest/setuptools.html#automatic-script-creation
setup(name='ugit',
      version='1.0',
      packages=['ugit'],
      entry_points={
            'console_scripts': [
                  'ugit = ugit.cli:main',
            ]
      })
#构建命令 python setup.py develop --user 生成的可执行文件默认路径为C:\Users\Administrator\AppData\Roaming\Python\Python313\Scripts