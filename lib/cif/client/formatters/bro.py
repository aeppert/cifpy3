import re

otype = {'ipv4': 'ADDR',
         'url': 'URL',
         'fqdn': 'DOMAIN'}

SEP = '|'

HEADER = '#' + '\t'.join(['fields',
                          'indicator',
                          'indicator_type',
                          'meta.desc',
                          'meta.cif_confidence',
                          'meta.source'])

cols = ['observable',
        'otype',
        'description',
        'confidence',
        'provider'
        ]


def _check_list(y):
    ret = y
    if type(y) is list:
        ret = SEP.join(y)
    return ret


def process(options, results, output_handle):
    text = []
    for result in results:
        r = []
        if result['otype'] is 'url':
            result['observable'] = re.sub(r'(https?://)', '',
                                          result['observable'])

        for c in cols:
            y = result.get(c, '-')
            y = _check_list(y)
            y = str(y)
            if c is 'otype':
                y = 'Intel::{0}'.format(otype[result[c]])
            if c is 'description':
                if result[c] is None:
                    y = result['tags']
                    y = _check_list(y)

            r.append(y)
        text.append("\t".join(r))

    text = "\n".join(text)
    text = "{0}\n{1}".format(HEADER, text)
    output_handle.write(text)
