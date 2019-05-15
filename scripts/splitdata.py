#!/usr/bin/env python3

import os
import sys

from logging import warning, error


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser(description='Split data by first column ID value')
    ap.add_argument('-q', '--quiet', default=False, action='store_true')
    ap.add_argument('data', help='data to split')
    ap.add_argument('parts', metavar='IDS:OUT', nargs='+',
                    help='files with IDS and files to write (OUT)')
    return ap


def read_ids(fn):
    ids = set()
    with open(fn) as f:
        for ln, l in enumerate(f, start=1):
            l = l.rstrip()
            if l in ids:
                warning('duplicate ID in {}: {}'.format(l, fn))
            ids.add(l)
    print('read {} IDs from {}'.format(len(ids), fn), file=sys.stderr)
    return ids


def main(argv):
    args = argparser().parse_args(argv[1:])

    id_and_out_fns = []
    for p in args.parts:
        try:
            id_fn, out_fn = p.split(':')
        except:
            error('parts arguments must have form "IDS:OUT"')
            return 1
        id_and_out_fns.append((id_fn, out_fn))

    ids_by_out_fn = {}
    for id_fn, out_fn in id_and_out_fns:
        if out_fn in ids_by_out_fn:
            error('duplicate OUT: {}'.format(out_fn))
            return 1
        ids_by_out_fn[out_fn] = read_ids(id_fn)

    out_by_fn = {}
    for out_fn in ids_by_out_fn:
        out_by_fn[out_fn] = open(out_fn, 'w')

    with open(args.data) as f:
        for ln, l in enumerate(f, start=1):
            try:
                id_ = l.split('\t')[0]
            except:
                error('reading line {} in {}: {}'.format(ln, args.data, l))
                return 1
            found = 0
            for fn, ids in ids_by_out_fn.items():
                if id_ in ids:
                    out_by_fn[fn].write(l)
                    found += 1
            if not found:
                if not args.quiet:
                    warning('id {} not found in any IDS'.format(id_))
            elif found > 1:
                if not args.quiet:
                    warning('id {} found in several IDS'.format(id_))

    for out in out_by_fn.values():
        out.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
