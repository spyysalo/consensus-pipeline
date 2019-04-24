class Textbound(object):
    def __init__(self, id_, type_, start, end, text):
        self.id = id_
        self.type = type_
        self.start = start
        self.end = end
        self.text = text

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


class Normalization(object):
    def __init__(self, id_, tb_id, norm_id, text):
        self.id = id_
        self.tb_id = tb_id
        self.norm_id = norm_id
        self.text = text

    def __str__(self):
        return '{}\tReference {} {}\t{}'.format(
            self.id, self.tb_id, self.norm_id, self.text)
