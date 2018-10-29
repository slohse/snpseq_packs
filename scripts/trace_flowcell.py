import os
import requests
import json
import sys
import subprocess
import yaml
import argparse
from datetime import datetime

class GetStuff:
    def __init__(self, api_base_url, access_headers, req_verify, workflow, tag):
        self.api_base_url = api_base_url
        self.headers = access_headers
        self.verify = req_verify
        self.workflow = workflow
        self.tag = tag
    
    def get_executions_for_tag(self):
        traces_response = requests.get(
            "{}/{}/?{}={}".format(self.api_base_url, "traces", "trace_tag", self.tag),
            verify = self.verify,
            headers = self.headers)
        if not traces_response.ok:
            raise Exception("Response not OK, got: " + traces_response.text)
        traces = json.loads(traces_response.text)
        for trace in traces:
            trace_id = trace["id"]
            trace_info_response = requests.get(
                "{}/{}/{}".format(self.api_base_url, "traces", trace_id),
                verify = self.verify,
                headers = self.headers)
            trace_info = json.loads(trace_info_response.text)
            action_executions = map(lambda x: x["object_id"], trace_info["action_executions"])
            for execution in action_executions:
                yield execution

    def get_actions_from_executions(self, executions):
        for execution_id in executions:
            execution_info_response = requests.get(
                "{}/{}/{}".format(self.api_base_url, "executions", execution_id),
                verify = self.verify,
                headers = self.headers)
            execution_info = json.loads(execution_info_response.text)
            yield execution_info
    
    def filter_actions_by_name(self, actions):
        filtered_actions = (action for action in actions if self.workflow in action["action"]["name"])
        def get_start_time(action):
            start_time = datetime.strptime(action['start_timestamp'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            return start_time
        sort_actions = sorted(filtered_actions, key = get_start_time)
        return sort_actions


class Runfolders:
    def __init__(self):

        with open(args.config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        hosts = cfg['runfolder_svc_urls']

        self.hitcount = 0
        for host in hosts:
            url_base = '/'.join(host.split('/')[:-1])
            result = requests.get("{}?state=*".format(url_base))
            result_json = json.loads(result.text)
            self.all_runfolders = result_json["runfolders"]

    def pick_runfolder(self, search_term):
        folders = {}
        states = {}
        choice = 0
        hitcount = 0
        outstring = "\n\tstatus\trunfolder_link\n"
        for runfolder in self.all_runfolders:
            link = runfolder["link"]
            state = runfolder["state"]
            if search_term in link and not "rchive" in link and not "biotank" in link:
                hitcount += 1
                dirs = link.split('/')
                folders[hitcount] = dirs[-1]
                states[hitcount] = state
                outstring += "{}\t{}\t{}\n".format(hitcount, state, folders[hitcount])
        
        if hitcount < 1:
            return 42
        if hitcount > 1:
            print outstring
            choice = int(raw_input("Which runfolder to trace: "))
            return folders[choice], states[choice]
        else:
            return folders[1], states[1]


def print_stackstorm_output(sorted_actions):
    for a in sorted_actions:
        bashCommand = "st2 execution get {}".format(a["id"])
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE) 
        output, error = process.communicate()
        print output
        
def print_stackstorm_id(sorted_actions):
    for a in sorted_actions:
        print a["id"]
        

if __name__ == "__main__":

    # Try to load access token from environment - fall back if not available
    try:
        access_token = os.environ['ST2_AUTH_TOKEN']
    except KeyError as e:
            print("Could not find ST2_AUTH_TOKEN in environment. "
                "Please set it to your st2 authentication token.")
    access_headers = {"X-Auth-Token": access_token}
        
    # parse the input
    parser = argparse.ArgumentParser(description="Gets execution ids associated with a flowcell "
                                     "(e.g. a runfolder) and a workflow. It can be used to track "
                                     "executions, e.g: python scripts/trace_flowcell.py "
                                     "--flowcell 000000000-ABGT6_testbio14 ")
    parser.add_argument('--flowcell',     required=True)
    parser.add_argument('--noverify',     action="store_false")
    parser.add_argument('--api_base_url', default="http://localhost:9101/v1")
    parser.add_argument('--config',       default="/opt/stackstorm/packs/snpseq_packs/config.yaml")
    parser.add_argument('--workflow',     default="workflow")
    args = parser.parse_args()

    # find the runfolder to trace
    get_runfolder = Runfolders()
    try:
        folder2trace, folder_state = get_runfolder.pick_runfolder(args.flowcell)
    except TypeError:
        print "\n\tNo hits found, will terminate.\n"
        sys.exit()
    print "Will trace {}.".format(folder2trace)

    # trace the runfolder
    find = GetStuff(args.api_base_url, access_headers, args.noverify, args.workflow, folder2trace)
    executions = find.get_executions_for_tag()
    actions = find.get_actions_from_executions(executions)
    sorted_actions = find.filter_actions_by_name(actions)
    
    # output the result
    try:
        print_stackstorm_output(sorted_actions)
    except OSError:
        print "\nIt looks as if stackstorm [st2] is unavailable. I will just list the IDs:"
        print_stackstorm_id(sorted_actions)
    
    # will add a line with the folder name at the end of the output.
    print "    {} [{}]\n".format(folder2trace, folder_state)
    
    sys.exit()
