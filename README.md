# MyPaas

MyPaas is a tool that makes it easy to run a platform as a service (PAAS)
on your own VM or hardware. It combines Traefik and Docker, and offers free
automatic https and deployments via dockerfiles.

*DISCLAIMER: none of what is described below actually works yet - this document is what I'd want MyPaas to do.*

## Docker plus Traefik is awesome

Docker makes it possible to run multiple applications on a single server
in a contained way, and setting (memory and CPU) limits on each container.

Traefik is a modern router, reverse proxy, and load balancer that can be
automatically configured using labels on Docker containers. It can also act
as an https endpoint and automatically refreshes SSL/TLS certificates with
Let's Encrypt.

MyPaas is no more than a tool that helps you setup Traefik, and deploy
Docker containers that have the right labels so that Traefik handles
them in the right way.


## How it works

MyPaas is a command line utility that you use both on your server (the PAAS),
as well as on other machines to push deploys to your server. There is no
web UI. You configure your service by adding special comments to the Dockerfile.


## Getting started

First, you'll need to install some dependencies. We'll be assuming a
fresh Ubuntu VM - you may need to adjust the commands if you are using
another operating system. You may also need to add `sudo` in front of
the commands.

First, let's make sure the package manager is up to date:
```sh
$ apt update
```

Next, install Docker, start the service, and make sure it starts automatically after a reboot:
```sh
$ apt install docker.io
$ systemctl start docker
$ systemctl enable docker
```

Now install MyPaas. It is written in Python, so we can use pip to install it (you'll need Python 3.6 or higher).
```sh
$ apt install python3-pip
$ pip3 install mypaas
```

That's it, you can now initialize your server:
```sh
$ mypaas init
```

The `init` command will:
* Start Traefik in a Docker container and make sure it is configured correctly
* Start a server (in a Docker container) that can accept deployments from the outside.
* Start a service (via systemctl) that will perform the deployments that the server prepares.

Your server is now a PAAS, ready to run apps and services!


## Setting up credentials

TODO


## Deploying a service

In MyPaas, the unit of deployment is called a "service". These are
sometimes called "apps". Each service is defined using one Dockerfile,
resulting in one Docker image, and will be deployed as one or more
containers (more than one when scaling).

The service can be configured by adding special comments in the Dockerfile. For example:
```Dockerfile
# mypaas.servicename = example-service
# mypaas.domain = www.mydomain.com
# mypaas.domain = mydomain.com

FROM python:3.7-alpine

RUN apk update
RUN pip --no-cache-dir install click h11 \
    && pip --no-cache-dir install uvicorn==0.6.1 --no-deps \
    && pip --no-cache-dir install asgineer==0.7.1

COPY . .
CMD python server.py
```

You can deploy services when logged into the server using:
```sh
$ mypaas deploy Dockerfile
```

But in most cases, you'll be deploying from another machine (e.g. your
laptop or CI/CD) by pushing the Dockerfile (and all other files in the
current directory) to the server:
```sh
$ mypaas push myservername Dockerfile
```

The server will accept the files and then do a `mypaas deploy`. For the above example,
your service will now be available via http://www.mydomain.com and http://mydomain.com.
Note though, that you need to point the domains' DNS records to the IP address of the server.


## CLI commands

```sh
$ mypaas init    # Initializes a server to use MyPaas deployment using Traefik and Docker.
                 # You'll typically only use this only once per server.
$ mypaas deploy  # Run on the server to deploy a service from a Dockerfile.
                 # Mosy users will probably use push instead.
$ mypaas push    # Do a deploy from another computer.
```

(there will probably be a few more commands)


## Configuration options

### mypaas.servicename

The name of the service. On each deploy, any service with the same name
will be replaced by the new deployment. It will also be the name of the
Docker image, and part of the name of the docker container. Therefore you can
eaily find it back using common Docker tools.

### mypaas.domain

Requests for this domain must be routed to this service, e.g.
`mydomain.com`, `foo.myname.org`, etc. You can use this parameter
multiple times to specify multiple domains.

If no domains are specified, the service is not accessible from the outside, but
can still be used by other services (e.g. a database).

### mypaas.https

A boolean ("true" or "false") indicating whether to enable `https`. Default `false`.
When `true`, Traefik will generate certificates and force all requests to be encrypted.
Traefik will also automatically renew the certificates before they
expire.

Before enabling this, make sure that all domains actually resolve to
the server. Otherwise Traefik will try to get a certificate and fail,
and doing this often is problematic, because Let's Encrypt limits the
number of requests (that Traefik can make) for a certificate.

### mypaas.volume

Equivalent to Docker's `--volume` option. Enables mounting a specific
directory of the server in the Docker container, to store data that is
retained between reboots. E.g. `~/dir_or_root:/dir_on_container`.
Can be used multiple times to specify multiple mounted directories.

Note that any data stored inside a container that is not in a mounted
directory will be lost after a re-deploy or reboot.

### mypaas.port

The port that the process inside the container is listening on. Default 80.

### mypaas.scale

An integer specifying how many containers should be running for this service.
Can be set to 0 to indicate "non-scaling", which is the default.

When deploying a non-scaling service, the old container is stopped
before starting the new one, resulting in a downtime of around 5
seconds. This way, there is no risk of multiple containers writing to
the same data at the same time.

If `scaling` is given and larger than zero (so also when scaling is set to 1),
a deployment will have no downtime, because the new containers will be
started and given time to start up before the old containers are stopped.