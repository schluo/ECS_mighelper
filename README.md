# ECS_mighelper
Command line tool to support CAS to ECS Migrations

### usage
    ecs_mig_tool.exe [-h] -H HOSTNAME -u USERNAME -p PASSWORD -n NAMESPACE -o {retentionclass} -f FILENAME [-t] *

    optional arguments:
    -h, --help                                          Show this help message and exit
    -H HOSTNAME, --hostname HOSTNAME                    Mgmt API target hostname or IP address and Port
    -u USERNAME, --username USERNAME                    API username
    -p PASSWORD, --password PASSWORD                    API User Password
    -n NAMESPACE, --namespace NAMESPACE                 namespace to work with
    -o {retentionclass}, --operation {retentionclass}   operation to access
    -f FILENAME, --filename FILENAME                    CSV file to parse
    -t, --testrun                                       Start testrun without creating retenion classes

### Example
    python3 -H ecstest:4443 -u admin -p ChangeMe -o retentionclass -f retentions.txt -n namespace_test
---
  
### Copyright (c) 2022 Dell Technologies

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
