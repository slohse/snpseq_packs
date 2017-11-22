import csv
import os
import tempfile

from st2tests.base import BaseActionTestCase
from read_projects_email_file import ReadProjectsEmailFile


class ReadProjectsEmailFileTestCase(BaseActionTestCase):
    action_cls = ReadProjectsEmailFile

    projects_email_file = None
    project_emails = {
        "AA-0001": {"email": "this.is.a.pi@email.com", "sensitive": False, "members": []},
        "BB-0002": {"email": "this.is.a.pi@email.com", "sensitive": True, "members": []},
        "CC-0003": {"email": "this.is.a.pi@email.com", "sensitive": False, "members": ["this.is.member.1@email.com"]},
        "DD-0004": {"email": "this.is.a.pi@email.com", "sensitive": True,
                    "members": ["this.is.member.1@email.com", "this.is.member.2@email.com"]}
    }

    @classmethod
    def setUpClass(cls):
        # write some content to a project email file
        fd, projects_email_file = tempfile.mkstemp(suffix=".csv", prefix="test_read_projects_email_file")
        with os.fdopen(fd) as csvh:
            csv_writer = csv.DictWriter(csvh, delimiter=";", fieldnames=["project", "email", "members", "sensitive"])
            csv_writer.writeheader()
            for proj, email in cls.project_emails.items():
                row = dict(email)
                row["project"] = proj
                row["members"] = ",".join(email["members"])
                csv_writer.writerow(row)
        cls.projects_email_file = projects_email_file

    def run_with_params(self, expected_exit_status, expected_result, *args):
        observed_exit_status, observed_result = self.get_action_instance().run(self.projects_email_file, *args)
        self.assertTrue(observed_exit_status == expected_exit_status)
        self.assertDictEqual(expected_result, observed_result)

    def test_run_with_all_projects(self):
        expected_exit_status = True
        expected_result = self.project_emails
        self.run_with_params(
            expected_exit_status,
            expected_result,
            {"projects": expected_result.keys()},
            "keep_all_projects")

    def test_run_with_some_projects(self):
        restrict_to_projects = "AA-0001,DD-0004"
        expected_exit_status = True
        expected_result = {
            proj: email for proj, email in self.project_emails.items() if proj in restrict_to_projects.split(",")}
        self.run_with_params(
            expected_exit_status,
            expected_result,
            {"projects": expected_result.keys()},
            restrict_to_projects)

    def test_run_with_missing_project(self):
        expected_exit_status = False
        expected_result = {}
        self.run_with_params(
            expected_exit_status,
            expected_result,
            {"projects": "this-project-is-not-in-file"},
            "keep_all_projects")

    def test_str_to_bool(self):
        for exp in (True, False):
            self.assertEqual(exp, self.get_action_instance().str_to_bool(str(exp)))
        with self.assertRaises(ValueError):
            self.get_action_instance().str_to_bool("Not a bool")
