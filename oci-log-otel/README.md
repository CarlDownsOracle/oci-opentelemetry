# Exporting OCI Logging Service Logs to An OpenTelemetry Collector

---
## Solution Architecture

Here is the basic architecture and flow of data from beginning to end:

* OCI services emit log data which is managed by the `Logging Service`.
* OCI IAM emits audit log data which is managed by the `Audit Service`.
* The Logging and Audit Services can feed log data events to a `Service Connector`.
* The `Service Connector` invokes a `Function` which transforms the metric data payload to `OpenTelemetry` protobuf messages format and posts the transformed payload to the `OTEL Collector` REST API.
* The `OTEL Collector` ingests the metrics, forwarding them on to downstream `SIEM` / monitoring.

---

![OTEL Collector](../images/architecture.png)


---

## OpenTelemetry Logs Specification

* [Logs](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/logs)
* [direct-to-collector](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/logs#direct-to-collector)

## OpenTelemetry Data Model

* [Data Model (logRecords)](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md)
* [log-and-event-record-definition](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md#log-and-event-record-definition)

### Behavior


Example Log Event:

      {
        "datetime": 1689108090000,
        "logContent": {
          "data": {
            "action": "ACCEPT",
            "bytesOut": 4132,
            "destinationAddress": "147.154.101.151",
            "destinationPort": 443,
            "endTime": 1689108091,
            "flowid": "75d72a74",
            "packets": 9,
            "protocol": 6,
            "protocolName": "TCP",
            "sourceAddress": "10.0.0.219",
            "sourcePort": 60830,
            "startTime": 1689108090,
            "targetSystem": "SPLUNK",
            "status": "OK",
            "version": "2"
          },
          "id": "159f15e5",
          "oracle": {
            "compartmentid": "ocid1.compartment.oc1....",
            "ingestedtime": "2023-07-11T20:42:24.573Z",
            "loggroupid": "ocid1.loggroup.oc1.phx...",
            "logid": "ocid1.log.oc1.phx....",
            "tenantid": "ocid1.tenancy.oc1.....",
            "vniccompartmentocid": "ocid1.compartment.oc1.....",
            "vnicocid": "ocid1.vnic.oc1.phx....",
            "vnicsubnetocid": "ocid1.subnet.oc1.phx.a..."
          },
          "source": "-",
          "specversion": "1.0",
          "time": "2023-07-11T20:41:30.000Z",
          "type": "com.oraclecloud.vcn.flowlogs.DataEvent"
        }
      }


Example OTEL Transformation using these Function Settings

Setting:

    OTEL_RESOURCE_ATTR_MAP = 'source time oracle'
    OTEL_SCOPE_ATTR_MAP = 'type'
    OTEL_LOG_RECORD_ATTR_MAP = 'id data'

Output:

        {
          "resourceLogs": [
            {
              "resource": {
                "attributes": [
                  {
                    "key": "source",
                    "value": {
                      "stringValue": "-"
                    }
                  },
                  {
                    "key": "time",
                    "value": {
                      "stringValue": "2023-07-11T20:41:30.000Z"
                    }
                  },
                  {
                    "key": "compartmentid",
                    "value": {
                      "stringValue": "ocid1.compartment.oc1....."
                    }
                  },
                  {
                    "key": "ingestedtime",
                    "value": {
                      "stringValue": "2023-07-11T20:42:24.573Z"
                    }
                  },
                  {
                    "key": "loggroupid",
                    "value": {
                      "stringValue": "ocid1.loggroup.oc1.phx...."
                    }
                  },
                  {
                    "key": "logid",
                    "value": {
                      "stringValue": "ocid1.log.oc1.phx...."
                    }
                  },
                  {
                    "key": "tenantid",
                    "value": {
                      "stringValue": "ocid1.tenancy.oc1....."
                    }
                  },
                  {
                    "key": "vniccompartmentocid",
                    "value": {
                      "stringValue": "ocid1.compartment.oc1....."
                    }
                  },
                  {
                    "key": "vnicocid",
                    "value": {
                      "stringValue": "ocid1.vnic.oc1.phx...."
                    }
                  },
                  {
                    "key": "vnicsubnetocid",
                    "value": {
                      "stringValue": "ocid1.subnet.oc1.phx...."
                    }
                  }
                ]
              },
              "scopeLogs": [
                {
                  "scope": {
                    "attributes": [
                      {
                        "key": "type",
                        "value": {
                          "stringValue": "com.oraclecloud.vcn.flowlogs.DataEvent"
                        }
                      }
                    ]
                  },
                  "logRecords": [
                    {
                      "attributes": [
                        {
                          "key": "id",
                          "value": {
                            "stringValue": "159f15e5"
                          }
                        },
                        {
                          "key": "action",
                          "value": {
                            "stringValue": "ACCEPT"
                          }
                        },
                        {
                          "key": "bytesOut",
                          "value": {
                            "intValue": "4132"
                          }
                        },
                        {
                          "key": "destinationAddress",
                          "value": {
                            "stringValue": "147.154.101.151"
                          }
                        },
                        {
                          "key": "destinationPort",
                          "value": {
                            "intValue": "443"
                          }
                        },
                        {
                          "key": "endTime",
                          "value": {
                            "intValue": "1689108091"
                          }
                        },
                        {
                          "key": "flowid",
                          "value": {
                            "stringValue": "75d72a74"
                          }
                        },
                        {
                          "key": "packets",
                          "value": {
                            "intValue": "9"
                          }
                        },
                        {
                          "key": "protocol",
                          "value": {
                            "intValue": "6"
                          }
                        },
                        {
                          "key": "protocolName",
                          "value": {
                            "stringValue": "TCP"
                          }
                        },
                        {
                          "key": "sourceAddress",
                          "value": {
                            "stringValue": "10.0.0.219"
                          }
                        },
                        {
                          "key": "sourcePort",
                          "value": {
                            "intValue": "60830"
                          }
                        },
                        {
                          "key": "startTime",
                          "value": {
                            "intValue": "1689108090"
                          }
                        },
                        {
                          "key": "targetSystem",
                          "value": {
                            "stringValue": "SPLUNK"
                          }
                        },
                        {
                          "key": "status",
                          "value": {
                            "stringValue": "OK"
                          }
                        },
                        {
                          "key": "version",
                          "value": {
                            "stringValue": "2"
                          }
                        },
                        {
                          "key": "datetime",
                          "value": {
                            "intValue": "1689108090000"
                          }
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }


### Environment

Here are the supported variables:

| Environment Variable            |        Default         | Purpose                                                                                                                                                                                     |
|---------------------------------|:----------------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| OTEL_COLLECTOR_LOGS_API_ENDPOINT |     not-configured     | This is an HTTP protocol address with port, reachable from the Function Service. Note that the [otel-collector-config.yaml](../otel-collector-config.yaml) must have HTTP protocol enabled. |
| OTEL_RESOURCE_ATTR_MAP          |         oracle         | mapping: transfer oracle (entire object) to resourceLogs attributes.                                                                                                                        |
| OTEL_SCOPE_ATTR_MAP      |                        | mapping: None.                                                                                                                                                                              |
| OTEL_LOG_RECORD_ATTR_MAP        |         id source time type data          | mapping: transfer id, source, time, and type to logRecords.                                                                                                                                 |
| RAISE_MISSING_MAP_KEY           |          True          | What happens if a mapped key is not found in the OCI payload?    Set this true to raise exception then a mapped key is missing.                                                             |
| LOG_MISSING_MAP_KEY             |          True          | What happens if a mapped key is not found in the OCI payload?  Set this true to see what is missing.                                                                                        |
| LOG_RECORD_CONTENT              |         False          | Log the OCI and OTEL full record contents to OCI logging (not recommended in production!!)                                                                                                  |
| LOGGING_LEVEL                   |          INFO          | Controls function logging outputs.  Choices: INFO, WARN, CRITICAL, ERROR, DEBUG                                                                                                             |



Please see these references for more details.

- [OCI Logging Overview](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm)
- [OCI Functions Overview](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
- [CloudEvents Specification](https://github.com/cloudevents/spec/blob/v1.0/json-format.md)


## License
Copyright (c) 2014, 2022 Oracle and/or its affiliates
The Universal Permissive License (UPL), Version 1.0
