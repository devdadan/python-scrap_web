# hook-mysql-connector.py
from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('mysql-connector-python')
