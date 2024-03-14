# Oracle Cloud Infrastructure OpenTelemetry Integration

---

## Overview

Let's take a look at bringing Oracle Cloud Infrastructure (OCI)’s rich Logs resources OpenTelemetry-compatible
3rd systems.  This function sample shows how to perform simple JSON-to-JSON transformation of the OCI log and 
metric events to OpenTelemetry's API contract.  Transformed messages are then sent to an `OTEL Collector` using 
the `http` receiver as JSON.

[See Collector QuickStart](https://opentelemetry.io/docs/collector/quick-start/)

![OTEL Collector](images/otel-collector.png)


---
### [Logging Service](oci-log-otel/README.md)
### [Monitoring Service](oci-metrics-otel/README.md)
### [Service Connector / Enrichment Task](oci-tag-enrich/README.md)
