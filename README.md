# Oracle Cloud Infrastructure OpenTelemetry Integration

---

## Overview

Let's take a look at bringing Oracle Cloud Infrastructure (OCI)’s rich observability data to OpenTelemetry-compatible
3rd party systems.  

The function samples contained in this repo show how to perform simple JSON-to-JSON transformation of the OCI log and 
metric events to OpenTelemetry's API contract.  Transformed messages are then sent to an `OTEL Collector`. 

Here are the sample functions for sending logs and metrics ... and a sample function showing
how to include OCI tags with your payloads.

* [Exporting OCI Logs to OTEL Collectors](oci-log-otel/README.md)
* [Exporting OCI Metrics to OTEL Collectors](oci-metrics-otel/README.md)
* [Enriching Logs and Metrics with OCI Tags](oci-tag-enrich/README.md)

Here are some useful OpenTelemetry resources:

* [OTEL Collector Documentation](https://opentelemetry.io/docs/collector/)
* [OTEL Collector QuickStart](https://opentelemetry.io/docs/collector/quick-start/)

---

![OTEL Collector](images/otel-collector.png)

---

## Setting up OTEL Collector Testbed

#### `WARNING`: These instructions are **NOT suitable for production environments!**

### Provision OCI VCN & Compute Node

You will need a VCN and a Compute node.  Create a new VCN ... or use the VCN your Functions will be using. `NOTE`: Be 
sure to add a VCN security list Ingress Rule to allow traffic to pass from the 
Functions to your Compute node. The remainder of this README assumes you have provisioned an 
Oracle 8 Linux Compute node with an ssh public key.

### Install Docker (Compose) on Oracle 8

I recommend following [Kyle Schwartz](https://dev.to/kylejschwartz)'s excellent article 
to [Install Docker (Compose) on Oracle Linux 8](https://dev.to/kylejschwartz/install-docker-compose-on-oracle-linux-8-1kb0) 
on your Compute node.

### Configure, start and test the Collector

Copy the `docker-compose.yaml` file found in the [Install the Collector](https://opentelemetry.io/docs/collector/installation/) docs
to your Compute node.  Copy [otel-collector-config.yaml](./otel-collector-config.yaml) to your node.  This configuration enables 
HTTP protocol ... **a must have** ... otherwise the Functions will NOT work.


### Start the Collector

    sudo docker-compose up -d
    sudo docker-compose logs

### Test the Collector's HTTP Protocol Locally

To test locally (where the OTEL Collector is running), you can copy this 
example [metrics.json](https://github.com/open-telemetry/opentelemetry-proto/blob/main/examples/metrics.json) file to 
that node and then perform an HTTP post using curl:
 
    curl -X POST -H "Content-Type: application/json" -d @metrics.json -i localhost:4318/v1/metrics
 
Logging can be tested as well with [logs.json](https://github.com/open-telemetry/opentelemetry-proto/blob/main/examples/logs.json):
 
    curl -X POST -H "Content-Type: application/json" -d @logs.json -i localhost:4318/v1/logs

View docker-compose logs:

    sudo docker-compose logs

If the logs and metrics are shown, your Testbed OTEL Collector is ready to receive HTTP POST's from OCI Functions.

