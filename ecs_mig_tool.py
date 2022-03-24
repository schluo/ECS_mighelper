#!/usr/bin/env python3
# encoding: utf-8

__author__ = "Oliver Schlueter"
__copyright__ = "Copyright 2022, Dell Technologies"
__license__ = "GPL"
__version__ = "1.0.1"
__email__ = "oliver.schlueter@dell.com"
__status__ = "Production"

""""
###########################################################################################################

  DELL EMC ECS Migration Helper Tool

  Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
  and associated documentation files (the "Software"), to deal in the Software without restriction, 
  including without limitation the rights to use, copy, modify, merge, publish, distribute, 
  sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in all copies or substantial 
  portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
  LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

###########################################################################################################
"""

import argparse
import datetime
import logging
import re
import sys
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

###########################################
#        VARIABLE
###########################################
DEBUG = True

###########################################
#    Methods
###########################################

def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', str(line))


def get_argument():
    global hostname, username, password, namespace, csv_filename, testrun, replicationgroup, operation

    try:
        # Setup argument parser
        parser = argparse.ArgumentParser()
        parser.add_argument('-H', '--hostname',
                            type=str,
                            help='hostname or IP address and Port',
                            required=True)
        parser.add_argument('-u', '--username',
                            type=str,
                            help='username',
                            required=True)
        parser.add_argument('-p', '--password',
                            type=str,
                            help='user password',
                            required=True)
        parser.add_argument('-n', '--namespace',
                            type=str,
                            help='namespace to work with',
                            required=True)
        parser.add_argument('-r', '--replicationgroup',
                            type=str,
                            help='replicationgroup to work with',
                            required=False)
        parser.add_argument('-o', '--operation',
                            type=str,
                            help='operation to access',
                            choices=['rc', 'buckets'],
                            required=True)
        parser.add_argument('-f', '--filename',
                            type=str,
                            help='CSV file to parse',
                            required=True)
        parser.add_argument('-t', '--testrun',
                            help='start testrun',
                            action='store_true',
                            required=False)
        args = parser.parse_args()

    except KeyboardInterrupt:
        # handle keyboard interrupt #
        return 0

    hostname = args.hostname
    username = args.username
    password = args.password
    csv_filename = args.filename
    namespace = args.namespace
    testrun = args.testrun
    replicationgroup = args.replicationgroup
    operation = args.operation


###########################################
#    CLASS
###########################################

class ecs:
    # This class permit to connect of the ECS's API

    def __init__(self):
        self.username = username
        self.password = password
        self.namespace = namespace
        self.csv_filename = csv_filename
        self.hostname = hostname.replace("https://", "").replace("HTTPS://", "")
        self.ret_classes = []
        self.buckets = []
        self.testrun = testrun
        self.replicationgroup = replicationgroup

    def get_token(self, hostname, username, password):
        try:
            # try to get token
            url = 'https://' + hostname + '/login'
            r = requests.get(url, verify=False, auth=(username, password))

            # read access token from returned header
            token = r.headers['X-SDS-AUTH-TOKEN']

            if DEBUG:
                logging.info('Token: ' + token)
            return token

        except Exception as err:
            logging.error('Not able to get token: ' + str(err))
            print(timestamp + ": Not able to get token: " + str(err))
            return ""

    def create_retentionclasses_from_list(self, hostname, username, password, namespace, ret_classes, testrun):
        # iterate through dict with retention definitions
        for rc in ret_classes:
            self.create_retentionclass(hostname, username, password, namespace, rc['name'], rc['period'], testrun)

    def create_buckets_from_list(self, hostname, username, password, buckets, testrun):
        # iterate through dict with bucket definitions
        for bucket in buckets:
            self.create_bucket(hostname, username, password, bucket['namespace'], bucket['name'], bucket['owner'],
                               testrun)

    def create_bucket(self, hostname, username, password, namespace, bucket_name, bucket_owner, testrun):

        url = 'https://' + hostname + '/object/bucket'
        try:
            # just a testrun
            if testrun:
                print(url, namespace, bucket_name, bucket_owner)

            # run against API
            else:
                # start post request
                r = requests.post(url, verify=False,
                                  headers={"X-SDS-AUTH-TOKEN": self.token, "Accept": "application/json"},
                                  json={"name": bucket_name, "namespace": namespace, "owner": bucket_owner})
                # Call was successful
                if r.status_code == 200:
                    print("SUCCESS: Bucket ", bucket_name, " in namespace ", namespace, " successfully created.")
                    logging.info(
                        "SUCCESS: Bucket " + bucket_name + " in namespace " + namespace + " successfully created.")
                    return True

                # Call wasn't successful
                else:
                    self.handle_http_error("Bucket " + bucket_name + " could not be created.", r)
                    return False

        except Exception as err:
            logging.error("Not able to create bucket: " + str(err))
            print(timestamp + ": Not able to create bucket: " + str(err))
            return False

    def create_retentionclass(self, hostname, username, password, namespace, class_name, class_period, testrun):

        url = 'https://' + hostname + '/object/namespaces/namespace/' + namespace + '/retention'
        try:
            # just a testrun
            if testrun:
                print(url, class_name, class_period)

            # run against API
            else:
                # start post request
                r = requests.post(url, verify=False,
                                  headers={"X-SDS-AUTH-TOKEN": self.token,  "Accept": "application/json"},
                                  json={"name": class_name, "period": class_period})
                # Call was successful
                if r.status_code == 200:
                    print("SUCCESS: Rentention Class ", class_name, " with period ", class_period,
                          " successfully created.")
                    logging.info("SUCCESS: Rentention Class " + class_name + " with period " + str(
                        class_period) + " successfully created.")
                    return True

                # Call wasn't successful
                else:
                    self.handle_http_error("Rentention Class ", class_name, " could not be created.", r)
                    return False
        except Exception as err:
            print("Could not create: ", class_name, str(err))
            logging.error("Could not create: " + str(class_name))
            return False

    def get_replicationgroup(self, hostname, username, password):

        # Try to get Replicaton Group
        try:
            url = 'https://' + self.hostname + '/vdc/data-service/vpools'
            # start get request
            r = requests.get(url, verify=False, headers={"X-SDS-AUTH-TOKEN": self.token, "Accept": "application/json"})
            # Call was successful
            if r.status_code == 200:
                logging.info("SUCCESS: Getting existing Replicaton Groups")
                replicationgroup = r.json()["data_service_vpool"][0]["name"]
                print("SUCCESS: Getting existing Replicaton Group: ", replicationgroup)
                logging.info("SUCCESS: Getting existing Replicaton Group: " + replicationgroup)
                return replicationgroup
            # Call wasn't successful
            else:
                self.handle_http_error("Error while resolving Replicaton Groups ", r)
                return ""
        except Exception as err:
            logging.error("Not able to get Replicaton Group: " + str(err))
            print(timestamp + ": Not able to get Replicaton Group: " + str(err))
            return ""

    def parse_rc_csv(self, csv_filename):
        ret_classes = []
        try:
            with open(csv_filename) as csv_file:
                for row in csv_file:
                    cols = row.split()
                    ret_period = 0
                    for col in cols:
                        # check if number
                        try:
                            col_number = int(col)
                        except:
                            temp = 0

                        # check which unit
                        if col in ["year", "month", "day", "hrs", "min", "years", "months", "days", "mins"]:
                            if col == "year" or col == "years":
                                seconds = 365 * 24 * 60 * 60
                            if col == "month" or col == "months":
                                seconds = 30 * 24 * 60 * 60
                            if col == "day" or col == "days":
                                seconds = 24 * 60 * 60
                            if col == "hrs":
                                seconds = 60 * 60
                            if col == "min":
                                seconds = 60
                            # increase number in seconds
                            ret_period = ret_period + col_number * seconds
                    # store retention class name and retention in seconds in dict
                    ret_classes.append({'name': cols[0], 'period': ret_period})
        except:
            ret_classes = []
        return ret_classes

    def parse_bucket_csv(self, csv_filename):
        buckets = []
        try:
            with open(csv_filename) as csv_file:
                for row in csv_file:
                    cols = row.split()
                    if len(cols) == 1:
                        buckets.append({'name': cols[0], 'namespace': self.namespace, "owner": ""})
                    if len(cols) == 2:
                        buckets.append({'name': cols[0], 'namespace': cols[1], "owner": ""})
                    if len(cols) == 3:
                        buckets.append({'name': cols[0], 'namespace': cols[1], 'owner': cols[2]})
        except:
            buckets = []
        return buckets

    def handle_http_error(self, errormessage, http_answer):

        # is description equal to details message then ignore details
        if http_answer.json()['description'].replace('"','') == http_answer.json()['details']:
            error_description = str(http_answer.json()['code']) + ":" + http_answer.json()['description']
        else:
            error_description = str(http_answer.json()['code']) + ":" + http_answer.json()['description'] + ":" + http_answer.json()['details']

        print("FAILED: " + errormessage)
        print(" --> " + error_description)

        logging.error("FAILED: " + errormessage)
        logging.error(" --> " + error_description)

def main():
    # get and test arguments
    get_argument()

    print("Start ...")
    if testrun:
        print("TESTRUN")

    sys.tracebacklimit = 0
    logging.basicConfig(filename='ECS_Mig_Helper.log', level=logging.INFO, format='%(asctime)-15s %(message)s')
    logging.info('Started')

    # display arguments if DEBUG enabled
    if DEBUG:
        logging.info("hostname: " + hostname)
        logging.info("user: " + username)
        logging.info("password: " + password)
        logging.info("csv filename: " + csv_filename)
        logging.info("namespace: " + namespace)

    if not replicationgroup:
        logging.info("replication group: not set")
    else:
        logging.info("replication group: " + replicationgroup)

    MyECS = ecs()
    MyECS.token = MyECS.get_token(hostname, username, password)
    if MyECS.token == "":
        exit(1)

    if operation == "rc":
        print("Option Retention Classes chosen")
        MyECS.ret_classes = MyECS.parse_rc_csv(csv_filename)
        if len(MyECS.ret_classes) > 0:
            MyECS.create_retentionclasses_from_list(hostname, username, password, namespace, MyECS.ret_classes, testrun)

    if operation == "buckets":
        print("Option Buckets chosen")
        MyECS.buckets = MyECS.parse_bucket_csv(csv_filename)
        if len(MyECS.buckets) > 0:
            if not replicationgroup:
                MyECS.replicationgroup = MyECS.get_replicationgroup(hostname, username, password)
            else:
                MyECS.replicationgroup = replicationgroup
            MyECS.create_buckets_from_list(hostname, username, password, MyECS.buckets, testrun)

    logging.info('Finished')


if __name__ == '__main__':
    main()
    sys.exit(0)
