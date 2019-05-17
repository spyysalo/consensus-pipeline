#!/usr/bin/env python

import sys
import os
import errno

from logging import error

from sqlitedict import SqliteDict


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser(description='List values in SQLiteDict DB.')
    ap.add_argument('-k', '--showkeys', default=False, action='store_true',
                    help='include keys in output')
    ap.add_argument('-d', '--directory', default=None,
                    help='output directory')
    ap.add_argument('-P', '--dir-prefix', type=int, default=None,
                    help='add subdirectory with document ID prefix')
    ap.add_argument('db', metavar='DB', help='database file')
    ap.add_argument('keys', metavar='KEY', nargs='*', help='keys to look up')
    return ap


def write(out, key, value, options):
    if options.showkeys:
        print('==> {} <=='.format(key), file=out)
    print(value, file=out)


def document_path(doc_id, options):
    if options.directory is None:
        directory = ''
    elif options.dir_prefix is None:
        directory = options.directory
    else:
        base = os.path.splitext(doc_id)[0]
        directory = os.path.join(options.directory, base[:options.dir_prefix])
    return os.path.join(directory, doc_id)


# https://stackoverflow.com/a/600612
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def output(key, value, options):
    if options.directory is None:
        write(sys.stdout, key, value, options)
    else:
        path = document_path(key, options)
        directory = os.path.dirname(path)
        if directory not in output.known_directories:
            mkdir_p(directory)
            output.known_directories.add(directory)
        with open(path, 'w', encoding='utf-8') as out:
            write(out, key, value, options)
output.known_directories = set()


def list_db(dbname, options):
    # No context manager (and no close()) as this is read-only and
    # close() can block for a long time for no apparent reason.
    db = SqliteDict(dbname, flag='r', autocommit=False)
    if not options.keys:
        for k, v in db.iteritems():
            output(k, v.rstrip('\n'), options)
    else:
        for k in options.keys:
            try:
                v = db[k]
            except KeyError as e:
                error('no such key: "{}"'.format(k))
            else:
                output(k, v.rstrip('\n'), options)


def main(argv):
    args = argparser().parse_args(argv[1:])
    if not os.path.exists(args.db):
        print('no such file: {}'.format(args.db), file=sys.stderr)
        return 1
    try:
        list_db(args.db, args)
    except BrokenPipeError:
        # Suppress exception when used in pipe with e.g. head
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
