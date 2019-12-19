"""Module for publishing directories / files in OS Swift."""
# Made with Python fire for easy creation, may be improved in the future.


import subprocess  # nosec
import os
import sys
import logging
import asyncio
import time

from swift_x_account_sharing.bindings.bind import SwiftXAccountSharing
from swift_sharing_request.bindings.bind import SwiftSharingRequest

import fire


logging.basicConfig()


class Publish():
    """Share and publish Openstack Swift containers."""

    @staticmethod
    def _get_address():
        """Discover the address for the object storage."""
        ret = subprocess.getoutput(["swift auth"])
        ret = ret.split("\n")[0]
        ret = ret.split("=")[1]
        return ret

    async def _push_share(self, container, recipient, rights):
        """Wrap the async share_new_access function."""
        sharing_client_url = os.environ.get("SWIFT_SHARING_URL", None)

        if not sharing_client_url:
            logging.log(
                logging.ERROR,
                "Swift Sharing APIs environment variables "
                "haven't been sourced. Please source the file if it is "
                "available, or download a new one from the storage UI."
            )

        sharing_client = SwiftXAccountSharing(sharing_client_url)

        async with sharing_client:
            await sharing_client.share_new_access(
                os.environ.get("OS_PROJECT_ID", None),
                container,
                recipient,
                rights,
                self._get_address()
            )

    async def _get_access_requests(self, container):
        """Wrap the async list_container_requests function."""
        request_client_url = os.environ.get("SWIFT_REQUEST_URL", None)
        if not request_client_url:
            logging.log(
                logging.ERROR,
                "Swift Sharing APIs environment variables "
                "haven't been sourced. Please source the file if it is "
                "available, or download a new one from the storage UI."
            )

        request_client = SwiftSharingRequest(request_client_url)

        async with request_client:
            return await request_client.list_container_requests(container)

    def share(self, container, recipient, *args):
        """Share an existing container."""
        print("share called")
        print(args)
        tenant = os.environ.get("OS_PROJECT_ID", None)
        if not tenant:
            logging.log(
                logging.ERROR,
                "Openstack RC file hasn't been sourced in the working %s%s",
                "environment. Please source an Openstack RC file to enable",
                " the use of Openstack tools."
            )
            sys.exit(-1)
        command = [
            "swift",
            "post",
            container
        ]
        rights = []
        # If read access is specified in arguments, grant read access.
        if "r" in args:
            command.append("--read-acl")
            command.append(recipient + ":*")
            rights.append("r")
            rights.append("l")
        # If write access is specified in arguments, grant write access.
        if "w" in args:
            command.append("--write-acl")
            command.append(recipient + ":*")
            rights.append("w")
        print("Running POST: %s" % command)
        subprocess.call(command)  # nosec

        if sys.version_info < (3, 7):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait([self._push_share(
                container,
                [recipient],
                rights
            )]))
        else:
            asyncio.run(self._push_share(
                container,
                [recipient],
                rights
            ))

    def publish(self, path, recipient, *args):
        """
        Upload and share a new container.

        Usage: publish [file or directory] [receiving project] [access (r, w)]
        """
        if not os.environ.get("OS_PROJECT_ID", None):
            logging.log(
                logging.ERROR,
                "Openstack RC file hasn't been sourced in the working %s%s",
                "environment. Please source an Openstack RC file to enable",
                " the use of Openstack tools."
            )
            sys.exit(-1)

        container = (
            "shared-upload-"
            + recipient
            + "-"
            + time.strftime("%Y%m%d-%H%M%S")
        )

        subprocess.call([  # nosec
            "swift",
            "upload",
            container,
            path
        ])

        self.share(container, recipient, *args)

    def publish_request(self, container, path, *args):
        """
        Upload and share a new container in response to a access request.

        Usage: publish_request [id] [file or directory] [access (r, w)]
        """
        if sys.version_info < (3, 7):
            loop = asyncio.get_event_loop()
            recipient_info = loop.run_until_complete(
                asyncio.gather(*[self._get_access_requests(
                    container
                )])
            )
            recipient_info = recipient_info[0]
        else:
            recipient_info = asyncio.run(self._get_access_requests(
                container
            ))

        subprocess.call([  # nosec
            "swift",
            "upload",
            container,
            path
        ])

        for request in recipient_info:
            if request["owner"] == os.environ.get("OS_PROJECT_ID"):
                self.share(container, request["user"], *args)


def main():
    """Run publishing module."""
    fire.Fire(Publish)


if __name__ == "__main__":
    fire.Fire(Publish)
