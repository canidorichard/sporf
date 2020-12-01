#!/usr/bin/env python3

# Copyright (c) 2019, Richard Hughes All rights reserved.
# Released under the BSD license. Please see LICENSE.md for more information.

import sys
import os
import argparse
import glob
import threading
import subprocess
import urllib.parse
from queue import Queue
from datetime import datetime

# Define command line arguments
parms=argparse.ArgumentParser()
parms.add_argument("-c", "--cmd", type=str, required=True, help="Command to execute")
parms.add_argument("-f", "--file", type=str, required=True, help="Specify input file")
parms.add_argument("-n", "--num_processes", type=int, required=False, default="32", help="Number of concurrent processes")
parms.add_argument("-p", "--path", type=str, required=False, default=".", help="Specify location of input file")
parms.add_argument("-t", "--test_only", required=False, action="store_true", help="Do not execute commands")
args = vars(parms.parse_args())

# Globals
cmdqueue=Queue()

# Main processing
def main(args):
  # Get current date and time
  timestamp = datetime.now()
  
  # Open file of parameters to populate command template
  lines = open(args['path'] + "/" + args['file'], "r")

  # Split input into parameters to build commend
  for line in lines:
    line=line.rstrip()
    parmlist=line.split("|")

    # Build command to execute
    cmdline=args['cmd']
    for idx in range(len(parmlist)):
      cmdline=cmdline.replace("{NOW}", timestamp.strftime('%Y%m%d-%H%M%S'))
      cmdline=cmdline.replace("{"+str(idx)+"}", parmlist[idx])
      cmdline=cmdline.replace("{URL:"+str(idx)+"}", urllib.parse.quote(parmlist[idx]).replace("/","%2F"))

    # Append command to list
    cmdqueue.put(cmdline)

  # Process
  process(args['num_processes'])


# Process command queue
def process(num_processes):

  # Create new threads
  threadlist=[]
  for threadnum in range(num_processes):
    threadlist.append(threading.Thread(target=thread_function))
    threadlist[threadnum].start()

  # Join threads
  for threadnum in range(num_processes):
    threadlist[threadnum].join()


# Thread function
def thread_function():
  while not cmdqueue.empty():
    if not cmdqueue.empty():
      c=cmdqueue.get_nowait()
      if args['test_only']:
        print(c)
      else:
        # Use subprocess.call if Python version < 3.5
        rc=0
        if sys.version_info[0] < 5:
            rc=subprocess.call(c,shell=True)
        else:
            p=subprocess.run(c,shell=True)
            rc=p.returncode
        if not rc == 0:
            print("Return Code: " + str(rc) + " - " + c, file=sys.stderr)


if __name__ == '__main__':
  # Execute main method
  main(args)
