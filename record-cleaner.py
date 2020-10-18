#!/usr/bin/env python
'''
This script finds stale Route53 records.

:authorname: Mike Pietruszka <mike@mpietruszka.com>
'''

import boto3

class Route53ops(object):
    '''
    Route53 Operations
    '''
    def __init__(self):
        self.route53 = boto3.client('route53')

    def get_hosted_zone_ids(self):
        '''
        Gets all the Hosted Zones
        '''
        self.hostedzones = self.route53.list_hosted_zones()['HostedZones']
        return self.hostedzones

    def get_records(self, hostedzone):
        '''
        For given Hosted Zone, provide Resource Record Sets
        '''
        self.hostedzone = hostedzone

        self.hz = self.hostedzone['Id'].replace('/hostedzone/', '')

        max_records = 10
        dns_records = []
        
        print("Hosted Zone: {0}".format(self.hz))

        dns_in_iteration  = self.route53.list_resource_record_sets(
            HostedZoneId=self.hz
        )
        dns_records.extend(dns_in_iteration['ResourceRecordSets'])

        while len(dns_records) < max_records and 'NextRecordName' in dns_in_iteration.keys():
            next_record_name = dns_in_iteration['NextRecordName']
            print("Next set: " + next_record_name)
            dns_in_teration  = self.route53.list_resource_record_sets(
                HostedZoneId=self.hz,
                StartRecordName=next_record_name
            )
            dns_records.extend(dns_in_teration['ResourceRecordSets'])

        print("Records found: " + str(len(dns_records)))
        for record in dns_records:
            if record['Type'] == 'A':
                sub_records = record['ResourceRecords']
                record_name = record['Name']
                yield {'Name': record_name, 'ResourceRecords': sub_records}


class ENIops(object):
    def __init__(self):
        self.ec2 = boto3.client('ec2')

    def get_enis(self):
        self.enis = self.ec2.describe_network_interfaces()
        for eni in self.enis['NetworkInterfaces']:
            yield {
                'ip_address': eni['PrivateIpAddress'],
                'eni_id': eni['NetworkInterfaceId']
            }


if __name__ == '__main__':
    r = Route53ops()
    e = ENIops()

    enis = []
    for eni in e.get_enis():
        enis.append(eni['ip_address'])

    hostedzones = r.get_hosted_zone_ids()
    for hz in hostedzones:
        records = r.get_records(hz)
        record_values = []
        for rr in records:
            for value in rr['ResourceRecords']:
                record_values.append(value['Value'])
                if value['Value'] not in enis:
                    print("Found stale Route53 record: {0} - {1}".format(
                        value['Value'], rr['Name']))
