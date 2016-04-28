#!/usr/bin/python
# -*- Mode: Python; python-indent: 8; indent-tabs-mode: t -*-

import sys, os
import subprocess

ENABLED_SERVICES = "enabled.log"
DISABLED_SERVICES = "disabled.log"
PRESET_FILE = "/usr/lib/systemd/system-preset/90-default.preset"
SYSTEMD_DIR = "/lib/systemd/system"
SYSTEMCTL = "/usr/bin/systemctl"
enabled_services = []
disabled_services = []
preset = []

def open_file(filename):
    try:
        f = open(filename, "r")
        try:
            line = f.readlines()
        except IOError:
            raise
    except IOError:
        raise
    else:
        f.close()
    return line


def run_subprocess(cmd):
    """ wrapper for Popen """
    sp = subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          shell=True,
                          bufsize=1)
    stdout = ''
    for stdout_data in iter(sp.stdout.readline, b''):
        # communicate() method buffers everything in memory, we will read stdout directly
        stdout += stdout_data
        print stdout_data,
    sp.communicate()

    return sp.returncode


def control_service(service, control="enable"):
    cmd = "{0} {1} {2}".format(SYSTEMCTL, control, service)
    print cmd
    run_subprocess(cmd)


def find_service_files(service):
    service_files = (filter(lambda x: x.startswith(service), os.listdir(SYSTEMD_DIR)))
    return service_files


def check_preset(service, control="enable"):
        service_file, extension = service.split('.')
        preset_found = filter(lambda x: service in x, preset)
        if preset_found:
            # If preset contains just <name>.service then enable directory
            if service_file in ''.join(preset_found):
                control_service(service_file, control=control)
            # Found all services for relevant <name>
            else:
                all_service_files = find_service_files(service)
                for service_type in all_service_files:
                    control_service(service_type, control=control)
        else:
            sys.stderr.write("The service %s is not mentioned in 90-default.preset file and therefore postupgrade script won't handle it\n" % service)

def determine_services(services):
    found_services = []
    for service in services:
        service = service.strip()
        if not os.access("{0}/{1}.service".format(SYSTEMD_DIR, service), os.F_OK):
            sys.stderr.write("systemd service %s.service does not exist.\n" % service)
            found_services.extend(find_service_files(service))
        else:
            found_services.append(service+".service")
    return found_services

def enable_services():
    global enabled_services
    try:
        services = open_file(ENABLED_SERVICES)
    except IOError:
        print "Unable to open enabled services"
        sys.exit(1)

    try:
        preset = open_file(PRESET_FILE)
    except IOError:
        print "Unable to open enabled services"
        sys.exit(1)

    enabled_services = determine_services(services)

    for service in enabled_services:
        if os.path.isdir(os.path.join(SYSTEMD_DIR, service)):
            continue
        check_preset(service)

def disable_services():
    global disabled_services
    try:
        services = open_file(DISABLED_SERVICES)
    except IOError:
        print "Unable to open enabled services"
        return

    disabled_services = determine_services(services)

    for service in disabled_services:
        print service
        if os.path.isdir(os.path.join(SYSTEMD_DIR, service)):
            continue
        check_preset(service, control="disable")

def main():
    disable_services()
    enable_services()

if __name__ == "__main__":
    sys.exit(main())