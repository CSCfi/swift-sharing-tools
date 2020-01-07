"""Unit tests for sharing tools."""


import unittest


import asynctest
import fire


from swift_sharing_tools.publish import Publish, main


class BaseAsyncioContextManager():
    """Base class for asyncio context managers."""

    async def __aenter__(self, *args, **kwargs):
        """."""

    async def __aexit__(self, *excinfo):
        """."""


class MockSharingClient(BaseAsyncioContextManager):
    """Mock class for the sharing client."""

    def __init__(self):
        """."""
        self.share_new_access = asynctest.CoroutineMock()


class MockSharingClientError(BaseAsyncioContextManager):
    """Mock class for the sharing client when raising an error."""

    def __init__(self):
        """."""
        self.share_new_access = asynctest.CoroutineMock(
            side_effect=AttributeError
        )


class MockRequestClient(BaseAsyncioContextManager):
    """Mock class for the request client."""

    def __init__(self):
        """."""
        self.list_container_requests = asynctest.CoroutineMock(
            return_value=None
        )


class MockRequestClientError(BaseAsyncioContextManager):
    """Mock class for request client when raising an error."""

    def __init__(self):
        """."""
        self.list_container_requests = asynctest.CoroutineMock(
            side_effect=AttributeError
        )


class PublishTestCase(asynctest.TestCase):
    """Tests for sharing tools class."""

    def setUp(self):
        """Set up relevant mocks."""
        self.inst = Publish()

        self.os_environ_get_mock = unittest.mock.Mock(
            return_value="http://example"
        )
        self.os_environ_get_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.os.environ.get",
            new=self.os_environ_get_mock
        )

        self.get_address_mock = unittest.mock.Mock(
            return_value="http://example"
        )
        self.patch_get_address = unittest.mock.patch(
            "swift_sharing_tools.publish.Publish._get_address",
            new=self.get_address_mock
        )

        self.sys_exit_mock = unittest.mock.Mock(
            side_effect=SystemExit
        )
        self.sys_exit_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.sys.exit",
            self.sys_exit_mock
        )

        self.mock_sharing_client = MockSharingClient()
        self.mock_init_sharing_client = unittest.mock.Mock(
            return_value=self.mock_sharing_client
        )
        self.patch_init_sharing_client = unittest.mock.patch(
            "swift_sharing_tools.publish.SwiftXAccountSharing",
            new=self.mock_init_sharing_client
        )

        self.mock_sharing_client_error = MockSharingClientError()
        self.mock_init_sharing_client_error = unittest.mock.Mock(
            return_value=self.mock_sharing_client_error
        )
        self.patch_init_sharing_client_error = unittest.mock.patch(
            "swift_sharing_tools.publish.SwiftXAccountSharing",
            new=self.mock_init_sharing_client_error
        )

        self.mock_request_client = MockRequestClient()
        self.mock_init_request_client = unittest.mock.Mock(
            return_value=self.mock_request_client
        )
        self.patch_init_request_client = unittest.mock.patch(
            "swift_sharing_tools.publish.SwiftSharingRequest",
            new=self.mock_init_request_client
        )

        self.mock_request_client_error = MockRequestClientError()
        self.mock_init_request_client_error = unittest.mock.Mock(
            return_value=self.mock_request_client_error
        )
        self.patch_init_request_client_error = unittest.mock.patch(
            "swift_sharing_tools.publish.SwiftSharingRequest",
            new=self.mock_init_request_client_error
        )

        self.subprocess_call_mock = unittest.mock.Mock()
        self.patch_subprocess_call = unittest.mock.patch(
            "swift_sharing_tools.publish.subprocess.call",
            new=self.subprocess_call_mock
        )

        self.sys_version_36_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.sys.version_info",
            new=(3, 6)
        )
        self.sys_version_38_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.sys.version_info",
            new=(3, 8)
        )

        self.push_share_mock = asynctest.CoroutineMock()
        self.patch_push_share = unittest.mock.patch(
            "swift_sharing_tools.publish.Publish._push_share",
            new=self.push_share_mock
        )

        self.get_access_requests_mock = asynctest.CoroutineMock(
            return_value=[{
                "owner": "http://example",
                "user": "test-user"
            }]
        )
        self.patch_get_access_requests = unittest.mock.patch(
            "swift_sharing_tools.publish.Publish._get_access_requests",
            new=self.get_access_requests_mock
        )

        self.share_mock = unittest.mock.Mock()
        self.share_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.Publish.share",
            new=self.share_mock
        )

        self.subprocess_getoutput_mock = unittest.mock.Mock(
            return_value="export OS_STORAGE_URL=http://example"
        )
        self.subprocess_getoutput_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.subprocess.getoutput",
            new=self.subprocess_getoutput_mock
        )

    def test_get_address(self):
        """Test the get_address static method."""
        with self.subprocess_getoutput_patch:
            ret = self.inst._get_address()
            self.assertEqual(ret, "http://example")

    async def test_push_share_no_envars(self):
        """Test _push_share method without correct environment variables."""
        with self.sys_exit_patch:
            with self.assertRaises(SystemExit):
                await self.inst._push_share(
                    "test-container",
                    "test-recipient",
                    ["r", "w"]
                )
                self.sys_exit_mock.assert_called_once()

    async def test_push_share_no_os_envars(self):
        """Test _push_share method without correct Openstack variables."""
        with self.sys_exit_patch, \
                self.patch_init_sharing_client_error, \
                self.patch_get_address, \
                self.os_environ_get_patch:
            with self.assertRaises(SystemExit):
                await self.inst._push_share(
                    "test-container",
                    "test-recipient",
                    ["r", "w"]
                )

    async def test_push_share(self):
        """Test _push_share method."""
        with self.patch_init_sharing_client, \
                self.patch_get_address, \
                self.os_environ_get_patch:
            await self.inst._push_share(
                "test-container",
                "test-recipient",
                ["r", "w"]
            )
            self.mock_sharing_client.share_new_access.assert_awaited_once()

    async def test_get_access_requests_no_envars(self):
        """Test _get_access_requests method without correct envars."""
        with self.sys_exit_patch:
            with self.assertRaises(SystemExit):
                await self.inst._get_access_requests(
                    "test-container"
                )
                self.sys_exit_mock.assert_called_once()

    async def test_get_access_requests_no_os_envars(self):
        """Test _get_access_requests method without correct OS variables."""
        with self.sys_exit_patch, \
                self.patch_init_request_client_error, \
                self.os_environ_get_patch:
            with self.assertRaises(SystemExit):
                await self.inst._get_access_requests(
                    "test-container"
                )

    async def test_get_access_requests(self):
        """Test _get_access_requests method."""
        with self.patch_init_request_client, self.os_environ_get_patch:
            await self.inst._get_access_requests(
                "test-contanier"
            )
            self.mock_request_client.list_container_requests.\
                assert_awaited_once()

    def test_share_no_os_environ(self):
        """Test share method without correct OS variables."""
        with self.sys_exit_patch:
            with self.assertRaises(SystemExit):
                self.inst.share(
                    "test-container",
                    "test-recipient",
                    "r",
                    "w"
                )
                self.sys_exit_mock.assert_called_once()

    def test_share_36(self):
        """Test share method."""
        with self.os_environ_get_patch, \
                self.patch_push_share, \
                self.patch_subprocess_call, \
                self.sys_version_36_patch:
            self.inst.share(
                "test-container",
                "test-recipient",
                "r",
                "w"
            )
            self.subprocess_call_mock.assert_called_once()
            self.push_share_mock.assert_awaited_once()

    def test_share_38(self):
        """Test share method (python version 3.8)."""
        with self.os_environ_get_patch, \
                self.patch_push_share, \
                self.patch_subprocess_call, \
                self.sys_version_38_patch:
            self.inst.share(
                "test-container",
                "test-recipient",
                "r",
                "w"
            )
            self.subprocess_call_mock.assert_called_once()
            self.push_share_mock.assert_awaited_once()

    def test_publish_no_os_environ(self):
        """Test publish method without correct OS variables."""
        with self.sys_exit_patch:
            with self.assertRaises(SystemExit):
                self.inst.publish(
                    ".",
                    "test-recipient",
                    "r",
                    "w"
                )
                self.sys_exit_mock.assert_called_once()

    def test_publish(self):
        """Test publish method."""
        with self.os_environ_get_patch, \
                self.patch_subprocess_call, \
                self.share_patch:
            self.inst.publish(
                "test-directory",
                "test-recipient",
                "r",
                "w"
            )
            self.os_environ_get_mock.assert_called_once()
            self.subprocess_call_mock.assert_called_once()
            self.share_mock.assert_called_once()

    def test_publish_request_36(self):
        """Test publish_request method (python 3.6)."""
        with self.sys_version_36_patch, \
                self.patch_get_access_requests, \
                self.patch_subprocess_call, \
                self.share_patch, \
                self.os_environ_get_patch:
            self.inst.publish_request(
                "test-container",
                "test-path",
                "r",
                "w"
            )
            self.os_environ_get_mock.assert_called_once()
            self.share_mock.assert_called_once()
            self.subprocess_call_mock.assert_called_once()
            self.get_access_requests_mock.assert_awaited_once()

    def test_publish_request_38(self):
        """Test publish_request method (python 3.8)."""
        with self.sys_version_38_patch, \
                self.patch_get_access_requests, \
                self.patch_subprocess_call, \
                self.share_patch, \
                self.os_environ_get_patch:
            self.inst.publish_request(
                "test-container",
                "test-path",
                "r",
                "w"
            )
            self.os_environ_get_mock.assert_called()
            self.share_mock.assert_called_once()
            self.subprocess_call_mock.assert_called_once()
            self.get_access_requests_mock.assert_awaited_once()

    def test_main(self):
        """Test main function."""
        fire_mock = unittest.mock.MagicMock(fire.Fire)
        fire_patch = unittest.mock.patch(
            "swift_sharing_tools.publish.fire.Fire",
            fire_mock
        )
        with fire_patch:
            main()
        fire_mock.assert_called_once()
