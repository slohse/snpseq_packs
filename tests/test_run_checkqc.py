import mock
import json
import requests

from st2tests.base import BaseActionTestCase

from run_checkqc import RunCheckQC


class RunCheckQCTestCase(BaseActionTestCase):
    action_cls = RunCheckQC

    class MockGetResponse:
        def __init__(self, mock_response, status_code):
            self.response = mock_response
            self.status_code = status_code
        def json(self):
            return self.response

    def run_checkqc(self, mock_response, status_code, expected_exit_status, ignore_result=False):

        fake_url = 'http://foo.bar/qc'

        with mock.patch.object(requests, 'get', return_value = self.MockGetResponse(mock_response, status_code)):

            action = self.get_action_instance()

            (exit_status, result) = action.run(url = fake_url,
                                               ignore_result = ignore_result,
                                               verify_ssl_cert = False)

            self.assertTrue(exit_status == expected_exit_status)

    def test_warning(self):
        mock_response = {"exit_status": 0,
                             "ClusterPFHandler": [{"type": "warning",
                                                   "message": "Cluster PF was too low on lane 1, it was: 117.93 M",
                                                   "data": {"lane": 1,
                                                            "lane_pf": 117929896,
                                                            "threshold": 180}}],
                             "run_summary": {"instrument_and_reagent_type": "hiseq2500_rapidhighoutput_v4",
                                             "read_length": "125-125",
                                             "handlers": [{"handler": "ClusterPFHandler",
                                                           "error": "unknown",
                                                           "warning": 180}]},
                             "version": "1.2.0"}
        self.run_checkqc(mock_response = mock_response, status_code = 200,
                         expected_exit_status = True, ignore_result = False)

    def test_error(self):
        mock_response = {"exit_status": 1,
                             "ClusterPFHandler": [{"type": "error",
                                                   "message": "Cluster PF was too low on lane 1, it was: 117.93 M",
                                                   "data": {"lane": 1,
                                                            "lane_pf": 117929896,
                                                            "threshold": 120}}],
                             "run_summary": {"instrument_and_reagent_type": "hiseq2500_rapidhighoutput_v4",
                                             "read_length": "125-125",
                                             "handlers": [{"handler": "ClusterPFHandler",
                                                           "error": 120,
                                                           "warning": 180}]},
                             "version": "1.2.0"}
        self.run_checkqc(mock_response = mock_response, status_code = 200,
                         expected_exit_status = False, ignore_result = False)

    def test_error_ignore_result(self):
        mock_response = {"exit_status": 1,
                             "ClusterPFHandler": [{"type": "error",
                                                   "message": "Cluster PF was too low on lane 1, it was: 117.93 M",
                                                   "data": {"lane": 1,
                                                            "lane_pf": 117929896,
                                                            "threshold": 120}}],
                             "run_summary": {"instrument_and_reagent_type": "hiseq2500_rapidhighoutput_v4",
                                             "read_length": "125-125",
                                             "handlers": [{"handler": "ClusterPFHandler",
                                                           "error": 120,
                                                           "warning": 180}]},
                             "version": "1.2.0"}
        self.run_checkqc(mock_response = mock_response, status_code = 200,
                         expected_exit_status = True, ignore_result = True)

    def test_status_code_not_200(self):
        mock_response = {"reason": "There is a problem with the qc config."}
        self.run_checkqc(mock_response = mock_response, status_code = 500,
                         expected_exit_status = False, ignore_result = False)

    def test_ignore_status_code_not_200(self):
        mock_response = {"reason": "There is a problem with the qc config."}
        self.run_checkqc(mock_response = mock_response, status_code = 500,
                         expected_exit_status = True, ignore_result = True)

