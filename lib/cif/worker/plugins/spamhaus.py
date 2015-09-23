__author__ = 'James DeVincentis <james.d@hexhost.net>'

import ipaddress
import datetime

import dns

import cif.types

provider = 'spamhaus.org'
confidence = 95
codes = {
    "ipv4": {
        "127.0.0.2" : {
            "assessment": "spam",
            "description": 'Direct UBE sources, spam operations & spam services',
        },
        "127.0.0.3" : {
            "assessment": "spam",
            "description": 'Direct snowshoe spam sources detected via automation',
        },
        "127.0.0.4" : {
            "assessment": "exploit",
            "description": 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
        },
        "127.0.0.5" : {
            "assessment": "exploit",
            "description": 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
        },
        "127.0.0.6" : {
            "assessment": "exploit",
            "description": 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
        },
        "127.0.0.7" : {
            "assessment": "exploit",
            "description": 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
        },
        "127.0.0.8" : {
            "assessment": "exploit",
            "description": 'CBL + customised NJABL. 3rd party exploits (proxies, trojans, etc.)',
        }
    },
    "fqdn": {
        "127.0.1.2" : {
            "assessment": "suspicious",
            "description": 'spammed domain',
        },
        "127.0.1.3" : {
            "assessment": "suspicious",
            "description": 'spammed redirector domain',
        }
    }
}

for i in range(4, 19):
    codes['fqdn']["127.0.1.{0}".format(i)] = { "assessment": "suspicious", "description": 'spammed domain'}

for i in range(20, 39):
    codes['fqdn']["127.0.1.{0}".format(i)] = {"assessment": "malware", "description": ''}


def process(observable=None):
    """Takes an observable and creates new observables from data relating to the specified observable

    :param cif.types.Observable observable: Observable to source data from
    :return: A list of new observables related to the incoming one
    :rtype: cif.types.Observable
    """
    if observable is None:
        return None

    if observable.provider is not None and observable.provider == provider:
        return None

    if observable.otype != "fqdn" and observable.tags != "ipv4":
        return None

    if observable.otype == "ipv4":

        ip = ipaddress.IPv4Interface(observable.observable).ip

        if ip.is_private:
            return None

        lookup = str(dns.reversename.from_address(str(ip))).replace(".in-addr.arpa.", "") + ".zen.spamhaus.org"
        altid = "http://www.spamhaus.org/query/bl?ip={0}".format(str(ip))

    elif observable.otype == "fqdn":

        lookup = observable.observable + ".dbl.spamhaus.org"
        altid = "http://www.spamhaus.org/query/dbl?domain={0}".format(observable.observable)

    else:

        return None

    newobservables = []
    records = []
    try:
        for record in dns.resolver.query(lookup, 'A').response.answer:
            if record is not None:
                records += str(record).split("\n")

    except:
        # Failures will be ignored. Failures happen for various reasons.
        pass

    for record in records:
        (hostname, ttl, record_class, record_type, record_value) = record.split(" ", 4)

        if record_value not in codes[observable.otype]:
            continue

        newobservables.append(cif.types.Observable(
            {
                "observable": observable.observable,
                "portlist": observable.portlist,
                "protocol": observable.protocol,
                "tags": [codes[observable.otype][record_value]["assessment"]],
                "description": codes[observable.otype][record_value]["description"],
                "tlp": observable.tlp,
                "group": observable.group,
                "provider": provider,
                "confidence": confidence,
                "application": observable.application,
                "altid": altid,
                "altid_tlp": "green",
                "related": observable.id,
                "lasttime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ"),
                "reporttime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ")
            }
        ))

    return newobservables