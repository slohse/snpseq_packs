import os
import requests
import json
import sys
import subprocess
import yaml
import argparse
from datetime import datetime

class GetTraces:
    
    def __init__(self, api_base_url, access_headers, req_verify, workflow):
        self.api_base_url = api_base_url
        self.headers = access_headers
        self.verify = req_verify
        self.workflow = workflow
    
    def get_executions_for_tag(self, tag):
        traces_response = requests.get(
            "{}/{}/?{}={}".format(self.api_base_url, "traces", "trace_tag", tag),
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
    
    def filter_and_order_actions_by_name(self, actions):
        filtered_actions = (action for action in actions if self.workflow in action["action"]["name"])
        def get_start_time(action):
            start_time = datetime.strptime(action['start_timestamp'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            return start_time
        sort_actions = sorted(filtered_actions, key = get_start_time)
        return sort_actions

    def get_sorted_actions_from_tag(self, tag):
        executions = self.get_executions_for_tag(tag)
        actions = self.get_actions_from_executions(executions)
        return self.filter_and_order_actions_by_name(actions)

class PickRunfolder:
    
    def __init__(self, config):
        with open(config, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
        self.hosts = cfg['runfolder_svc_urls']

    def load_folders(self):
        for host in self.hosts:
            url_base = '/'.join(host.split('/')[:-1])
            result = requests.get("{}?state=*".format(url_base))
            result_json = json.loads(result.text)
     for runfolder in result_json["runfolders"]:
         yield runfolder

    def choose_runfolder(self, search_term):
        all_runfolders = self.load_folders()
        folders = {}
        states = {}
        choice = 0
        hitcount = 0
        outstring = "\n\tstatus\trunfolder_link\n"
        for runfolder in all_runfolders:
            link = runfolder["link"]
            state = runfolder["state"]
            if search_term in link and not "rchive" in link and not "biotank" in link:
                hitcount += 1
                dirs = link.split('/')
                folders[hitcount] = dirs[-1]
                states[hitcount] = state
                outstring += "{}\t{}\t{}\n".format(hitcount, state, folders[hitcount])
        
        if hitcount < 1:
            raise ValueError("No hit")
        if hitcount > 1:
            print outstring
            choice = int(raw_input("Which runfolder to trace: "))
        else:
            choice = 1
        return folders[choice], states[choice]

def get_executions(actions):
    for a in actions:
        bashCommand = "st2 execution get {}".format(a["id"])
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE) 
        return process.communicate()

        
def print_stackstorm_id(sorted_actions):
    for a in sorted_actions:
        print a["id"]
        

if __name__ == "__main__":

    # Try to load access token from environment - fall back if not available
    try:
        access_token = os.environ['ST2_AUTH_TOKEN']
    except KeyError:
            print("Could not find ST2_AUTH_TOKEN in environment. "
                "Please set it to your st2 authentication token.")
    access_headers = {"X-Auth-Token": access_token}
        
    # parse the input
    parser = argparse.ArgumentParser(description="Gets execution ids associated with a flowcell "
                                     "(e.g. a runfolder) and a workflow. It is used to trace the flowcell"
                                     "--flowcell 000000000-ABGT6_testbio14 ")
    parser.add_argument('--flowcell', required=True, help='Specify the flowcell you want to trace. E.g. --flowcell HTTT3CCXY')
    parser.add_argument('--noverify', action="store_false")
    parser.add_argument('--api_base_url', default="http://localhost:9101/v1")
    parser.add_argument('--config', default="/opt/stackstorm/packs/snpseq_packs/config.yaml")
    parser.add_argument('--workflow', default="workflow")
    args = parser.parse_args()

    # find the runfolder to trace
    runfolder = PickRunfolder(args.config)
    try:
        folder2trace, folder_state = runfolder.choose_runfolder(args.flowcell)
    except ValueError: 
        print "\n\tNo hits found, will terminate.\n"
        sys.exit()
    print "Will trace {}.".format(folder2trace)

    # trace the runfolder
    myTraces = GetTraces(args.api_base_url, access_headers, args.noverify, args.workflow)
    sorted_actions = myTraces.get_sorted_actions_from_tag(folder2trace)
    
    # output the result
    output, error = get_executions(sorted_actions)
    print output
    
    # will add a line with the folder name at the end of the output.
    print "    {} [{}]\n".format(folder2trace, folder_state)
    
    sys.exit()
