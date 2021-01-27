"""Module for publishing directories / files in OS Swift."""
# Made with Python fire for easy creation, may be improved in the future.


import subprocess  # nosec
import os
import sys
import logging
import asyncio
import time
import typing
from pathlib import Path

from swift_x_account_sharing.bindings.bind import SwiftXAccountSharing
from swift_sharing_request.bindings.bind import SwiftSharingRequest

import fire


logging.basicConfig()


class Publish():
    """Share and publish Openstack Swift containers."""

    @staticmethod
    def _get_address() -> str:
        """Discover the address for the object storage."""
        ret = subprocess.getoutput(["swift auth"])  # type: ignore
        ret = ret.split("\n")[0]
        ret = ret.split("=")[1]
        return ret

    @staticmethod
    def _check_large_files(
            path: str
    ) -> bool:
        """Check if folder contains large files."""
        p = Path(path)
        gb = int(os.environ.get("SWIFT_SHARING_UPLOAD_SEGMENT_SIZE",
                                1024 * 1024 * 1024 * 5))
        result = False
        if p.is_dir():
            _files = [i.stat().st_size
                      for i in p.glob('**/*') if i.is_file()]
            result = True if any(t > gb for t in _files) else False
        elif p.is_file():
            result = True if p.stat().st_size > gb else False

        return result

    async def _push_share(
            self,
            container: str,
            recipient: typing.List[str],
            rights: typing.List[str]
    ) -> None:
        """Wrap the async share_new_access function."""
        sharing_client_url = os.environ.get("SWIFT_SHARING_URL", None)

        if not sharing_client_url:
            logging.log(
                logging.ERROR,
                "Swift Sharing APIs environment variables "
                "haven't been sourced. Please source the file if it is "
                "available, or download a new one from the storage UI."
            )
            sys.exit(-1)

        sharing_client = SwiftXAccountSharing(sharing_client_url)

        async with sharing_client:
            try:
                await sharing_client.share_new_access(
                    os.environ.get("OS_PROJECT_ID", None),
                    container,
                    recipient,
                    rights,
                    self._get_address()
                )
            except AttributeError:
                logging.log(
                    logging.ERROR,
                    "Swift SharingAPIs environment variables "
                    "haven't been sourced. Please source the file if it is "
                    "available, or download a new one from the storage UI."
                )
                sys.exit(-1)

    async def _get_access_requests(
            self,
            container: str
    ) -> typing.List[dict]:
        """Wrap the async list_container_requests function."""
        request_client_url = os.environ.get("SWIFT_REQUEST_URL", None)
        if not request_client_url:
            logging.log(
                logging.ERROR,
                "Swift Sharing APIs environment variables "
                "haven't been sourced. Please source the file if it is "
                "available, or download a new one from the storage UI."
            )
            sys.exit(-1)

        request_client = SwiftSharingRequest(request_client_url)

        async with request_client:
            try:
                return await request_client.list_container_requests(container)
            except AttributeError:
                logging.log(
                    logging.ERROR,
                    "Swift SharingAPIs environment variables "
                    "haven't been sourced. Please source the file if it is "
                    "available, or download a new one from the storage UI."
                )
                sys.exit(-1)

    def share(
            self,
            container: str,
            recipient: str,
            *args: typing.Any
    ) -> None:
        """Share an existing container."""
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

    def publish(
            self,
            path: str,
            recipient: str,
            *args: typing.Any
    ) -> None:
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
            "shared-upload-" +
            recipient +
            "-" +
            time.strftime("%Y%m%d-%H%M%S")
        )

        subprocess.call([  # nosec
            "swift",
            "upload",
            container,
            "-S",
            str(os.environ.get("SWIFT_SHARING_UPLOAD_SEGMENT_SIZE",
                               1024 * 1024 * 1024 * 5)),  # Default to 5GiB
            path
        ])

        self.share(container, recipient, *args)

        # If performed a segmented upload, also share the segments
        if self._check_large_files(path):
            self.share(f"{container}_segments", recipient, *args)

    def publish_request(
            self,
            container: str,
            path: str,
            *args: typing.Any
    ) -> None:
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
            "-S",
            str(os.environ.get("SWIFT_SHARING_UPLOAD_SEGMENT_SIZE",
                               1024 * 1024 * 1024 * 5)),  # Default to 5GiB
            path
        ])

        for request in recipient_info:
            if request["owner"] == os.environ.get("OS_PROJECT_ID"):
                self.share(container, request["user"], *args)

                # If performed a segmented upload, aso share the segments
                if self._check_large_files(path):
                    self.share(f"{container}_segments", request["user"], *args)


def main() -> None:
    """Run publishing module."""
    try:
        fire.Fire(Publish)
    except Exception as e:
        print(f"An error ocurred: {e}")


if __name__ == "__main__":
    main()
