#!/usr/bin/env python3

# Remove annotations from an annotation set. (Incomplete: does not
# support all annotation types.)


import sys
import os

from collections import Counter, OrderedDict
from itertools import chain
from logging import warning, error

from standoff import parse_standoff

try:
    import sqlitedict
except ImportError:
    error('failed to import sqlitedict, try `pip3 install sqlitedict`')
    raise


ANN_SUFFIX, TXT_SUFFIX = '.ann', '.txt'


def argparser():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-l', '--limit', metavar='N', type=int, default=None,
                    help='only compare first N documents')
    ap.add_argument('-o', '--overlap', default=False, action='store_true',
                    help='accept annotation overlap as match')
    ap.add_argument('-r', '--random', metavar='RATIO', default=None,
                    type=float, help='process random RATIO of documents')
    ap.add_argument('-s', '--suffix', default=ANN_SUFFIX,
                    help='suffix of annotation files')
    ap.add_argument('-t', '--include-text', default=False, action='store_true',
                    help='include text to align to in output')
    ap.add_argument('fromset', metavar='NAME:DB',
                    help='annotation set to remove from')
    ap.add_argument('output', metavar='DB',
                    help='output DB')
    ap.add_argument('sets', metavar='NAME:DB', nargs='+',
                    help='annotation sets to remove')
    return ap


def remove(annset1, annset2, options):
    remaining, removed = [], []
    if not options.overlap:
        ann_by_span = { (a.start, a.end): a for a in annset2 }
        for a in annset1:
            m = ann_by_span.get((a.start, a.end))
            if m is None:
                remaining.append(a)
            else:
                removed.append(a)
    else:
        # overlap matching (TODO: avoid O(n^2))
        for a in annset1:
            overlaps = [o for o in annset2 if a.overlaps(o)]
            if not overlaps:
                remaining.append(a)
            else:
                removed.append(a)
    return remaining


def remove_datasets(datasets, options):
    name_from, db_from = list(datasets.items())[0]
    doc_count, missing_by_dataset = 0, Counter()
    with sqlitedict.SqliteDict(options.output, autocommit=False) as out_db:
        for key, val_from in db_from.items():
            if options.limit is not None and doc_count >= options.limit:
                break
            root, suffix = os.path.splitext(key)
            if suffix != options.suffix:
                continue
            text_key = root+TXT_SUFFIX

            names, values, missing = [name_from], [val_from], False
            for name, db in list(datasets.items())[1:]:
                val = db.get(key)
                if val is None:
                    missing_by_dataset[name] += 1
                    warning('{} not found for {}'.format(key, name))
                    missing = True
                    continue
                names.append(name)
                values.append(val)
            if missing:
                continue    # incomplete data

            annsets = [
                parse_standoff(val, '{}/{}'.format(name, key), name)
                for name, val in zip(names, values)
            ]

            from_aset = annsets[0]
            for aset in annsets[1:]:
                from_aset = remove(from_aset, aset, options)

            for a in from_aset:
                a.remove_id_prefix()

            ann_str = '\n'.join(str(a) for a in from_aset)
            out_db[key] = ann_str

            if options.include_text:
                out_db[text_key] = from_db.get(text_key)

            doc_count += 1

            if doc_count % 1000 == 0:
                print('Inserted {}, committing...'.format(
                    doc_count, end='', file=sys.stderr, flush=True))
                out_db.commit()
                print('done.', file=sys.stderr)

        out_db.commit()

    missing = 'none' if not missing_by_dataset else dict(missing_by_dataset)
    print('Done, processed {} (missing: {})'.format(doc_count, missing))


def get_datasets(options):
    # TODO eliminate redundancy with compareannotations.py get_datasets()
    datasets = OrderedDict()
    for d in chain([options.fromset], options.sets):
        if ':' in d:
            name, path = d.split(':', 1)
        else:
            name = os.path.splitext(os.path.basename(d))[0]
            path = d
        if name in datasets:
            raise ValueError('duplicate name {}'.format(name))
        if not os.path.exists(path):
            print('no such file: {}'.format(path), file=sys.stderr)
            return None
        # No close() as this is read-only and close() can block
        db = sqlitedict.SqliteDict(path, flag='r', autocommit=False)
        datasets[name] = db
    return datasets


def main(argv):
    args = argparser().parse_args(argv[1:])
    if args.random is not None and not 0 < args.random < 1:
        print('error: must have 0 < RATIO < 1 for --random',
              file=sys.stderr)
        return 1
    datasets = get_datasets(args)
    if datasets is None:
        return 1
    remove_datasets(datasets, args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
