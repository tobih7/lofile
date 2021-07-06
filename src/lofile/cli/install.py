# lool-File Format # CLI # (un)installing components #

import sys
import os
from ctypes import windll
from time import sleep
from subprocess import call, DEVNULL

from lofile.cli.loolclitools import Selector, out


def installer():

    FILE_EXTENSION = os.path.splitext(os.path.realpath(sys.argv[0]))[1] # installation is possible via an .exe file or an .pyz file, so the extension needs to be determined
    TARGET_PATH = os.path.join(os.getenv("PROGRAMFILES"), "lool", "lofile", f"lofile{FILE_EXTENSION}")

    # this actions have to be done with admin rights:
    INSTALLATION_SCRIPT = "&".join([
        # install to programfiles
        'md "%programfiles%\\lool\\lofile"',
        f'copy "{os.path.abspath(sys.argv[0])}" "%programfiles%\\lool\\lofile\\lofile{FILE_EXTENSION}"',

        # lofile may be already installed in another format (pyz/exe)
        'del /f /q "%programfiles%\\lool\\lofile\\lofile{}"'.format(".pyz" if os.path.splitext(TARGET_PATH)[1] == ".exe" else ".exe"),

        # registry - double click handler
        'reg ADD "HKCR\\.lo" /ve /d "lofile" /f',
        'reg ADD "HKCR\\lofile" /ve /d "lofile" /f',
        'reg ADD "HKCR\\lofile\\DefaultIcon" /ve /d "%SystemRoot%\\system32\\imageres.dll,-102" /f',
        f'reg ADD "HKCR\\lofile\\shell\\open\\command" /ve /d "\\"C:\\Windows\\py.exe\\" \\"%programfiles%\\lool\\lofile\\lofile{FILE_EXTENSION}\\" \\"decode\\" \\"%1\\"" /f',

        # create shortcut for start menu
        f'powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut(\'%programdata%\\Microsoft\\Windows\\Start Menu\\Programs\\lofile CLI.lnk\');$s.TargetPath=\'%programfiles%\\lool\\lofile\\lofile{FILE_EXTENSION}\';$s.IconLocation=\'%comspec%,0\';$s.Save()"',
    ])


    if not os.path.splitext(sys.argv[0])[1] in (".pyz", ".exe"):
        out("  \x1b[91mInstalling is only possible if lofile is running as an .exe or an .pyz file!\n")
        return

    # options
    create_desktop_shortcut = bool(Selector(("No", "Yes"), "Create a desktop shortcut?").pos)
    out("\n")

    # check for admin access
    try:
        is_admin = windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    # run installation script
    if is_admin:
        out("\r\x1b[K  \x1b[96mInstalling ...\x1b[0m ", flush=True)
        call(INSTALLATION_SCRIPT, shell=True, stdout=DEVNULL, stderr=DEVNULL, stdin=DEVNULL)

    else: # request UAC elevation and run
        out("\r\x1b[K  \x1b[96mWaiting ...\x1b[0m ", flush=True)
        errcode = windll.shell32.ShellExecuteW(None, "runas", os.getenv("COMSPEC"), "/c " + INSTALLATION_SCRIPT, None, 0) # last param = nShowCmd
        if errcode == 5:
            out("\r\x1b[K  \x1b[91mAccess was denied!\x1b[0m\n")
            return
        elif errcode <= 32:
            out("\r\x1b[K  \x1b[91mInstallation failed!\x1b[0m\n")
            return
        else:
            out("\r\x1b[K  \x1b[96mInstalling ...\x1b[0m ", flush=True)

    # validate installation
    i = 0
    while True:
        if os.path.exists(TARGET_PATH):
            break
        if i == 20: # 2 secs
            out("\r\x1b[K  \x1b[91mInstallation failed!\x1b[0m\n")
            return
        sleep(.1)
        i += 1

    # no admin stuff
    if create_desktop_shortcut:
        call(["powershell.exe", rf"$s=(New-Object -COM WScript.Shell).CreateShortcut('{os.getenv('USERPROFILE')}\Desktop\lofile CLI.lnk');$s.TargetPath='{os.getenv('PROGRAMFILES')}\lool\lofile\lofile{FILE_EXTENSION}';$s.IconLocation='{os.getenv('COMSPEC')},0';$s.Save()"], stdout=DEVNULL, stderr=DEVNULL, stdin=DEVNULL)

    # message
    out("\r\x1b[K  \x1b[92mInstallation completed!\x1b[0m\n")


def uninstaller():
    raise NotImplementedError("uninstaller is not implemented yet")
