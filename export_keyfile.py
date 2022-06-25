#!/usr/bin/env python3.6
# author: thuhak.zhou@nio.com
"""
export dyna key file
"""
import os
import re
from argparse import ArgumentParser
import logging
import shutil

import coloredlogs


INCLUDE_PATH = r'^\*INCLUDE_PATH\n(?P<include_path>.*)\n'
INCLUDE_FILE = r'(^\*INCLUDE(?:_TRANSFORM)?\n)(?P<include_file>(?:.*/)?(.*))'
MULTI_LINE = r'\s+\+\n'
DESCRIPTION = r'^\$.*\n'
FIX_LINE = re.compile('|'.join([MULTI_LINE, DESCRIPTION]), flags=re.MULTILINE)
MASTER_PAT = re.compile('|'.join([INCLUDE_PATH, INCLUDE_FILE]), flags=re.MULTILINE)


def export_key(keyfile, outputdir=None, force=False):
    logging.info(f'export {keyfile}')
    try:
        with open(keyfile) as f:
            text = FIX_LINE.sub('', f.read())
    except:
        logging.error(f'invalid keyfile {keyfile}')
        return
    keyfile_dir = os.path.dirname(keyfile)
    keyfile_name = os.path.basename(keyfile)
    include_paths = [keyfile_dir]
    include_files = []
    k_files = []
    for m in MASTER_PAT.finditer(text):
        for k, v in m.groupdict().items():
            if v:
                if k == 'include_path' and os.path.isdir(v):
                    include_paths.append(v)
                elif k == 'include_file':
                    include_files.append(v)
    for k in include_files:
        for base_path in include_paths:
            k_file = os.path.join(base_path, k)
            if os.path.isfile(k_file):
                k_files.append(k_file)
                break
        else:
            logging.error(f'{k} doest not exist')
            if not force:
                return
    export_name = keyfile_name.rsplit('.', maxsplit=1)[0]
    if outputdir:
        export_dir = os.path.join(outputdir, export_name)
    else:
        export_dir = os.path.join(keyfile_dir, export_name)
    os.makedirs(export_dir, exist_ok=True)
    export_text = re.sub(INCLUDE_PATH, '', text, flags=re.MULTILINE)
    export_text = re.sub(INCLUDE_FILE, r'\g<1>\g<3>', export_text, flags=re.MULTILINE)
    export_key = os.path.join(export_dir, keyfile_name)
    with open(export_key, 'w') as f:
        logging.debug(f'export {keyfile_name}')
        f.write(export_text)
    for k_file in k_files:
        logging.debug(f'export {k_file}')
        shutil.copy(k_file, export_dir)


if __name__ == '__main__':
    parser = ArgumentParser('export dyna include files')
    parser.add_argument('-l', '--log_level', choices=['debug', 'info', 'error'], default='info', help='logging level')
    parser.add_argument('-f', '--force', action='store_true', help='continue exporting if some k file was missing')
    parser.add_argument('-o', '--output', help='output dir')
    parser.add_argument('keyfile', nargs='+', help='path of key files')
    args = parser.parse_args()
    coloredlogs.install(level=args.log_level.upper(), fmt="[%(levelname)s]%(message)s")

    output = args.output
    if output and not os.path.exists(output):
        logging.debug(f'creating export dir')
        os.makedirs(output)
    for keyfile in args.keyfile:
        export_key(keyfile, output, force=args.force)