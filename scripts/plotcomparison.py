#!/usr/bin/env python3

# Plot statistics from compareannotations.py output

import sys
import os

from collections import defaultdict
from itertools import product

import colorsys

import matplotlib.pyplot as plt
from matplotlib_venn import venn3
import matplotlib.colors as mc


COLOR_BY_TYPE = {
    'Chemical': 'mediumturquoise',
    'Gene': 'blue',
    'Disease': 'red',
    'Organism': 'orange',
    'TOTAL': '#22CC22',
}


def lighten_color(color, amount=0.5):
    # From https://stackoverflow.com/a/49601444
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])


def plot_venn3(stats, type_, fn):
    labels, count_by_asets = set(), {}
    for asets, count, ratio in stats:
        labels.update(asets.split('/'))
        count_by_asets[asets] = int(count)
    labels = sorted(labels)

    Abc = count_by_asets[labels[0]]
    aBc = count_by_asets[labels[1]]
    abC = count_by_asets[labels[2]]
    ABc = count_by_asets['/'.join([labels[0],labels[1]])]
    AbC = count_by_asets['/'.join([labels[0],labels[2]])]
    aBC = count_by_asets['/'.join([labels[1],labels[2]])]
    ABC = count_by_asets['/'.join(labels)]

    # print((Abc, aBc, ABc, abC, AbC, aBC, ABC))
    v = venn3(subsets=(Abc, aBc, ABc, abC, AbC, aBC, ABC), set_labels=labels)
    #v.get_label_by_id('100').set_text('Unknown')

    for patch in (''.join(p) for p in product('01', repeat=3)):
        # ['000', '001', '010', '011', '100', '101', '110', '111']
        if patch != '000':
            color = COLOR_BY_TYPE.get(type_, 'blue')
            color = lighten_color(color, 0.75**patch.count('0'))
            v.get_patch_by_id(patch).set_color(color)

    plt.savefig(fn)
    print('Wrote {}'.format(fn))
    plt.close()


def read_until(f, line):
    found, lines = False, []
    for l in f:
        l = l.rstrip()
        if l == line:
            found = True
            break
        lines.append(l)
    if not found:
        raise ValueError('line "{}" not seen in input'.format(line))
    return lines


def main(argv):
    if len(argv) != 2:
        print('usage: {} STATS'.format(os.path.basename(__file__)),
              file=sys.stderr)
        return 1

    type_stats = defaultdict(list)
    total_stats = None
    with open(argv[1]) as f:
        read_until(f, '--- by type ---')
        lines = read_until(f, '--- totals ---')
        for l in lines:
            type_, asets, count, ratio = l.split('\t')
            type_stats[type_].append((asets, count, ratio))
        lines = read_until(f, '--- doc level ---')
        total_stats = [l.split('\t') for l in lines if len(l.split('\t')) == 3]

    for type_, stats in type_stats.items():
        plot_venn3(stats, type_, '{}-venn3.png'.format(type_))
    plot_venn3(total_stats, 'TOTAL', 'TOTAL-venn3.png')

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
