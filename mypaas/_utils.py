import os
import sys
import subprocess


def appdata_dir(appname=None):
    """ Get the path to the application directory, where applications
    are allowed to write user specific files (e.g. configurations).
    """

    # Define default user directory
    userDir = os.path.expanduser("~")
    if not os.path.isdir(userDir):  # pragma: no cover
        userDir = "/var/tmp"

    # Get system app data dir
    path = None
    if sys.platform.startswith("win"):
        path = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    elif sys.platform.startswith("darwin"):
        path = os.path.join(userDir, "Library", "Application Support")
    # On Linux and as fallback
    if not (path and os.path.isdir(path)):
        path = userDir

    # Get path specific for this app
    if appname:
        if path == userDir:
            appname = "." + appname.lstrip(".")  # Make it a hidden directory
        path = os.path.join(path, appname)
        if not os.path.isdir(path):  # pragma: no cover
            os.makedirs(path, exist_ok=True)

    return path


def dockercall(*args, fail_ok=False):
    cmd = ["docker"]
    cmd.extend(args)
    if fail_ok:
        subprocess.call(cmd)
    else:
        subprocess.check_call(cmd)


USER_CONFIG_DIR = appdata_dir("mypaas")
SERVER_CONFIG_DIR = os.path.join(os.path.expanduser("~"), "_mypaas")
os.makedirs(SERVER_CONFIG_DIR, exist_ok=True)
