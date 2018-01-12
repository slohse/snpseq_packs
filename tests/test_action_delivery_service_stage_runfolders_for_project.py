import mock

from st2tests.base import BaseActionTestCase
from arteria_delivery_service import ArteriaDeliveryService
from arteria_delivery_service import ArteriaDeliveryServiceHandler

class ArteriaDeliveryServiceTest(BaseActionTestCase):
    action_cls=ArteriaDeliveryService

    class MockPostResponse:
        def __init__(self, mock_response_post):
            self.response_post=mock_response_post

        def __getitem__(self, key):
            return self.response_post[key]

    class MockGetResponse:
        def __init__(self, mock_response_get):
            self.response_get=mock_response_get

        def __getitem__(self, key):
            return self.response_get[key]


    def test_stage_runfolders_for_project(self):
        fake_delivery_base_api_url = 'http://foo.bar/delivery'
        fake_irma_api_key = "theKey"
        sleep_time=3

        mock_response_post={'staged_data': [{'name': 'ABC_123',
                                              'path': '/foo/160930_ST-E00216_0112_BH37CWALXX/Projects/ABC_123',
                                              'runfolder_name': '160930_ST-E00216_0112_BH37CWALXX',
                                              'runfolder_path': '/foo/160930_ST-E00216_0112_BH37CWALXX'},
                                             {'name': 'ABC_123',
                                              'path': '/foo/160930_ST-E00216_0111_BH37CWALXX/Projects/ABC_123',
                                              'runfolder_name': '160930_ST-E00216_0111_BH37CWALXX',
                                              'runfolder_path': '/foo/160930_ST-E00216_0111_BH37CWALXX'}],
                            'staging_order_ids': {'ABC_123': 484},
                            'staging_order_links': {'ABC_123': 'http://130.238.178.29:8080/api/1.0/stage/484'}}

        mock_response_get={'size': 1060, 'status': 'staging_successful'}

        with mock.patch.object(ArteriaDeliveryServiceHandler, '_post_to_server',
                               return_value=self.MockPostResponse(mock_response_post)), \
             mock.patch.object(ArteriaDeliveryServiceHandler, '_get_from_server',
                               return_value=self.MockGetResponse(mock_response_get)):

            action_instance=self.get_action_instance()

            exit_status, result=action_instance.run(action="stage_runfolders_for_project",
                                                    delivery_base_api_url=fake_delivery_base_api_url,
                                                    irma_api_key=fake_irma_api_key,
                                                    sleep_time=sleep_time,
                                                    project_name='ABC_123',
                                                    mode='FORCE')

            expected_result={'ABC_123': {'size': 1060,
                                        'staged_data': ['/foo/160930_ST-E00216_0112_BH37CWALXX/Projects/ABC_123',
                                                        '/foo/160930_ST-E00216_0111_BH37CWALXX/Projects/ABC_123'],
                                        'staging_id': 484,
                                        'successful': True}}

            self.assertEqual(result, expected_result)
            self.assertTrue(exit_status)

