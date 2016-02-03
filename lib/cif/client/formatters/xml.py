import xml.etree.cElementTree

__author__ = "Aaron Eppert <aaron.eppert@packetsled.com>"


def process(self, options, results, output_handle):
    headers = options['select'].split(',')

    if options['write'] is not None:
        self.output_handle.close()
        self.output_handle = open(options['write'], 'wb')
    else:
        raise RuntimeError("XML output can only be written to a file.")

    observables = xml.etree.cElementTree.Element("observables")
    for result in self.results:
        observable = xml.etree.cElementTree.SubElement(observables, "observable")
        for header in headers:
            if isinstance(result[header], list):
                if not header.endswith('s'):
                    header += 's'
                sub = xml.etree.cElementTree.SubElement(observable, header)
                for val in result[header]:
                    xml.etree.cElementTree.SubElement(sub, header[:-1]).text = val
            else:
                xml.etree.cElementTree.SubElement(observable, header).text = result[header]

    tree = xml.etree.cElementTree.ElementTree(observables)
    tree.write(self.output_handle)