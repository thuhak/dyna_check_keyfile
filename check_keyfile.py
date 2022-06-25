#!/usr/bin/env python3.6
# author: thuhak.zhou@nio.com
import re
import os
import heapq
import logging
from argparse import ArgumentParser
from collections import defaultdict
from weakref import WeakValueDictionary
from functools import total_ordering

import coloredlogs
from flashtext import KeywordProcessor

KEY_FILE = re.compile(r'(.*?)((?:\d+[._-])*\d+)\.(.+)$')
INCLUDE_PATH = r'^\*INCLUDE_PATH\n(?P<include_path>.*)'
INCLUDE_FILE = r'^\*INCLUDE(_TRANSFORM)?\n(?P<include_file>.*)'
MULTI_LINE = r'\s+\+\n'
DESCRIPTION = r'^\$.*\n'
FIX_LINE = re.compile('|'.join([MULTI_LINE, DESCRIPTION]), flags=re.MULTILINE)
MASTER_PAT = re.compile('|'.join([INCLUDE_PATH, INCLUDE_FILE]), flags=re.MULTILINE)


class FlyWeight:
    def __init__(self, cls):
        self._cls = cls
        self._instances = WeakValueDictionary()

    def __call__(self, *args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key in self._instances:
            instance = self._instances[key]
        else:
            instance = self._cls(*args, **kwargs)
            self._instances[key] = instance
        return instance


@total_ordering
class Version:
    def __init__(self, v):
        versions = [v] if type(v) is int else re.findall(r'\d+', v)
        self.versions = [int(n) for n in versions] if versions else [0]
        self.len = len(self.versions)

    def __eq__(self, other):
        for i, n in enumerate(self.versions):
            try:
                if n != other.versions[i]:
                    return False
            except IndexError:
                return False
        return True

    def __gt__(self, other):
        for i, n in enumerate(self.versions):
            try:
                oversion = other.versions[i]
                if n < oversion:
                    return False
                if n > oversion:
                    return True
            except IndexError:
                return True
        return self.len > other.len


@FlyWeight
@total_ordering
class KFile:
    pattern_table = defaultdict(list)

    def __init__(self, path):
        logging.debug(f'parsing {path}')
        self.dirname = os.path.dirname(path)
        self.name = os.path.basename(path)
        m = KEY_FILE.findall(self.name)
        if not m:
            self.pattern = self.name
            self.version = Version(0)
        else:
            pattern, num, suffix = m[0]
            self.pattern = f'{pattern}|{suffix}'
            self.version = Version(num)
        heapq.heappush(self.pattern_table[self.pattern], self)

    @property
    def latest_version(self):
        return self.pattern_table[self.pattern][0]

    def search_siblings(self):
        for f in os.listdir(self.dirname):
            filename = os.path.join(self.dirname, f)
            if os.path.isfile(filename):
                KFile(filename)

    def __lt__(self, other):
        return self.version > other.version  # inverse order for minheap

    def __eq__(self, other):
        return self.version == other.version

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


def keyfile_parser(text, keyfile_dir):
    include_paths = [keyfile_dir]
    include_files = []
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
                yield k_file
                break
        else:
            logging.critical(f"{k} does not exist")


if __name__ == '__main__':
    parser = ArgumentParser('parse LS-dyna .key file')
    parser.add_argument('-l', '--log_level', choices=['debug', 'info', 'error'], default='info', help='logging level')
    parser.add_argument('-u', '--update', choices=['yes', 'no', 'auto'], default='auto',
                        help='update to the latest version')
    parser.add_argument('keyfile', nargs='+', help='path of key files')
    args = parser.parse_args()
    coloredlogs.install(level=args.log_level.upper(), fmt="[%(levelname)s]%(message)s")
    yes = lambda answer: answer[0].upper() == 'Y'

    for keyfile in args.keyfile:
        need_update = False
        keyfile_dir = os.path.dirname(keyfile)
        keyword_processor = KeywordProcessor()
        try:
            with open(keyfile) as f:
                text = f.read()
        except:
            logging.error(f'invalid keyfile {keyfile}')
            continue
        for k in keyfile_parser(FIX_LINE.sub('', text), keyfile_dir):
            k_file = KFile(k)
            k_file.search_siblings()
            latest_verion = k_file.latest_version
            if k_file is not latest_verion:
                need_update = True
                logging.info(f'[NEW VERSION] {keyfile}: {k_file} -> {latest_verion}')
                keyword_processor.add_keyword(k_file.name, latest_verion.name)
        if need_update:
            update = yes(input(f'Need update {keyfile}?(Y/N):')) if args.update == 'auto' else yes(args.update)
            if update:
                logging.info(f'updating {keyfile}')
                new_text = keyword_processor.replace_keywords(text)
                with open(keyfile, 'w') as f:
                    f.write(new_text)
