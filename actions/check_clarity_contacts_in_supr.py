#!/usr/bin/env python

from st2actions.runners.pythonrunner import Action

from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
from lib.supr_utils import * 


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

    def check_email_in_supr(email_adress):
    	supr_utils.search_by_email(base_url, email_adress, user, key)


    def run(self): #supr_base_api_url, api_user, api_key
        #fetch projects
        projects = self.fetch_open_projects()
	for project in projects:
		pi_email = project.udf.get("Email of PI")
		bio_email = project.udf.get("Email of bioinformatics responsible person")
		#primary_email = project.udf.get("Email of primary contact")

		if (pi_email):
			check_email_in_supr(pi_email)




		print "---------------------"
		print project.open_date
		print project.close_date
		print "---------------------"
        #Retrieve contacs

        #Check SUPR
