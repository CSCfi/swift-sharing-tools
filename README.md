### Swift sharing tools

### Installation
```pip install git+https://github.com/CSCfi/swift-sharing-tools```

Contains following tools:
- swift-publish

### Usage
#### swift-publish
Using swift-publish requires an Openstack project file to be sourced in the
working terminal (the file containing Openstack user information for related
project). Following additional information needs to be passed via environment
variables:
```
SWIFT_SHARING_URL="http://example"; REQUIRED; The url containing the sharing related APIs.
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
./[OpenStack RC File]
```
