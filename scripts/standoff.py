from itertools import chain

from logging import error, warning


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

    def span_matches(self, other):
        return self.start == other.start and self.end == other.end

    def contains(self, other):
        return ((self.start <= other.start and self.end > other.end) or
                (self.start < other.start and self.end >= other.end))

    def span_crosses(self, other):
        return ((self.start < other.start and
                 other.start < self.end < other.end) or
                (other.start < self.start and
                 self.start < other.end < self.end))

    def add_id_prefix(self, prefix):
        self.id = '{}:{}'.format(prefix, self.id)

    def remove_id_prefix(self, cascade=True):
        self.id = self.id.split(':')[-1]
        if cascade:
            for n in self.normalizations:
                n.remove_id_prefix()

    def __eq__(self, other):
        return (self.start, self.end, self.type) == (other.start, other.end, other.type)

    def __lt__(self, other):
        if self.start != other.start:
            return self.start < other.start
        elif self.end != other.end:
            return self.end > other.end
        else:
            return self.type < other.type

    def __repr__(self):
        return 'Textbound({}, {}, {}, {}, {})'.format(
            self.id, self.type, self.start, self.end, self.text)

    def __str__(self):
        return '{}\t{} {} {}\t{}'.format(
            self.id, self.type, self.start, self.end, self.text)

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

    def remove_id_prefix(self):
        self.id = self.id.split(':')[-1]
        self.tb_id = self.id.split(':')[-1]

    def __str__(self):
        return '{}\t{} {} {}\t{}'.format(self.id, self.type, self.tb_id,
                                         self.norm_id, self.text)

    @classmethod
    def from_standoff(cls, line):
        id_, type_ids, text = line.split('\t')
        type_, tb_id, norm_id = type_ids.split(' ')
        return cls(id_, type_, tb_id, norm_id, text)


def parse_standoff(ann, source='<INPUT>', annset=None):
    # Note: only handles textbounds and normalizations
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
