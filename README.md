# Oracle Cloud Infrastructure OpenTelemetry Integration

---

## Overview

Let's take a look at bringing Oracle Cloud Infrastructure (OCI)’s rich observability data to OpenTelemetry-compatible
3rd systems.  These function samples show how to perform simple JSON-to-JSON transformation of the OCI log and 
metric events to OpenTelemetry's API contract.  Transformed messages are then sent to an `OTEL Collector`. 

See the [OTEL Collector Documentation](https://opentelemetry.io/docs/collector/)
and [QuickStart](https://opentelemetry.io/docs/collector/quick-start/).

![OTEL Collector](images/otel-collector.png)


---
### [Exporting OCI Logging Service Logs to An OpenTelemetry Collector](oci-log-otel/README.md)
### [Exporting OCI Monitoring Service Metrics to OTEL Collectors](oci-metrics-otel/README.md)
### [Enriching Log and Metric Event Payloads with OCI Tags](oci-tag-enrich/README.md)
