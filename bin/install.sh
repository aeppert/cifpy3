#!/bin/bash

# Operating System tests
OS_LINUX=0
OS_DEBIAN=0
OS_UBUNTU=0
OS_REDHAT=0
OS_MAC=0

# Get the OS Type
function os_type
{
    case `uname` in
        Linux )
            echo "[OKAY] Detected Linux Operating System"
            OS_LINUX=1

            if [[ -f /etc/redhat-release ]]; then
                echo "[OKAY] Detected RedHat/CentOS distribution"
                OS_REDHAT=1
            fi

            if [[ -f /etc/debian-version ]]; then
                echo "[OKAY] Detected Debian distribution"
                OS_DEBIAN=1
            fi

            if [[ -f /etc/lsb-release ]]; then
                echo "[OKAY] Detected Ubuntu distribution"
                OS_UBUNTU=1
            fi

            ;;
        Darwin )
            echo "[ERROR] Detected Mac Operating System. Currently Unsupported. Support Pending"
            OS_MAC=1
            ;;
        * )
            echo "[ERROR] Unsupported OS: `uname`"
            exit 1
            ;;
    esac
}

os_type

# Install Debian Dependencies
if [[ OS_DEBIAN -gt 0 ]] || [[ OS_UBUNTU -gt 0 ]]; then

    # Apt Dependencies
    echo -n "Installing Apt Dependencies..."
    sudo apt-get -qq -y install git python3 python3-requests python3-yaml python3-dnspython python3-pip python3-dateutil \
    elasticsearch
    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Cann  ot Install dependencies."
        exit
    fi
    echo "Done"

    # Pip dependencies
    echo -n "Installing Pip3 Dependencies..."
    sudo pip3 -q install pygeoip feedparser tabulate
    if [[ $? -ne 0 ]]; then
        echo "[ERROR] Cannot Install dependencies."
        exit
    fi
    echo "Done"

    # Modify elasticsearch to startup automatically
    sudo cat /etc/default/elasticsearch | sed -e 's/#START_DAEMON/START_DAEMON/' > /etc/default/elasticsearch.new
    sudo mv /etc/default/elasticsearch.new /etc/default/elasticsearch
    sudo /etc/init.d/elasticsearch start

    # Create CIF user
    useradd -r -d /opt/cifpy3 -M cif-server

    # clone cifpy3 to /opt/
    echo "Cloning CIFpy3 to /opt/cifpy3"
    git clone https://github.com/jmdevince/cifpy3.git /opt/cifpy3
    if [[ $? -ne 0 ]]; then
        echo "[ERRROR] Could not clone cifpy3"
        exit
    fi

    chown cif:cif -Rf /opt/cifpy3

    # Copy init scripts
    cp /opt/cifpy3/scripts/debian/cif-server.systemd /etc/systemd/system/cif-server.service
    cp /opt/cifpy3/scripts/debian/cif-server.default /etc/default/cif-server
    cp /opt/cifpy3/scripts/debian/cif-server.init /etc/init.d/cif-server
    chmod +x /etc/init.d/cif-server

    # Start it up, need to detect which version
    service cif-server start

fi