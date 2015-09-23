__author__ = 'James DeVincentis <james.d@hexhost.net>'

import urllib.parse
import socket
import datetime

import cif.types


def process(observable=None):
    """Takes an observable and creates new observables from data relating to the specified observable

    :param cif.types.Observable observable: Observable to source data from
    :return: A list of new observables related to the incoming one
    :rtype: cif.types.Observable
    """

    if observable is None:
        return None
    if observable.otype != "url":
        return None

    if "://" not in observable.observable:
        url = "http://"+observable.observable
    else:
        url = observable.observable

    try:
        url = urllib.parse.urlparse(url)
    except:
        # If it's not a valid URL, ignore it.
        return None


    port = None
    try:
        port = [socket.getservbyname(url.sceheme, 'tcp')]
    except:
        # Ignore failures. We aren't that interested
        pass

    return [cif.types.Observable({
        "observable": url.hostname,
        "rdata": observable.observable,
        "portlist": port,
        "related": observable.id,
        "tags": observable.tags,
        "tlp": observable.tlp,
        "group": observable.group,
        "provider": observable.provider,
        "confidence": observable._degrade_confidence(),
        "application": observable.application,
        "protocol": observable.protocol,
        "altid": observable.altid,
        "altid_tlp": observable.altid_tlp,
        "lasttime" : datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ"),
        "reporttime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%I:%SZ")
    })

    ]