#!/usr/bin/env python

import sys
import os

from random import random

from sqlitedict import SqliteDict


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser(
        description='Format texts in SQLiteDict DB for JensenLab tagger.')
    ap.add_argument('-i', '--id-prefix', default='PMID:',
                    help='prefix to add to document ids')
    ap.add_argument('-l', '--limit', type=int, default=None,
                    help='maximum number of documents to output')
    ap.add_argument('-r', '--random', metavar='RATIO', default=None,
                    type=float, help='process random RATIO of documents')
    ap.add_argument('-s', '--suffix', default='.txt', help='text file suffix')
    ap.add_argument('db', nargs='+')
    return ap


def process_db(dbpath, options):
    output_count = 0
    # No context manager (and no close()) as this is read-only and
    # close() can block for a long time for no apparent reason.
    db = SqliteDict(dbpath, flag='r', autocommit=False)
    for key, value in db.items():
        root, ext = os.path.splitext(key)
        if ext != options.suffix:
            continue
        if options.random is not None and options.random < random():
            continue

        if options.id_prefix is None:
            doc_id = root
        else:
            doc_id = options.id_prefix + root

        text = value.rstrip('\n').replace('\n', ' ').replace('\t', ' ')

        print('{}\t<AUTHORS>\t<JOURNAL>\t<YEAR>\t{}'.format(doc_id, text))

        output_count += 1
        if options.limit is not None and output_count >= options.limit:
            break

    return output_count


def main(argv):
    args = argparser().parse_args(argv[1:])
    if args.random is not None and not 0 < args.random < 1:
        print('error: must have 0 < RATIO < 1 for --random',
              file=sys.stderr)
        return 1
    for dbpath in args.db:
        if not os.path.exists(dbpath):
            print('no such file: {}'.format(dbpath), file=sys.stderr)
            continue
        count = process_db(dbpath, args)
        print('Processed {}, output {} documents'.format(dbpath, count),
              file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
