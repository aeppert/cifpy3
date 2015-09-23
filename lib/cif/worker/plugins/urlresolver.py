__author__ = 'James DeVincentis <james.d@hexhost.net>'

import urllib.parse
import socket
import datetime
import cif.types

def process(observable=None):
    # Return nothing if nothing was given
    if observable is None:
        return None
    # If the observable is not a URL we have nothing to do
    if observable.otype != "url":
        return None

    # Check to make sure the URL has a scheme
    if "://" not in observable.observable:
        url = "http://"+observable.observable
    else:
        url = observable.observable

    # Parse the URL
    try:
        url = urllib.parse.urlparse(url)
    except:
        return None

    # Get port
    port = None
    try:
        port = [socket.getservbyname(url.sceheme, 'tcp')]
    except:
        pass

    # Createa a new
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