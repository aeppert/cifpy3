__author__ = 'James DeVincentis <james.d@hexhost.net>'

import datetime

import dns.resolver

import cif


# noinspection PyBroadException
def process(observable=None):
    """Takes an observable and creates new observables from data relating to the specified observable

    :param cif.types.Address observable: Observable to source data from
    :return: A list of new observables related to the incoming one
    :rtype: cif.types.Observable
    """

    if observable is None:
        return None

    if observable.otype != "fqdn":
        return None

    if observable.confidence < cif.CONFIDENCE_MIN:
        return None

    newobservables = []
    confidence = observable._degrade_confidence()
    tags = set(observable.tags)
    tags.add("rdata")
    types = ['A', 'NS', 'MX']
    records = []
    for recordtype in types:
        try:
            for record in dns.resolver.query(observable.observable, recordtype).response.answer:
                if record is not None:
                    records += str(record).split("\n")
        except:
            continue

    for record in records:
        (hostname, ttl, record_class, record_type, record_value) = record.split(" ", 4)
        if record_type == "A":
            newobservable = record_value
            application = None
            otype = "ipv4"
        elif record_type == "NS":
            newobservable = record_value
            if newobservable.endswith("."):
                newobservable = newobservable[:-1]
            application = "dns"
            if confidence > 35:
                confidence = 35
            else:
                confidence = observable._degrade_confidence(c=35)
            otype = "fqdn"
        elif record_type == "MX":
            newobservable = record_value.split(" ")[1]
            if newobservable.endswith("."):
                newobservable = newobservable[:-1]
            application = "smtp"
            if confidence > 35:
                confidence = 35
            else:
                confidence = observable._degrade_confidence(c=35)
            otype = "fqdn"
        else:
            continue

        if not cif.types.is_ipv4(newobservable) and not cif.types.is_fqdn(newobservable):
            continue

        newobservables.append(
            cif.types.Observable({
                "otype" : otype,
                "related": observable.id,
                "observable": newobservable,
                "confidence": confidence,
                "tags": list(tags),
                "tlp": observable.tlp,
                "group": observable.group,
                "provider": observable.provider,
                "rdata": observable.observable,
                "application": application,
                "portlist": observable.portlist,
                "protocol": observable.protocol,
                "altid": observable.altid,
                "altid_tlp": observable.altid_tlp,
                "rtype": record_type,
                "lasttime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ"),
                "reporttime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ")
            })
        )
    return newobservables
