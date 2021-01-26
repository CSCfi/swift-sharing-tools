![Python style check](https://github.com/CSCfi/swift-sharing-tools/workflows/Python%20style%20check/badge.svg)
![Python Unit Tests](https://github.com/CSCfi/swift-sharing-tools/workflows/Python%20Unit%20Tests/badge.svg)

### Swift sharing tools

### Installation
```
pip install git+https://github.com/CSCfi/swift-sharing-tools
# test the command has installed correctly
# the command below should display the help message on command line
swift-publish --help
```

Contains following tools:
- swift-publish
    + `share`: Share an existing container to a project
    + `publish`: Upload and share a folder / files to a project
    + `publish-request`: fulfill a request for a container with specified files

### Usage

#### swift-publish
Using swift-publish requires an Openstack project file to be sourced in the
working terminal (the file containing Openstack user information for related
project). Following additional information needs to be passed via environment
variables:
```
SWIFT_SHARING_URL="http://example"; Required for sharing functionality.
SWIFT_REQUEST_URL="http://example"; Required for fulfilling sharing requests.
SWIFT_UI_API_KEY="example_key"; Required for API access.
```

The Openstack RC file can be found from the Openstack UI, aka Horizon. It
can be found in the following location after logging in:
```
Access & Security -> API Access -> Download OpenStack RC File v3
```

After the OpenStack RC File has been downloaded, it should be run with the
following commands:
```
chmod u+x [OpenStack RC File]
. ./[OpenStack RC File]
```

Remember that the RC files are project specific, so you can't use them to
upload from anything else besides your currently active project.

Example command, for fulfilling a request for new container, with read access:
```
swift-publish publish-request container_name folder_name r
```

Example command, for uploading a file or folder to another project with read and write access (need to be separated by space):
```
swift-publish publish file_or_folder_name os_project_id r w
```

Example command, for sharing a file or folder to another project with read and write (need to be separated by space):
```
swift-publish share container_name os_project_id r w
```
