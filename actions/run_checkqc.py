#!/usr/bin/env python

import requests
import json
from requests.exceptions import RequestException

# Needs to be run in a Stackstorm virtualenv
from st2actions.runners.pythonrunner import Action

class runCheckQC(Action):

    def query(self, url, verify_ssl_cert):
        try:
            response = requests.get(url, verify=verify_ssl_cert)
            return response
        except RequestException as err:
            self.logger.error("An error was encountered when "
                              "querying url: {0},  {1}".format(url, err))
            raise err

    def run(self, url, ignore_result, verify_ssl_cert):
        response = self.query(url, verify_ssl_cert).json()
        exit_status = response["exit_status"]
        if (ignore_result & exit_status != 0):
            self.logger.warning("Ignoring the failed result because of override flag.")
            return True, response
        elif (exit_status == 0):
            return True, response
        else:
            return False, response
