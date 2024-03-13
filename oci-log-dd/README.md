# Exporting OCI Logging Service Logs to Datadog

---

## Sample Overview

This sample presents an approach for mapping OCI Logging Service logs to a format
suitable for ingestion by DataDog.  This sample is designed to be compatible with service, audit and custom OCI Logs.
While there is a DataDog client library, this implementation relies on the DataDog REST API.

See the [Monitoring OCI DataDog](https://docs.oracle.com/en/learn/logs_oci_datadog/index.html#introduction) 
documentation to get up and running.

### Environment

Here are the supported variables:

| Environment Variable        | Default           | Purpose  |
| ------------- |:-------------:| :----- |
| DATADOG_LOGGING_API_ENDPOINT      | not-configured | REST API endpoint for reaching DataDog ([see docs](https://docs.datadoghq.com/api/latest/logs/#send-logs))|
| DATADOG_API_KEY      | not-configured      |   API license token obtained from DataDog |
| DDSOURCE | type      |  OCI payload attribute whose value is to be used for ddsource.  Example value: com.oraclecloud.logging.custom.application |
| DDSERVICE | source      |  OCI payload attribute whose value is to be used for service.  Example value: logging-demo-compute |
| DDMESSAGE | message      |  OCI payload attribute whose value is to be used for message.  |
| DDHOSTNAME | hostname      |  OCI payload attribute whose value is to be used for hostname.  Hostname is not a specified cloud events attribute.  Use what is relevant for your situation.  |
| DDTAG_KEYS |       |    Comma-separated list of OCI payload attributes to be characterized as DataDog ddtags ([see docs](https://docs.datadoghq.com/getting_started/tagging/))|
| DDLOG | oci      |    The complete OCI Logging event JSON payload is assigned to this attribute |
| FORWARD_TO_DATADOG | True      |    Determines whether messages are forwarded to DataDog |
| LOGGING_LEVEL | INFO     |    Controls function logging outputs.  Choices: INFO, WARN, CRITICAL, ERROR, DEBUG |
| ENABLE_TRACING | False     |    Enables complete exception stack trace logging |


### Behavior

The Function's environment variables can be overridden to change the mapping.  To override, use OCI 
Application / Function configurations. 

Example DataDog Format:

     {
       "ddsource": "nginx",
       "service": "payment"
       "ddtags": "env:staging,version:5.1",
       "message": "2019-11-19T14:37:58,995 INFO [process.name][20081] Hello World",
       "hostname": "i-012345678",
     }

Default transformation behavior:

     {
       "ddsource": <cloud events 'type' attribute value>,
       "service": <cloud events 'source' attribute value>,
       "ddtags": <selected cloud events attribute/value pairs in ddtag compatible format>,
       "message": <cloud events 'message' attribute value>,       
       "hostname": <cloud events 'hostname' attribute value (if any)>,
       "oci": <complete OCI message in JSON format>,
     }

Example resulting output:

    {
        "ddsource": "com.oraclecloud.logging.custom.application",
        "service": "logging-demo-compute",
        "hostname": null,
        "message": "127.0.0.1 - - [12/Apr/2022 02:42:01] \"GET / HTTP/1.1\" 200 -",
        "ddtags": "id:d3889b50-36e4-4f60-a3ef-c7c1a51920f2,instanceid:ocid1.instance.oc1...",
        "oci": {
            "data": {
                "message": "127.0.0.1 - - [12/Apr/2022 02:42:01] \"GET / HTTP/1.1\" 200 -",
                "tailed_path": "/home/opc/app/http.server.log"
            },
            "id": "d3889b50-36e4-4f60-a3ef-c7c1a51920f2",
            "oracle": {
                "compartmentid": "ocid1.compartment.oc1...",
                "ingestedtime": "2022-04-12T02:44:11.230Z",
                "instanceid": "ocid1.instance.oc1...",
                "loggroupid": "ocid1.loggroup.oc1...",
                "logid": "ocid1.log.oc1...",
                "tenantid": "ocid1.tenancy.oc1..."
            },
            "source": "logging-demo-compute",
            "specversion": "1.0",
            "subject": "/home/opc/app/http.server.log",
            "time": "2022-04-12T02:42:01.259Z",
            "type": "com.oraclecloud.logging.custom.application"
        }
    }

Please see these references for more details.

- [OCI Logging Overview](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm)
- [OCI Functions Overview](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
- [DataDog OCI Integration via Client Library](https://docs.datadoghq.com/integrations/oracle_cloud_infrastructure/?tab=serviceconnectorhub)  
- [DataDog send-logs API](https://docs.datadoghq.com/api/latest/logs/#send-logs)
- [DataDog Tagging Reference](https://docs.datadoghq.com/getting_started/tagging/)
- [CloudEvents Specification](https://github.com/cloudevents/spec/blob/v1.0/json-format.md)


## **OCI** Related Workshops
LiveLabs is the place to explore Oracle's products and services using workshops designed to 
enhance your experience building and deploying applications on the Cloud and On-Premises.
ur library of workshops cover everything from how to provision the world's first autonomous 
database to setting up a webserver on our world class OCI Generation 2 infrastructure, 
machine learning and much more.  Use your existing Oracle Cloud account, 
a [Free Tier](https://www.oracle.com/cloud/free/) account or a LiveLabs Cloud Account to build, test, 
and deploy applications on Oracle's Cloud.

Visit [LiveLabs](http://bit.ly/golivelabs) now to get started.  Workshops are added weekly, please visit frequently for new content.

- [The Essentials of Cloud Observability Workshop](https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/view-workshop?wid=708)

## License
Copyright (c) 2014, 2022 Oracle and/or its affiliates
The Universal Permissive License (UPL), Version 1.0
