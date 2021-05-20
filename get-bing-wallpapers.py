import argparse
import datetime
import hashlib
import logging
import os
import re
import shutil

import bs4
import funcy
import requests


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] - %(levelname)s - %(message)s')
log = logging.getLogger()


@funcy.retry(3, timeout=lambda a: 2 ** a)
def main():
    """
    @param: dest Destination for downloaded image
    Find the URL of today's image and download it we don't have it.
    Destination filename will be YYYY-mm-dd_{md5dum}.jpg
    """
    dest = './assets/BingWallpapers'
    bing_url = 'https://bing.com'
    archive_dir = os.path.join(dest, 'Archive')

    try:
        log.info(f"Connecting to {bing_url}")
        r = requests.get(bing_url)
        if not r.ok:
            raise RuntimeError(f"{r.reason}")
    except:
        log.error(f"Could not get data from {bing_url}. Exiting.")
        return

    img_cont = bs4.BeautifulSoup(
        r.content, 'html.parser').find_all('div', class_='img_cont')
    if not img_cont:
        log.error(f"Could not parse html from {bing_url}. Exiting.")
        return
    url = bing_url + re.search(r'\((.+)\)', str(img_cont)).group(1)
    log.info(f"Found image url in html: {url}")
    md5sum = hashlib.md5(url.encode('utf-8')).hexdigest()[:5]
    log.info(f"Hash of image url: {md5sum}")

    # Stop if we have this checksum in dest
    existing_files = os.listdir(dest)
    log.debug(f"Existing files in {dest} are {existing_files}")
    if any(md5sum in f for f in existing_files):
        log.info(f"Found {md5sum} hash in {dest}. Exiting.")
        return

    # Build the filename
    image_file = f"{datetime.date.today().isoformat()}_{md5sum}.jpg"
    log.info(f"image_file name: {image_file}")
    image_fullname = os.path.join(dest, image_file)

    # Download the file
    try:
        log.info(f"Downloading {url} to {image_fullname}")
        r = requests.get(url, allow_redirects=True)
        if r.ok:
            with open(image_fullname, 'wb') as f:
                log.debug(f"Writing to disk as {image_fullname}")
                f.write(r.content)
        else:
            log.error(f"Could not download {url}, reason: {r.reason}")
    except:
        log.error(f"Could not download {url} to {image_fullname}")
        return

    # Archive the existing jpg files if archive directory exists
    if os.path.isdir(archive_dir):
        for f in existing_files:
            if f.endswith('.jpg'):
                log.info(f"Archiving {f} to {archive_dir}")
                shutil.move(os.path.join(dest, f), archive_dir)

    # Done
    log.info('Done')


if __name__ == '__main__':
    main()
