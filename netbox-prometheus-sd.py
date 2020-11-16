#!/usr/bin/env python3

import yaml
import argparse
import itertools
import json
import os
import netaddr
import pynetbox
import time

def main(config):
    # Establish connection to Netbox
    netbox = pynetbox.api(config['netbox_url'], token=config['netbox_token'])

    print('Start generation of service discovery files.')

    for group in config['groups']:
        print('Generate prometheus service discovery for netbox tag ' + group['netbox_tag'] + ' and put the file here: ' + group['prometheus_file'])

        # Prepare empty arrays.
        targets = []

        # Fetch devices and virtual machines from Netbox
        devices = netbox.dcim.devices.filter(has_primary_ip=True, tag=group['netbox_tag'], status="active")
        vms = netbox.virtualization.virtual_machines.filter(has_primary_ip=True, tag=group['netbox_tag'], status="active")

        # Iterate through devices
        for device in itertools.chain(devices, vms):
            # Generate labels based on Netbox data
            labels = {}
            if getattr(device, 'name', None):
                labels['netbox_name'] = device.name
            else:
                labels['netbox_name'] = repr(device)
            if device.tenant:
                labels['netbox_tenant'] = device.tenant.slug
                if device.tenant.group:
                    labels['netbox_tenant_group'] = device.tenant.group.slug
            if getattr(device, 'cluster', None):
                labels['netbox_cluster'] = device.cluster.name
            if getattr(device, 'asset_tag', None):
                labels['netbox_asset_tag'] = device.asset_tag
            if getattr(device, 'device_role', None):
                labels['netbox_role'] = device.device_role.slug
            if getattr(device, 'device_type', None):
                labels['netbox_type'] = device.device_type.model
            if getattr(device, 'rack', None):
                labels['netbox_rack'] = device.rack.name
            if getattr(device, 'site', None):
                labels['netbox_pop'] = device.site.slug
            if getattr(device, 'serial', None):
                labels['netbox_serial'] = device.serial
            if getattr(device, 'parent_device', None):
                labels['netbox_parent'] = device.parent_device.name
            if getattr(device, 'address', None):
                labels['netbox_address'] = device.address
            if getattr(device, 'description', None):
                labels['netbox_description'] = device.description

            if 'prometheus_port' in group:
                targets.append({'targets': [labels['netbox_name'] + ':' + str(group['prometheus_port'])], 'labels': labels})
            else:
                targets.append({'targets': [labels['netbox_name']], 'labels': labels})

        # Put data into output file
        temp_file = None
        if group['prometheus_file'] == '-':
            output = sys.stdout
        else:
            temp_file = '{}.tmp'.format(group['prometheus_file'])
            output = open(temp_file, 'w')

        json.dump(targets, output, indent=4)
        output.write('\n')

        if temp_file:
            output.close()
            os.rename(temp_file, group['prometheus_file'])
        else:
            output.flush()

    print('Finished generation of service discovery files.')


if __name__ == '__main__':
    # Define arguments that need to be passed to the script.
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration', help='Path to configuration file.')
    args = parser.parse_args()

    # Check if configuration parameter has a valid path to a file.
    if os.path.exists(args.configuration):
        # Parse configuration file and drop configuration into main function.
        with open(args.configuration, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
                if 'scan_interval' in config:
                    print('Startet netbox-prometheus-sd as a daemon.')
                    while True:
                        main(config)
                        time.sleep(config['scan_interval'])
                else:
                    main(config)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        print('Configuration file could not be openend.')
