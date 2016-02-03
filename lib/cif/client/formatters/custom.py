__author__ = "Aaron Eppert <aaron.eppert@packetsled.com>"


def process(options, results, output_handle):
    columns = options['select'].split(',')
    for result in results:
        row = []
        for column in columns:
            if column in result:
                row.append(result[column])
            else:
                row.append('')
        try:
            output_handle.write(options['format_string'].format(*row) + "\n")
        except Exception as ex:
            raise RuntimeError("Could not use custom formatting. column count: {0}; row count: {1}.".format(
                len(columns), len(row))
            ) from ex