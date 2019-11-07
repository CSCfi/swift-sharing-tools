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
