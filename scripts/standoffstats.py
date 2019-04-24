#!/usr/bin/env python3

import sys
import os

from collections import defaultdict, OrderedDict, Counter
from logging import info, warning

from standoff import Textbound, Normalization

try:
    import sqlitedict
except ImportError:
    error('failed to import sqlitedict, try `pip3 install sqlitedict`')
    raise


# Keys for stats dict
ENTITY_TYPE = 'entity-type'
ENTITY_TEXT = 'text-overall'
TEXT_BY_TYPE = 'text ({})'
FRAGMENTED_SPAN = 'fragmented'
SAME_SPAN = 'same-span'
CONTAINMENT = 'containment'
CROSSING_SPAN = 'crossing-span'
CONSISTENCY = 'consistency'
TOTALS = 'TOTAL'

# Order in which to show stats
STATS_ORDER = [
    CROSSING_SPAN,
    SAME_SPAN,
    CONTAINMENT,
    TEXT_BY_TYPE,
    FRAGMENTED_SPAN,
    ENTITY_TEXT,
    ENTITY_TYPE,
    CONSISTENCY,
    TOTALS,
]


def argparser():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-l', '--limit', metavar='INT', type=int,
                    help='maximum number of documents to process')
    ap.add_argument('-s', '--suffix', default='.ann',
                    help='annotation suffix')
    ap.add_argument('-t', '--show-top', metavar='N', type=int, default=10,
                    help='show top N most frequent')
    ap.add_argument('data', nargs='+', metavar='DB')
    return ap


def is_sqlite_db(path):
    # TODO better identification
    return os.path.splitext(os.path.basename(path))[1] == '.sqlite'


def find_overlapping(textbounds):
    # Avoiding O(n^2) comparisons: create list of (offset, start/end, tb),
    # sort with end<start, and then iterate over the list while maintaining
    # a list of currently open.
    START, END = 's', 'e', #1, -1    # need END < START for sort to work right
    boundaries = []
    for t in textbounds:
        if t.end <= t.start:
            # TODO: zero-widths require special treatment: as ends sort
            # before starts, the basic algorithm doesn't work if end==start.
            warning('find_overlapping: ignoring zero-width textbound: {}'.\
                    format(t))
            continue
        boundaries.append((t.start, START, t))
        boundaries.append((t.end, END, t))
    boundaries.sort()

    overlapping = []
    open_textbounds = OrderedDict()
    for offset, boundary, textbound in boundaries:
        if boundary == START:    # overlaps with everything currently open
            for t in open_textbounds.values():
                overlapping.append((t, textbound))
            assert textbound.id not in open_textbounds, 'duplicate id'
            open_textbounds[textbound.id] = textbound
        else:
            assert boundary == END
            del open_textbounds[textbound.id]
    return overlapping


def generate_id(prefix):
    id_ = '{}{}'.format(prefix, generate_id.next_free[prefix])
    generate_id.next_free[prefix] += 1
    return id_
generate_id.next_free = defaultdict(lambda: 1)


def make_textbound(type_, span_str, text, stats):
    id_ = generate_id('T')
    spans = []
    for span in span_str.split(';'):
        start, end = (int(i) for i in span.split())
        spans.append((start, end))
    min_start = min(s[0] for s in spans)
    max_end = max(s[1] for s in spans)
    if len(spans) > 1:
        warning('replacing fragmented span {} with {} {}'.format(
            span_str, min_start, max_end))
        stats[FRAGMENTED_SPAN][type_] += 1
    return Textbound(id_, type_, min_start, max_end, text)


def take_stats(txt, ann, fn, stats):
    annotations = []
    for ln, line in enumerate(ann.splitlines(), start=1):
        if not line or line.isspace() or line[0] not in 'TN':
            info('skipping line {} in {}: {}'.format(ln, fn, line))
        if line[0] == 'T':
            id_, type_span, text = line.split('\t')
            type_, span = type_span.split(' ', 1)
            stats[ENTITY_TYPE][type_] += 1
            stats[ENTITY_TEXT][text] += 1
            stats[TEXT_BY_TYPE.format(type_)][text] += 1
            stats[TOTALS]['textbounds'] += 1
            annotations.append(make_textbound(type_, span, text, stats))
        elif line[0] == 'N':
            stats[TOTALS]['normalizations'] += 1
        else:
            assert False, 'internal error'
    stats[TOTALS]['documents'] += 1

    is_consistent = True
    overlapping = find_overlapping(annotations)
    for t1, t2 in overlapping:
        sorted_types = '{}-{}'.format(*sorted([t1.type, t2.type]))
        if t1.span_matches(t2):
            if t1.type == t2.type:
                # same span, different types
                is_consistent = False
            stats[SAME_SPAN][sorted_types] += 1
        elif t1.contains(t2):
            stats[CONTAINMENT]['{} in {}'.format(t2.type, t1.type)] += 1
        elif t2.contains(t1):
            stats[CONTAINMENT]['{} in {}'.format(t1.type, t2.type)] += 1
        elif t1.span_crosses(t2):
            is_consistent = False
            stats[CROSSING_SPAN]['{}/{}'.format(t1.type, t2.type)] += 1
        else:
            assert False, 'internal error'
    if is_consistent:
        stats[CONSISTENCY]['consistent'] += 1
    else:
        stats[CONSISTENCY]['inconsistent'] += 1


def process_db(path, stats, options):
    # No context manager: close() can block and this is read-only
    db = sqlitedict.SqliteDict(path, flag='r', autocommit=False)
    count = 0
    for key, val in db.items():
        root, ext = os.path.splitext(key)
        if ext != options.suffix:
            continue
        # txt_key = '{}.txt'.format(root)
        # txt = db[txt_key]     # everything hangs if I do this
        take_stats('', val, key, stats)
        count += 1
        if options.limit is not None and count >= options.limit:
            break

    print('Done, processed {}.'.format(count), file=sys.stderr)
    return count


def process(path, options):
    stats = defaultdict(Counter)
    if is_sqlite_db(path):
        count = process_db(path, stats, options)
    else:
        raise NotImplementedError('filesystem input ({})'.format(path))
    return stats


def report_stats(stats, options, out=sys.stdout):
    categories = list(set(STATS_ORDER + list(stats.keys())))
    rank = dict((c.split(' ')[0], i) for i, c in enumerate(STATS_ORDER))
    categories = sorted(categories, key=lambda k: (rank[k.split(' ')[0]], k))
    for category in categories:
        if '{}' in category and category not in counts:
            continue
        counts = stats[category]
        print('--- {} ---'.format(category), file=out)
        for key, count in counts.most_common(options.show_top):
            print(count, key, file=out)
        extra = len(counts)-options.show_top
        if extra > 0:
            print('[and {} more]'.format(extra), file=out)


def main(argv):
    args = argparser().parse_args(argv[1:])
    for d in args.data:
        stats = process(d, args)
        report_stats(stats, args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
