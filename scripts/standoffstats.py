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


# Normalization DB/ontology prefixes
TAXONOMY_PREFIX = 'NCBITaxon:'

# NCBI Taxonomy dump files
TAXONOMY_NODES = 'nodes.dmp'
TAXONOMY_DIVISION= 'division.dmp'
TAXONOMY_MERGED = 'merged.dmp'

# Keys for stats dict
ENTITY_TYPE = 'entity-type'
ENTITY_TEXT = 'text-overall'
TEXT_BY_TYPE = 'text ({})'
FRAGMENTED_SPAN = 'fragmented'
SAME_SPAN = 'same-span'
SAME_SPAN_TEXT = 'same-span-text'
CONTAINMENT = 'containment'
CONTAINMENT_TEXT = 'containment-text'
CROSSING_SPAN = 'crossing-span'
CROSSING_SPAN_TEXT = 'crossing-span-text'
TAXONOMY_RANK = 'taxonomy-rank'
TAXONOMY_DIV = 'taxonomy-division'
TAXONOMY_RANK_DIV = 'taxonomy-rank/division'
TAXONOMY_UNKNOWN = 'unknown-taxid'
TEXT_BY_RANK = 'rank ({})'
CONSISTENCY = 'document-consistency'
TOTALS = 'TOTAL'

# Order in which to show stats
STATS_ORDER = [
    CROSSING_SPAN,
    CROSSING_SPAN_TEXT,
    SAME_SPAN,
    SAME_SPAN_TEXT,
    CONTAINMENT,
    CONTAINMENT_TEXT,
    TEXT_BY_TYPE,
    FRAGMENTED_SPAN,
    ENTITY_TEXT,
    ENTITY_TYPE,
    TAXONOMY_RANK,
    TAXONOMY_DIV,
    TAXONOMY_RANK_DIV,
    TAXONOMY_UNKNOWN,
    TEXT_BY_RANK,
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
    ap.add_argument('-T', '--taxdata', metavar='DIR', default=None,
                    help='NCBI taxonomy data directory')
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


def take_stats(txt, ann, fn, stats, options):
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
            if len(span.split(';')) > 1:
                stats[FRAGMENTED_SPAN][type_] += 1
            annotations.append(Textbound(id_, type_, span, text))
        elif line[0] == 'N':
            id_, type_rid_tid, text = line.split('\t')
            type_, rid, tid = type_rid_tid.split(' ')
            if (tid.startswith(TAXONOMY_PREFIX) and
                options.taxdata is not None):
                tax_id = tid[len(TAXONOMY_PREFIX):]
                rank = options.taxdata.get_rank(tax_id)
                if rank == '<UNKNOWN>':
                    stats[TAXONOMY_UNKNOWN][tax_id] += 1
                division= options.taxdata.get_division(tax_id)
                stats[TAXONOMY_RANK][rank] += 1
                stats[TAXONOMY_DIV][division] += 1
                stats[TAXONOMY_RANK_DIV]['/'.join([rank, division])] += 1
                stats[TEXT_BY_RANK.format(rank)][text] += 1
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
            stats[SAME_SPAN_TEXT][t1.text] += 1
        elif t1.contains(t2):
            stats[CONTAINMENT]['{} in {}'.format(t2.type, t1.type)] += 1
            stats[CONTAINMENT_TEXT]['{} in {}'.format(t2.text, t1.text)] += 1
        elif t2.contains(t1):
            stats[CONTAINMENT]['{} in {}'.format(t1.type, t2.type)] += 1
            stats[CONTAINMENT_TEXT]['{} in {}'.format(t1.text, t2.text)] += 1
        elif t1.span_crosses(t2):
            is_consistent = False
            stats[CROSSING_SPAN]['{}/{}'.format(t1.type, t2.type)] += 1
            stats[CROSSING_SPAN_TEXT]['{}/{}'.format(t1.text, t2.text)] += 1
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
        take_stats('', val, key, stats, options)
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



class TaxonomyData(object):
    def __init__(self, rank_by_id, div_by_id, new_id):
        self.rank_by_id = rank_by_id
        self.div_by_id = div_by_id
        self.new_id = new_id

    def get_rank(self, tax_id):
        if tax_id not in self.rank_by_id and tax_id in self.new_id:
            tax_id = self.new_id[tax_id]    # old id, use merged
        return self.rank_by_id.get(tax_id, '<UNKNOWN>')

    def get_division(self, tax_id):
        if tax_id not in self.div_by_id and tax_id in self.new_id:
            tax_id = self.new_id[tax_id]    # old id, use merged
        return self.div_by_id.get(tax_id, '<UNKNOWN>')

    @classmethod
    def from_directory(cls, path):
        # Load NCBI taxonomy data from given directory
        div_name_by_id = {}
        with open(os.path.join(path, TAXONOMY_DIVISION)) as f:
            for ln, l in enumerate(f, start=1):
                l = l.rstrip('\n')
                fields = l.split('\t')[::2]    # skip separators
                div_id, div_code, div_name = fields[:3]
                div_name_by_id[div_id] = div_name

        rank_by_id = {}
        div_by_id = {}
        with open(os.path.join(path, TAXONOMY_NODES)) as f:
            for ln, l in enumerate(f, start=1):
                l = l.rstrip('\n')
                fields = l.split('\t')[::2]    # skip separators
                tax_id, parent_id, rank, embl_code, div_id = fields[:5]
                rank_by_id[tax_id] = rank
                div_by_id[tax_id] = div_name_by_id[div_id]

        new_id_by_old_id = {}
        with open(os.path.join(path, TAXONOMY_MERGED)) as f:
            for ln, l in enumerate(f, start=1):
                l = l.rstrip('\n')
                fields = l.split('\t')[::2]    # skip separators
                old_id, new_id = fields[:2]
                new_id_by_old_id[old_id] = new_id

        return cls(rank_by_id, div_by_id, new_id_by_old_id)


def main(argv):
    args = argparser().parse_args(argv[1:])
    if args.taxdata is not None:
        args.taxdata = TaxonomyData.from_directory(args.taxdata)
    for d in args.data:
        stats = process(d, args)
        report_stats(stats, args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
