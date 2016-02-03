__author__ = "Aaron Eppert <aaron.eppert@packetsled.com>"


def process(options, results, output_handle):
    for result in results:
        if options['select'] is None:
            options['select'] = 'observable'
        if options['select'] in result:
            output_handle.write(result[options['select']] + "\n")