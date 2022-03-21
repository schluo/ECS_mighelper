#!/usr/bin/env python3
# encoding: utf-8

__author__ = "Oliver Schlueter"
__copyright__ = "Copyright 2020, Dell Technologies"
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
    global hostaddress, username, password, namespace, csv_filename, testrun

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
        parser.add_argument('-o', '--operation',
                            type=str,
                            help='operation to access',
                            choices=['retentionclass'],
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

    hostaddress = args.hostname
    username = args.username
    password = args.password
    csv_filename = args.filename
    namespace = args.namespace
    testrun = args.testrun


###########################################
#    CLASS
###########################################

class ecs:
    # This class permit to connect of the ECS's API

    def __init__(self):
        self.user = username
        self.password = password
        self.namespace = namespace
        self.csv_filename = csv_filename
        self.hostname = hostaddress.replace("https://","").replace("HTTPS://", "")
        self.ret_classes = []
        self.testrun = testrun

    def send_post_retentionclass(self):

        try:
            # try to get token
            url = 'https://' + self.hostname + '/login'
            r = requests.get(url, verify=False, auth=(self.user, self.password))

            # read access token from returned header
            ecs_token = r.headers['X-SDS-AUTH-TOKEN']

            if DEBUG:
                logging.info('Token: ' + ecs_token)

        except Exception as err:
            logging.error('Not able to get token: ' + str(err))
            print(timestamp + ": Not able to get token: " + str(err))
            exit(1)

        # iterate through dict with retention definitions
        for rc in self.ret_classes:
            try:
                url = 'https://' + self.hostname + '/object/namespaces/namespace/' + self.namespace + '/retention'
                try:
                    # just a testrun
                    if self.testrun:
                        print(url, rc['name'], rc['period'])

                    # run against API
                    else:
                        # start post request
                        r = requests.post(url, verify=False,
                                          headers={"X-SDS-AUTH-TOKEN": ecs_token, "Content-Type": "application/json"},
                                          json={"name": rc['name'], "period": rc['period']})
                        # Call was successful
                        if r.status_code == 200:
                            print("SUCCESS: Rentention Class ", rc['name'], " with period ", rc['period'],
                                  " successfully created.")
                            logging.info("SUCCESS: Rentention Class " + str(rc['name']) + " with period " + str(
                                rc['period']) + " successfully created.")
                        # Call wasn't successful
                        else:
                            print("FAILED: Rentention Class ", rc['name'], " could not be created.")
                            print(" --> ", r.content)
                            logging.error("FAILED: Rentention Class " + rc['name'] + " could not be created.")
                            logging.error(" --> " + str(r.content))
                except:
                    print("Could not create: ", rc)
                    logging.error("Could not create: " + str(rc))

            except Exception as err:
                logging.error("Not able to create retention class: " + str(err))
                print(timestamp + ": Not able to create retention class: " + str(err))
                exit(1)

    def parse_csv(self):
        with open(self.csv_filename) as csv_file:
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
                self.ret_classes.append({'name': cols[0], 'period': ret_period})

def main():
    # get and test arguments
    get_argument()
    print("Start ...")
    if testrun:
        print("TESTRUN")
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename='ecs2checkmk.log', level=logging.INFO, format=FORMAT)
    logging.info('Started')

    # store timestamp
    global timestamp, metric_filter_file, metric_config_file
    timestamp = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")

    # display arguments if DEBUG enabled
    if DEBUG:
        logging.info("hostname: " + hostaddress)
        logging.info("user: " + username)
        logging.info("password: " + password)
        logging.info("csv filename: " + csv_filename)
        logging.info("namespace: " + namespace)
    else:
        sys.tracebacklimit = 0

    myecs = ecs()
    myecs.parse_csv()
    myecs.send_post_retentionclass()

    logging.info('Finished')


if __name__ == '__main__':
    main()
    sys.exit(0)
