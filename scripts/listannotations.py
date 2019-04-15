#!/usr/bin/env python

import sys
import os

from logging import error

from sqlitedict import SqliteDict


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser(description='List annotations in SQLiteDict DB.')
    ap.add_argument('-s', '--suffix', default='.ann',
                    help='Suffix for keys with annotation values')
    ap.add_argument('db', metavar='DB', help='database file')
    return ap


def list_annotations(dbname, options):
    # No context manager: close() can block and this is read-only
    doc_count, ann_count = 0, 0
    db = SqliteDict(dbname, flag='r', autocommit=False)
    for k, v in db.iteritems():
        root, ext = os.path.splitext(os.path.basename(k))
        if ext != options.suffix:
            continue
        for line in v.splitlines():
            print('{}\t{}'.format(root, line))
            ann_count += 1
        doc_count += 1
    print('Done, listed {} annotations in {} docs from {}'.format(
        ann_count, doc_count, dbname), file=sys.stderr)


def main(argv):
    args = argparser().parse_args(argv[1:])
    if not os.path.exists(args.db):
        print('no such file: {}'.format(args.db), file=sys.stderr)
        return 1
    list_annotations(args.db, args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
