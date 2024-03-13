# Exporting OCI Logging Service Logs to An OpenTelemetry Collector

---

## OpenTelemetry Logs Specification

* [Logs](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/logs)
* [direct-to-collector](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/logs#direct-to-collector)

## OpenTelemetry Data Model

* [Data Model (logRecords)](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md)
* [log-and-event-record-definition](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md#log-and-event-record-definition)

### Behavior


Example resulting output:

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
            "compartmentid": "ocid1.compartment.oc1..aaaaaaaap3ng5unawee4vgjyynn3l4htp2ejqy3a5rxkra3zfxzwyc6crraa",
            "ingestedtime": "2023-07-11T20:42:24.573Z",
            "loggroupid": "ocid1.loggroup.oc1.phx.amaaaaaaa752xmyaxu5d2snrezxfsrms3g5rnad3d6mu5aj4pum6d3er2ueq",
            "logid": "ocid1.log.oc1.phx.amaaaaaaa752xmyaewrujrk5utqfggr64k6b2m3iedpi2dnvet2lnljtnoqa",
            "tenantid": "ocid1.tenancy.oc1..aaaaaaaaebxriz7y7egelwfkjdbnjdvq6k5vaaxo3o35fvfzf3g7ryvxevka",
            "vniccompartmentocid": "ocid1.compartment.oc1..aaaaaaaap3ng5unawee4vgjyynn3l4htp2ejqy3a5rxkra3zfxzwyc6crraa",
            "vnicocid": "ocid1.vnic.oc1.phx.abyhqljr47ao7pa5gxnwnygbjjxxulmx3hazqupmy5pya2ijmfyqedrxge2a",
            "vnicsubnetocid": "ocid1.subnet.oc1.phx.aaaaaaaac4urlt7pz44x6pgolftcvmpbnmw5ze3tndjemwciar6ox4s6gs7q"
          },
          "source": "-",
          "specversion": "1.0",
          "time": "2023-07-11T20:41:30.000Z",
          "type": "com.oraclecloud.vcn.flowlogs.DataEvent"
        }
      }

Transformed to this OTEL format:

    {
      "resourceLogs": [
        {
          "resource": {
            "attributes": [
              {
                "key": "service.name",
                "value": {
                  "stringValue": "my.service"
                }
              }
            ]
          },
          "scopeLogs": [
            {
              "scope": {
                "name": "my.library",
                "version": "1.0.0",
                "attributes": [
                  {
                    "key": "my.scope.attribute",
                    "value": {
                      "stringValue": "some scope attribute"
                    }
                  }
                ]
              },
              "logRecords": [
                {
                  "timeUnixNano": "1544712660300000000",
                  "observedTimeUnixNano": "1544712660300000000",
                  "severityNumber": 10,
                  "severityText": "Information",
                  "traceId": "5B8EFFF798038103D269B633813FC60C",
                  "spanId": "EEE19B7EC3C1B174",
                  "body": {
                    "stringValue": "Example log record"
                  },
                  "attributes": [
                    {
                      "key": "string.attribute",
                      "value": {
                        "stringValue": "some string"
                      }
                    },
                    {
                      "key": "boolean.attribute",
                      "value": {
                        "boolValue": true
                      }
                    },
                    {
                      "key": "int.attribute",
                      "value": {
                        "intValue": "10"
                      }
                    },
                    {
                      "key": "double.attribute",
                      "value": {
                        "doubleValue": 637.704
                      }
                    },
                    {
                      "key": "array.attribute",
                      "value": {
                        "arrayValue": {
                          "values": [
                            {
                              "stringValue": "many"
                            },
                            {
                              "stringValue": "values"
                            }
                          ]
                        }
                      }
                    },
                    {
                      "key": "map.attribute",
                      "value": {
                        "kvlistValue": {
                          "values": [
                            {
                              "key": "some.map.key",
                              "value": {
                                "stringValue": "some value"
                              }
                            }
                          ]
                        }
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

| Environment Variable        | Default           | Purpose                                                                          |
|-----------------------------|:-------------:|:---------------------------------------------------------------------------------|
| OTEL_COLLECTOR_API_ENDPOINT | not-configured | This is an HTTP protocol address with port, reachable from the Function Service. |
| LOGGING_LEVEL               | INFO     | Controls function logging outputs.  Choices: INFO, WARN, CRITICAL, ERROR, DEBUG  |


Please see these references for more details.

- [OCI Logging Overview](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm)
- [OCI Functions Overview](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
- [CloudEvents Specification](https://github.com/cloudevents/spec/blob/v1.0/json-format.md)


## License
Copyright (c) 2014, 2022 Oracle and/or its affiliates
The Universal Permissive License (UPL), Version 1.0
