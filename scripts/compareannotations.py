#!/usr/bin/env python3

# Compare two or more sets of brat-flavored annotations. (Incomplete: does
# not support all annotation types.)


import sys
import os

from collections import defaultdict, OrderedDict
from itertools import chain
from random import random
from logging import info, warning, error

try:
    import sqlitedict
except ImportError:
    error('failed to import sqlitedict, try `pip3 install sqlitedict`')
    raise


# Filter down to these
TARGET_TYPES = [
    'Chemical',
    'Disease',
    'Gene',
    'Organism',
]


TYPE_MAP = {
    # EVEX
    'cel': 'Cell',
    'che': 'Chemical',
    'dis': 'Disease',
    'ggp': 'Gene',
    'org': 'Organism',
    # EXTRACT
    'Chemical_compound': 'Chemical',
    # PubTator
    'Species': 'Organism',
}


def argparser():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('-I', '--no-ids', default=False, action='store_true',
                    help='exclude annotation IDs in output')
    ap.add_argument('-l', '--limit', metavar='N', type=int, default=None,
                    help='only compare first N documents')
    ap.add_argument('-o', '--overlap', default=False, action='store_true',
                    help='accept annotation overlap as match')
    ap.add_argument('-r', '--random', metavar='RATIO', default=None,
                    type=float, help='process random RATIO of documents')
    ap.add_argument('-S', '--no-spans', default=False, action='store_true',
                    help='exclude annotation span in output')
    ap.add_argument('-s', '--suffix', default='.ann',
                    help='suffix of files to compare')
    ap.add_argument('data', metavar='NAME:DB', nargs='+',
                    help='dataset name and path')
    return ap


class FormatError(Exception):
    pass


class ComparisonStats(object):
    def __init__(self):
        self.document_stats = defaultdict(int)
        self.annotation_totals = defaultdict(int)
        self.annotation_by_type = defaultdict(lambda: defaultdict(int))
        self.missing_docs_by_dataset = defaultdict(int)
        self.compared_docs = 0

    def __str__(self):
        s = []
        s.append('--- by type ---')
        for n in sorted(self.annotation_by_type.keys()):
            t = sum(self.annotation_by_type[n].values())
            for k, v in self.annotation_by_type[n].items():
                s.append('{}\t{}\t{}\t{:.2%}'.format(n, k, v, v/t))
        s.append('--- totals ---')
        t = sum(self.annotation_totals.values())
        for k, v in self.annotation_totals.items():
            s.append('{}\t{}\t{:.2%}'.format(k, v, v/t))
        s.append('TOTAL\t{}'.format(t))
        s.append('--- doc level ---')
        t = sum(self.document_stats.values())
        for k, v in sorted(self.document_stats.items()):
            s.append('{}\t{}\t{:.2%}'.format(k, v, v/t))            
        s.append('--- coverage ---')
        for k, v in self.missing_docs_by_dataset.items():
            s.append('{}\t{} missing'.format(v, k))
        s.append('TOTAL\t{}'.format(self.compared_docs))
        return '\n'.join(s)


class Textbound(object):
    def __init__(self, id_, type_, span, text):
        self.id = id_
        self.type = type_
        self.span = span
        self.text = text
        self.start, self.end = Textbound.parse_span(span)
        self.normalizations = []
        self.annset = None

    def overlaps(self, other):
        return not (self.end <= other.start or other.end <= self.start)

    def add_id_prefix(self, prefix):
        self.id = '{}:{}'.format(prefix, self.id)

    def __str__(self):
        return '{}\t{} {}\t{}'.format(self.id, self.type, self.span, self.text)

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def parse_span(span):
        if ';' not in span:
            start, end = (int(i) for i in span.split(' '))
        else:
            start = min(int(f.split(' ')[0]) for f in span.split(';'))
            end = max(int(f.split(' ')[1]) for f in span.split(';'))
            warning('multi-span Textbound ({}), using max span ({} {})'.\
                    format(span, start, end))
        return start, end

    @classmethod
    def from_standoff(cls, line):
        id_, type_span, text = line.split('\t')
        type_, span = type_span.split(' ', 1)
        return cls(id_, type_, span, text)


class Normalization(object):
    def __init__(self, id_, type_, tb_id, norm_id, text):
        self.id = id_
        self.type = type_
        self.tb_id = tb_id
        self.norm_id = norm_id
        self.text = text
        self.annset = None

    def add_id_prefix(self, prefix):
        self.id = '{}:{}'.format(prefix, self.id)
        self.tb_id = '{}:{}'.format(prefix, self.tb_id)

    def __str__(self):
        return '{}\t{} {} {}\t{}'.format(self.id, self.type, self.tb_id,
                                         self.norm_id, self.text)

    def __repr__(self):
        return self.__str__()
        
    @classmethod
    def from_standoff(cls, line):
        id_, type_ids, text = line.split('\t')
        type_, tb_id, norm_id = type_ids.split(' ')
        return cls(id_, type_, tb_id, norm_id, text)


def parse_standoff(ann, source='<INPUT>', annset=None):
    textbounds = []
    normalizations = []
    for ln, l in enumerate(ann.splitlines(), start=1):
        if not l or l.isspace():
            continue
        elif l[0] == 'T':
            try:
                textbounds.append(Textbound.from_standoff(l))
            except Exception as e:
                error('line {} in {}: {}'.format(ln, source, l))
                raise
        elif l[0] == 'N':
            try:
                normalizations.append(Normalization.from_standoff(l))
            except Exception as e:
                error('line {} in {}: {}'.format(ln, source, l))
                raise
        else:
            warning('skipping line {} in {}: {}'.format(ln, source, l))
            continue

    # Attach normalizations to textbounds
    tb_by_id = {}
    for t in textbounds:
        tb_by_id[t.id] = t
    for n in normalizations:
        tb = tb_by_id.get(n.tb_id)
        if tb is not None:
            tb.normalizations.append(n)
        else:
            error('skip normalization for unknown textbound: {}'.format(n))

    if annset is not None:
        for a in chain(textbounds, normalizations):
            a.add_id_prefix(annset)
            a.annset = annset
            
    return textbounds


def find_overlapping(ann, annsets, ignore=None):
    if ignore is None:
        ignore = []
    overlapping = []
    for annset in annsets:
        for a in annset:
            if a is ann or a in ignore:
                continue
            if a.overlaps(ann):
                overlapping.append(a)
    return overlapping


def compare_annsets(label, names, annsets, stats, options):
    if options.overlap:
        raise NotImplementedError()
    # Exact match; group by (start, end, type)
    grouped = defaultdict(list)
    for name, annset in zip(names, annsets):
        for a in annset:
            key = (a.start, a.end, a.type)
            if any(m for m in grouped[key] if m.annset == a.annset):
                warning('dup annotation in {}: {}'.format(name, a))
                # Ignore (start, end, type) duplicates
            else:
                grouped[key].append(a)

    # Stats
    all_asets, doc_asets, mm_asets = set(names), set(), set()
    for (start, end, type_), group in grouped.items():
        asets = set(a.annset for a in group)
        asets_str = '/'.join(sorted(asets))
        doc_asets.add(tuple(sorted(a.annset for a in group)))
        if len(all_asets) > 2 and len(asets) == 1:
            mm_asets.add(list(asets)[0])    # odd one out
        elif len(all_asets) > 2 and len(asets) == len(all_asets)-1:
            mm_asets.add(list(all_asets-asets)[0])    # odd one out
        stats.annotation_by_type[type_][asets_str] += 1
        stats.annotation_totals[asets_str] += 1
    if len(doc_asets) == 0:
        stats.document_stats['match-all-empty'] += 1
    elif len(doc_asets) == 1 and list(doc_asets)[0] == tuple(sorted(all_asets)):
        stats.document_stats['match-all-nonempty'] += 1
    elif len(mm_asets) == 1:
        stats.document_stats['mismatch-{}'.format(mm_asets.pop())] += 1
    else:
        stats.document_stats['mismatch-multiple'] += 1

    # Instance output
    for (start, end, type_), group in grouped.items():
        # sanity
        texts = set(a.text for a in group)
        assert len(texts) == 1, 'text mismatch: {}'.format(texts)
        text = texts.pop()
        overlapping = find_overlapping(group[0], annsets, group)
        if options.no_ids:
            ids = '/'.join(sorted(a.annset for a in group))
        else:
            ids = '/'.join(sorted(a.id for a in group))
        if options.no_spans:
            type_span = type_
        else:
            type_span = '{} {} {}'.format(type_, start, end)
        overlap_strs = ['{}/{}'.format(a.text, a.type) for a in overlapping]
        print('{}\t{}\t{}\t{}\t{}'.format(
            label, ids, type_span, text, sorted(set(overlap_strs))))

    
def compare_datasets(datasets, options):
    stats = ComparisonStats()
    name1, db1 = list(datasets.items())[0]
    for key, val1 in db1.items():
        if options.limit is not None and stats.compared_docs >= options.limit:
            break
        if os.path.splitext(key)[1] != options.suffix:
            continue
        if options.random is not None and options.random < random():
            continue
        names, values, missing = [name1], [val1], False
        for name, db in list(datasets.items())[1:]:
            val = db.get(key)
            if val is None:
                stats.missing_docs_by_dataset[name] += 1
                warning('{} not found for {}'.format(key, name))
                missing = True
                continue
            names.append(name)
            values.append(val)
        if missing:
            continue    # incomplete data

        # Parse, map types, and filter to targeted types
        annsets = [
            parse_standoff(val, '{}/{}'.format(name, key), name)
            for name, val in zip(names, values)
        ]
        for annset in annsets:
            for a in annset:
                a.type = TYPE_MAP.get(a.type, a.type)
        for i in range(len(annsets)):
            annsets[i] = [a for a in annsets[i] if a.type in TARGET_TYPES]

        # Run comparison
        label = os.path.splitext(key)[0]
        compare_annsets(label, names, annsets, stats, options)
        stats.compared_docs += 1
    return stats


def get_datasets(options):
    datasets = OrderedDict()
    for d in options.data:
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
        # No context manager (and no close()) as this is read-only and
        # close() can block for a long time for no apparent reason.
        db = sqlitedict.SqliteDict(path, flag='r', autocommit=False)
        datasets[name] = db
    return datasets


def main(argv):
    args = argparser().parse_args(argv[1:])
    if len(args.data) < 2:
        print('error: at least two NAME:DB arguments required',
              file=sys.stderr)
        return 1
    if args.random is not None and not 0 < args.random < 1:
        print('error: must have 0 < RATIO < 1 for --random',
              file=sys.stderr)
        return 1
    datasets = get_datasets(args)
    if datasets is None:
        return 1
    stats = compare_datasets(datasets, args)
    print(stats, file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
