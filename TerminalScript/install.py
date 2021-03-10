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
    install('openpyxl')
    install('--upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib')

if __name__ == '__main__':
    pip_install()