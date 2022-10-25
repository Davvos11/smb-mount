import re
import shlex
import subprocess

import requests

ROOT = "/home/david/servers/plex/smb"
PLEX_TOKEN = "INSERT TOKEN HERE"


def main():
    # Get url
    url = input("SMB url: ")
    # Get the name of the series/movie
    auto_name = detect_title(url)
    name = input(f"Name (leave empty for \"{auto_name}\": ")
    name = name if name else auto_name
    # Get the type
    library_id = int(input("TV series (1) or movie (2): "))
    folder = ""
    match library_id:
        case 1:
            folder = "tv"
        case 2:
            folder = "movies"
        case _:
            print("Provide an integer (1 or 2)")
            exit(1)

    # Parse url
    url, host = parse_url(url)
    # Try to mount
    path = f"{ROOT}/{folder}/{name} [{host}]"
    mount(url, path)

    # Scan Plex library (make sure the library id is correct,
    # https://support.plex.tv/articles/201638786-plex-media-server-url-commands/#toc-1)
    scan_plex_library(library_id)

    permanent = input("Mounting seems successful, make permanent? [Y/n]")
    if permanent.lower() == "n":
        exit(0)

    create_fstab_entry(url, path)


def parse_url(url: str) -> (str, str):
    # Remove "smb:" at the start
    url = re.sub(r"^smb:", '', url)
    # Add .student.utwente.nl
    host = re.search(r"//([^/]+)", url).group(1)
    url = re.sub(r"//([^/]+)", "//\\1.student.utwente.nl", url)

    return url, host


def detect_title(url: str) -> str:
    return re.search(r"([^/]+)/?$", url).group(1)


def execute(command: str) -> (str, str):
    process = subprocess.run(shlex.split(command))
    if process.returncode != 0:
        exit()


def mount(url: str, path: str):
    # Create directory
    execute(f"mkdir -p \"{path}\"")
    # Try to mount
    cmd = f"mount -t cifs -o username=USERNAME,password=PASSWORD \"{url}\" \"{path}\""
    execute(cmd)


def create_fstab_entry(url: str, path: str):
    # Replace spaces with \040, because fstab is like that
    url = url.replace(' ', '\\040')
    path = path.replace(' ', '\\040')
    # Add to fstab
    with open('/etc/fstab', 'a') as file:
        file.write(f"{url} {path} cifs username=USERNAME,password=PASSWORD,iocharset=utf8,file_mode=0777,dir_mode=0777")


def scan_plex_library(library_id: int):
    requests.get(f"http://localhost:32400/library/sections/{library_id}/refresh?X-Plex-Token={PLEX_TOKEN}")


if __name__ == '__main__':
    main()
