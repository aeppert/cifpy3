import tabulate

__author__ = "Aaron Eppert <aaron.eppert@packetsled.com>"


def process(options, results, output_handle):
    headers = options['select'].split(',')
    rows = []
    for result in results:
        row = []
        for header in headers:
            if header in result:
                if isinstance(result[header], list):
                    result[header] = ', '.join(result[header])
                row.append(result[header])
            else:
                row.append('')
        rows.append(row)
    output_handle.write(tabulate.tabulate(rows, headers=headers, tablefmt="psql") + "\n")