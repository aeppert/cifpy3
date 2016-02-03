CIFpy3
===================

CIFpy3 is a python rewrite and adaptation of the [Collective Intelligence Framework](http://csirtgadgets.org/collective-intelligence-framework/). The python version has a number of significant performance and feature advantages over the long standing Perl version.

There are two main components: the server, and the client. The server is responsible for almost everything. The client is simply used to interact and format data using the fully RESTful API exposed by the server.

**More information can be found on the [CIFpy3 Wiki](https://github.com/jmdevince/cifpy3/wiki)**

----------

* [Features](#features)
* [Architecture](https://github.com/jmdevince/cifpy3/wiki/Architecture)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Updating](#updating)
* [Usage](#usage)
  * [CLI Usage](#cli-usage)
  * [API Usage](https://github.com/jmdevince/cifpy3/wiki/API-Usage)
* [Object Reference](https://github.com/jmdevince/cifpy3/wiki/Object-Definition-Reference)
* [Performance Notes](https://github.com/jmdevince/cifpy3/wiki/Performance-Notes)

Features
----------
* Powered by Python 3.4+
* Performance
  * Ingest ~50-60 Observables per second per CPU core
    * This equates to ingesting about 800K Observables in ~35 minutes using 8vCPUs
  * Less than 250MB RAM per worker process
  * Configurable workers/threads count
    * Default: (1 Worker per CPU + 30 threads per /worker)
  * Faster Installation (only a few dependencies)
* Features
  * Completely Modular
    * Can split Front-End API / Feed Parser / Workers from each other
    * Run multiple worker servers if desired
  * Uses RabbitMQ for queue management
  * Full REST API
  * Simple Architecture
  * Easy to read logs
  * Comprehensive documentation and code commenting
  * Cross platform compatible
  * More flexable scheduling using hourly, daily, or weekly intervals specified for each feed
* Bug Fixes
  * No longer bails out if a single feed fails
  * Handles errors better
  * Doesn't consume memory unchecked for large feeds
  * Logic bug fixes
  * Reduction in number of memory leaks (zero or near zero leaks)
  * Proper proxy usage when fetching feeds

Prerequisites
-------------
* A powerful and fast upstream DNS server (use a local caching instance is preferred).
  * This software can generate over 3000 DNS requests/second second when using 8 vCPUs and is processing lots of observables
* One of the following supported operating systems
  * Debian 8 (jessie) or later
  * Ubuntu 14.04 (trusty) or later
  * CentOS 7 or later
  * RHEL 7 or later (with an active RHN subscription)
  * FreeBSD 10.2 or later

Installation
-------------
By default CIFpy3 gets installed to /usr/local/cifpy3/.

> **note**: be sure to save the admin token generated during installation. You need it if you want to add any additional users or use CIFpy3 with authentication enabled or even use the API. It does get saved to ~/.cif.

RedHat/CentOS
```
#!/bin/bash
curl -k https://raw.githubusercontent.com/jmdevince/cifpy3/master/bin/install.sh > install.sh
chmod +x install.sh
./install.sh
```

Ubuntu/Debian
```
#!/bin/bash
wget --no-check-certificate -O install.sh https://raw.githubusercontent.com/jmdevince/cifpy3/master/bin/install.sh
chmod +x install.sh
./install.sh
```

CIFpy3 will automatically install and configure a token for the cli & user that installs CIFpy3. This is the admin token. Any token flagged as an 'admin' is capable of deleting other admins.



Usage
-------
#### Configuring & Running
* Directory Layout
  * bin: Runtime files (cif, cif-server, cif-utility, install.sh)
  * cache: Cache folder for feed journals
  * etc: Contains configuration files for CIFpy3
    * feeds: This is where all feeds go. Standard YAML format is used. Feeds outside of this directory (or in subdirectories) are not loaded
  * lib: Contains the CIF runtime and GeoIP database if downloaded
  * log: Contains log files for CIFpy3 runs

#### CLI Usage
CIFpy3 comes with a CLI client called 'cif'. This client can be used to manage an entire CIF instance easily.


* Features
  * Select only fields desired. Almost any field is searchable
  * Customize output formats (csv,pipe,xml,json,delimiter)
  * Shows HTTP requests sent and received for debugging and advanced API usage

More details are available via the --help argument(> cif --help)


Updating
--------
Very simple process to update cifpy3

```
#!/bin/bash
cd /usr/local/cifpy3
git pull
```

Then reboot your server or just restart the cif-server service.
