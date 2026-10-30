from PyInstaller.utils.hooks import collect_all  # noqa: D100
datas, binaries, hiddenimports = collect_all('speedwagon')
