__author__ = 'James DeVincentis <james.d@hexhost.net>'

import ipaddress

import pygeoip

import cif


def process(observable=None):
    """Takes an observable and adds meta to it. This meta processor adds GeoIP data

    :param cif.types.Observable observable: Observable to add meta to
    :return: The augmented observable
    :rtype: cif.types.Observable
    """

    if observable is None:
        return observable

    if observable.otype not in ["ipv4"]:
        return observable

    if ipaddress.IPv4Interface(observable.observable).ip.is_private:
        return observable

    if cif.GEODATA is None:
        geodata = os.path.join(cif.LIBDIR, 'GeoIP', 'GeoLiteCity.dat')
        if os.path.exists:
            cif.GEODATA = pygeoip.GeoIP(geodata, flags=pygeoip.MEMORY_CACHE
        else:
            cif.GEODATA = False
            return observable
    elif cif.GEODATA = False
        return observable

    record = cif.GEODATA.record_by_addr(str(ipaddress.IPv4Interface(observable.observable).ip))
    if isinstance(record, dict):
        observable.cc = record['country_code']
        if record["city"] is not None and record["region_code"] is not None:
            observable.citycode = record['city'] + ", " + record['region_code']
        observable.latitude = record['latitude']
        observable.longitude = record['longitude']
        observable.timezone = record['time_zone']
        observable.metrocode = record['metro_code']
        observable.geolocation = "{0}, {1}".format(record['latitude'], record['longitude'])
    return observable