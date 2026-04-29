import importlib.metadata
from PyInstaller.utils.hooks import copy_metadata, collect_all
try:
    datas = copy_metadata('galatea', recursive=True)
except importlib.metadata.PackageNotFoundError as e:
    print("Package 'galatea' not found. Available packages:")
    for dist in importlib.metadata.distributions():
        print(dist.metadata['Name'])
    raise e
