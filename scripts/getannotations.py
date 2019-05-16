#!/usr/bin/env python3

# Get annotations with context from database.

import sys
import os
import re

from logging import warning, error

from standoff import Textbound

try:
    from sqlitedict import SqliteDict
except ImportError:
    error('failed to import sqlitedict, try `pip3 install sqlitedict`')
    raise


def argparser():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-w', '--words', metavar='NUM', default=5, type=int,
                    help='number of context words to include')
    ap.add_argument('-as', '--ann-suffix', default='.ann',
                    help='suffix for annotations')
    ap.add_argument('-ts', '--text-suffix', default='.txt',
                    help='suffix for texts')
    ap.add_argument('ids', metavar='IDS',
                    help='list of DOC-ID<TAB>ANN-ID to output')
    ap.add_argument('data', metavar='DB', help='database')
    return ap


def get_annotation(standoff, id_):
    """Get annotation with given ID from standoff"""
    for ln, line in enumerate(standoff.splitlines(), start=1):
        fields = line.split('\t')
        if fields[0] == id_:
            if id_[0] == 'T':
                return Textbound.from_standoff(line)
            else:
                raise NotImplementedError()


def is_word(token):
        return any(c for c in token if c.isalnum())    # loose definition


def get_words(text, maximum, reverse=False):
    split = re.split(r'(\s+)', text)
    if reverse:
        split = reversed(split)
    words, count = [], 0
    for w in split:
        if count >= maximum:
            break
        words.append(w)
        if is_word(w)
            count += 1
    if reverse:
        words = reversed(words)
    return ''.join(words)


def normalize_space(s):
    return s.replace('\n', ' ').replace('\t', ' ')


def get_annotations(dbpath, ids, options):
    # No context manager: close() can block and this is read-only
    db = SqliteDict(dbpath, flag='r', autocommit=False)
    for docid, annid in ids:
        so_key = docid + options.ann_suffix
        so = db.get(so_key)
        if so is None:
            warning('{} not found in {}, skipping'.format(so_key, dbpath))
            continue
        text_key = docid + options.text_suffix
        text = db.get(text_key)
        if text is None:
            warning('{} not found in {}, skipping'.format(text_key, dbpath))
            continue
        ann = get_annotation(so, annid)
        before = 'DOCSTART ' + text[:ann.start]
        after = text[ann.end:] + 'DOCEND'
        before = get_words(before, options.words, reverse=True)
        after = get_words(after, options.words, reverse=False)
        before = normalize_space(before)
        after = normalize_space(after)
        print('\t'.join([docid, annid, ann.type, before, ann.text, after]))


def read_ids(fn, options):
    ids = []
    with open(fn) as f:
        for ln, line in enumerate(f, start=1):
            line = line.rstrip()
            fields = line.split('\t')
            docid, annid = fields[0:2]
            ids.append((docid, annid))
    return ids


def main(argv):
    args = argparser().parse_args(argv[1:])
    if args.words < 1:
        error('invalid --words NUM {}'.format(args.words))
        return 1
    ids = read_ids(args.ids, args)
    try:
        get_annotations(args.data, ids, args)
    except BrokenPipeError:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
