from liveusb import LiveUSBError

import subprocess
import os
import sys
import requests
import tempfile

from PyQt5.QtCore import QStandardPaths


def find_downloads():
    # todo look into SUDO_UID and PKEXEC_UID for the original user
    if sys.platform.startswith("linux"):
        import pwd
        uid = 0
        if 'SUDO_UID' in os.environ:
            uid = int(os.environ['SUDO_UID'])
        elif 'PKEXEC_UID' in os.environ:
            uid = int(os.environ['PKEXEC_UID'])

        pw = pwd.getpwuid(uid)
        p = subprocess.Popen(['sudo', '-u', pw[0], 'xdg-user-dir', 'DOWNLOAD'], stdout=subprocess.PIPE)
        p.wait()
        path = p.stdout.readline().strip()
    else:
        path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)

    return path

def chown_file(path):
    if sys.platform.startswith("linux"):
        import pwd
        uid = 0
        gid = 0
        if 'SUDO_UID' in os.environ:
            uid = int(os.environ['SUDO_UID'])
            gid = int(os.environ['SUDO_GID'])
        elif 'PKEXEC_UID' in os.environ:
            uid = int(os.environ['PKEXEC_UID'])
            pw = pwd.getpwuid(uid)
            gid = pw[3]
        else:
            pass

        os.chown(path, uid, gid)
    else:
        pass

def cancel_download(url, target_folder=find_downloads()):
    file_name = os.path.basename(url)
    full_path = os.path.join(target_folder, file_name)
    partial_path = full_path + ".part"

    if os.path.exists(partial_path):
        os.remove(partial_path)

def download(url, target_folder=find_downloads(), update_maximum = None, update_current = None):
    CHUNK_SIZE = 1024 * 1024
    current_size = 0

    file_name = os.path.basename(url)
    full_path = os.path.join(target_folder, file_name)
    partial_path = full_path + ".part"
    if os.path.exists(full_path):
        return full_path
    elif os.path.exists(partial_path):
        current_size = os.path.getsize(partial_path)
    bytes_read = current_size

    if current_size > 0:
        resume_header = {'Range': 'bytes=%d-' % current_size}
    else:
        resume_header = {}

    try:
        r = requests.get(url, headers=resume_header, stream=True, allow_redirects=True, timeout=(30.0, 30.0))

        if r.status_code == 200:
            mode = "ab"
        elif r.status_code == 206:
            mode = "wb"
        elif r.status_code == 416:
            return full_path
        else:
            raise LiveUSBError("Couldn't download the file: %s (%d)" % (r.reason, r.status_code))

        if update_maximum:
            update_maximum(current_size + int(r.headers['Content-Length']))

        with open(partial_path, mode) as f:
            chown_file(partial_path)

            for chunk in r.iter_content(CHUNK_SIZE):
                f.write(chunk)
                bytes_read += len(chunk)
                if update_current:
                    update_current(bytes_read)

        os.rename(partial_path, full_path)

    except requests.exceptions.ReadTimeout as e:
        raise LiveUSBError("Your internet connection seems to be broken")
    except requests.exceptions.ConnectTimeout as e:
        raise LiveUSBError("Your internet connection seems to be broken")
    except Exception as e:
        raise LiveUSBError("Couldn't download the file: %s (%d): %s" % (r.reason, r.status_code, e.message))

    return full_path



def __print(val):
    print(val)

if __name__ == '__main__':
    import pprint
    #download("https://download.fedoraproject.org/pub/fedora/linux/releases/23/Workstation/x86_64/iso/Fedora-Live-Workstation-x86_64-23-10.iso", update_maximum=__print, update_current=__print)
    print find_downloads()
