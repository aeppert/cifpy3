__author__ = 'James DeVincentis <james.d@hexhost.net>'

import ipaddress
import dns.resolver
import datetime

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

    # Nothing in, nothing out
    if observable is None:
        return None

    # If the observable is already from here, ignore it
    if observable.provider is not None and observable.provider == provider:
        return None

    # If the observable isn't an IP or domain bail out
    if observable.otype != "fqdn" and observable.tags != "ipv4":
        return None

    # IPv4 Lookup & AltID
    if observable.otype == "ipv4":
        # Create an IP object
        ip = ipaddress.IPv4Interface(observable.observable).ip
        # If the observable is an IP and is private bail out
        if ip.is_private:
            return None
        # Generate the lookup and altid
        lookup = str(dns.reversename.from_address(str(ip))).replace(".in-addr.arpa.", "") + ".zen.spamhaus.org"
        altid = "http://www.spamhaus.org/query/bl?ip={0}".format(str(ip))
    # FQDN Lookup & AltID
    elif observable.otype == "fqdn":
        # Generate the lookup and altid
        lookup = observable.observable + ".dbl.spamhaus.org"
        altid = "http://www.spamhaus.org/query/dbl?domain={0}".format(observable.observable)
    else:
        return None

    # Create a place to store new observables
    newobservables = []
    # Place to store records
    records = []
    # Try to do the lookups
    try:
        # Do the lookups and aggregate results
        for record in dns.resolver.query(lookup, 'A').response.answer:
            # Make sure the lookup didnt fail
            if record is not None:
                # Append the record(s)
                records += str(record).split("\n")
    # Catch all excepts
    except:
        # Ignore failures
        pass

    for record in records:
        # Split the record into it's components
        (hostname, ttl, record_class, record_type, record_value) = record.split(" ", 4)

        # http://www.spamhaus.org/faq/answers.lasso?section=Spamhaus%20PBL#183
        if record_value not in codes[observable.otype]:
            continue

        # Create a new observable with the data
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