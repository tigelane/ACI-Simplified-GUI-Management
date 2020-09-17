# ACI Simplified GUI Management
Building simplified interfaces to complex systems

![Production](https://github.com/tigelane/ACI-Simplified-GUI-Management/workflows/Production/badge.svg)
![Branch](https://github.com/tigelane/ACI-Simplified-GUI-Management/workflows/Branch/badge.svg)

# Building the Container
Using the standard library argparse control the container
* ./dock.py build - Build the initial container image
* ./dock.py rebuild - Force a rebuild of the container image using the no-cache setting
* ./dock.py start - Start the container
* ./dock.py stop - Stop the container
* ./dock.py delete - Delete the container (not the image)
* ./dock.py restart - Stop and start the running container

# Creating a Personal Access Token
The github module uses an OATH token.  You it does not support using github password.  The permissions needed are:

* user
* public_repo
* repo
* repo_deployment
* repo:status
* read:repo_hook
* read:org
* read:public_key
* read:gpg_key

It may work with less, but these are the permissions it was tested with.

[Github OATH Token Permissions](https://developer.github.com/v4/guides/forming-calls/#authenticating-with-graphql)