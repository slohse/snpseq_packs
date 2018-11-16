#!/usr/bin/env python

from st2actions.runners.pythonrunner import Action

from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
from lib.supr_utils import * 

#disable ssl warnings
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


class CheckClarityContactsInSupr(Action):
    """
    Retrives contacts from open projects in ClarityLIMS and checks for
    SUPR accounts by email.
    Then composes an email body to notify project coordinators.
    """

    def fetch_open_projects(self):
        lims = Lims(BASEURI, USERNAME, PASSWORD)
        lims.check_version()
        projects = lims.get_projects() 
	filtered_projects = list()
	for project in projects:
		if project.open_date and not project.close_date:
			filtered_projects.append(project)
        return filtered_projects

    def check_email_in_supr(self, email_adress):
        email_missing = False
        email_multi = False

        try:
            pi_id = SuprUtils.search_by_email(self.supr_base_url, email_adress, self.supr_user, self.supr_key)
        except AssertionError as ae:
            if ("no hits" in ae.message):
                email_missing = True
            elif ("more than one" in ae.message):
                email_multi = True

        return (email_missing, email_multi)

    def run(self): #supr_base_url, supr_user, supr_key
        #TODO:debug vars, remove
	supr_base_url = "https://supr.snic.se/api"
	supr_user = "api-2"
	supr_key= "Acgxd6Hvns"

        self.supr_base_url = supr_base_url
        self.supr_user = supr_user
        self.supr_key = supr_key

        projects = self.fetch_open_projects()
	email_body = ""
        debug_break = 30 #TODO: remove
	for project in projects:
            pi_missing = False
            pi_multi = False
            bio_missing = False
            bio_multi = False

            debug_break =- 1        #TODO: remove
            if (debug_break == 0):
                break

            pi_email = project.udf.get("Email of PI")
            bio_email = project.udf.get("Email of bioinformatics responsible person")
            #primary_email = project.udf.get("Email of primary contact")
            if (pi_email):
                (pi_missing, pi_multi) = self.check_email_in_supr(pi_email) 
  
            if (bio_email):
                (bio_missing, bio_multi) = self.check_email_in_supr(bio_email)
 
            if (pi_missing or pi_multi or bio_missing or bio_multi):
                pi_name = project.udf.get("Name of PI")
                if (not pi_name):
                    pi_name = "Name missing from LIMS"
                bio_name = project.udf.get("Name of bioinformatics responsible person")
                if (not bio_name):
                    bio_name = "Name missing from LIMS"
                email_body += "<hr>Project: " + project.name + ": <br><br>"

                if (pi_missing):
                    email_body += "PI missing from SUPR ( " + pi_name + ", " + pi_email + " )<br>"
                if (pi_multi):
                    email_body += "PI has multiple accounts in SUPR ( " + pi_name + ", " + pi_email + " )<br>"
                if (bio_missing):
                    email_body += "BIO missing from SUPR ( " + bio_name + ", " + bio_email + " )<br>"
                if (bio_multi):
                    email_body += "BIO has multiple accounts in SUPR ( " + bio_name + ", " + bio_email + " )<br>"

        return (True, email_body)



