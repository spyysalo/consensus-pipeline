#!/usr/bin/env python

import sys
import os

from sqlitedict import SqliteDict


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser(description='List keys in SQLiteDict DB.')
    ap.add_argument('db', nargs='+')
    return ap


def list_db(dbname):
    # No context manager (and no close()) as this is read-only and
    # close() can block for a long time for no apparent reason.
    db = SqliteDict(dbname, flag='r', autocommit=False)
    for k in db:
        print(k)


def main(argv):
    args = argparser().parse_args(argv[1:])
    for dbname in args.db:
        if not os.path.exists(dbname):
            print('no such file: {}'.format(dbname), file=sys.stderr)
            continue
        try:
            list_db(dbname)
        except BrokenPipeError:
            # Suppress exception when used in pipe with e.g. head
            break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
