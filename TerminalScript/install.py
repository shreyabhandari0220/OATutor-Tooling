import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def pip_install():
    install('gspread')
    install('lax')
    install('oauth2client')
    install('pytexit')
    install('jsbeautifier')

if __name__ == '__main__':
    pip_install()