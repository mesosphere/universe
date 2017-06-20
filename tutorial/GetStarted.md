# Getting Started

This document is intended as a "getting started" guide. The audience are developers looking to modify or *publish* the packages to the universe. This document is written in tutorial and walk-through format. The goal is to help you "get started". It does not go into great depth on some of the conceptual or inner details. This guide aims at making a user familiar with the concepts of what a Package is and what are the roles of marathon and universe in the package life cycle.

Before the launch, make sure you have:
* Access to a running [DC/OS](https://dcos.io/docs/latest/overview/what-is-dcos/).
* python3 is installed in your environment.
* [DC/OS CLI](https://dcos.io/docs/latest/cli/install/) installed and configured.
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.


### What is universe
The Universe is a DC/OS package repository that contains services like Spark, Cassandra, Jenkins, and many others. It allows users to install these services with a single click from the DC/OS UI or by a simple `dcos package install package_name` command from the DC/OS CLI. Many community members have already submitted their own packages to the Universe, and we encourage anyone interested to get involved with package development! It is a great way of contributing to the DC/OS ecosystem and allows users to easily get started with your favorite package.

### What is marathon
[Marathon](https://mesosphere.github.io/marathon/) is a production-grade container orchestration platform for Mesosphere’s Datacenter Operating System (DC/OS) and [Apache Mesos](https://mesos.apache.org/). In order to deploy applications on top of Mesos, one can use Marathon for Mesos. Marathon is a cluster-wide init and control system for running Linux services in cgroups and Docker containers. Marathon has a number of different deploy [features](https://mesosphere.github.io/marathon/#features) and is a very mature project. Marathon runs on top of Mesos, which is a highly scalable, battle tested and flexible resource manager. Marathon is proven to scale and runs in many production environments.

### What is package
