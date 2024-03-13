import json

from google.protobuf.internal.well_known_types import Timestamp
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.common.v1.common_pb2 import InstrumentationScope, KeyValueList, KeyValue, AnyValue
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, LogsData, ResourceLogs, ScopeLogs

# see https://github.com/open-telemetry/oteps/blob/main/text/logs/0097-log-data-model.md#example-log-records
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

# see https://github.com/open-telemetry/opentelemetry-proto/blob/main/examples/logs.json


example1 = {
    "Timestamp": 1586960586000,

    "Attributes": {
        "http.status_code": 500,
        "http.url": "https://example.com",
        "my.custom.application.tag": "hello",
    },
    "Resource": {
        "service.name": "donut_shop",
        "service.version": "semver:2.0.0",
        "k8s.pod.uid": "1138528c-c36e-11e9-a1a7-42010a800198",
    },
    "TraceId": "f4dbb3edd765f620",
    "SpanId": "43222c2d51a7abe3",
    "SeverityText": "INFO",
    "SeverityNumber": 9,
    "Body": "20200415T072306-0700 INFO I like donuts"
}

example2 = {
    "Timestamp": 1586960586000,
    "Body": {
        "i": "am",
        "an": "event",
        "of": {
            "some": "complexity"
        }
    }
}

example3 = {
    "Timestamp": 1586960586000,
    "Attributes": {
        "http.scheme": "https",
        "http.host": "donut.mycie.com",
        "http.target": "/order",
        "http.method": "post",
        "http.status_code": 500,
        "http.flavor": "1.1",
        "http.user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko)",
    }
}

timestamp = 1586960586000
attributes = {
    "http.scheme": "https",
    "http.host": "donut.google.com",
    "http.target": "/order",
    "http.method": "post",
    "http.status_code": 500,
    "http.flavor": "1.1",
    "http.user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko)",
}

body = {
    "i": "am",
    "an": "event",
    "of": {
        "some": "complexity"
    }
}

# resource = {
#         "service.name": "donut_shop",
#         "service.version": "semver:2.0.0",
#         "k8s.pod.uid": "1138528c-c36e-11e9-a1a7-42010a800198",
#     }

# //////////////////////////////////////////////

# TODO if you are going to code to the generated classes, use this:
#   See https://protobuf.dev/reference/python/python-generated/#map-fields

ts = Timestamp()

kv_list = KeyValueList()
k1 = KeyValue()
k1.key = "this"
k2 = KeyValue()
k2.key = "totally.get.it.now"

list_of_keys = [k1, k2]

resource1 = Resource(attributes=list_of_keys)

k3 = KeyValue(key='counter', value=AnyValue(int_value=700008))
k4 = KeyValue(key='tenancy_is_active', value=AnyValue(bool_value=True))
k5 = KeyValue(key='vcn', value=AnyValue(string_value='this is a vcn'))

kvlist = [k3, k4]
k6 = KeyValue(key='dictionary', value=AnyValue(kvlist_value=KeyValueList(values=kvlist)))

resource2 = Resource(attributes=[k3, k4, k5, k6])

resource_logs = [ResourceLogs(resource=resource1), ResourceLogs(resource=resource2)]

inst_scope = InstrumentationScope()
log_records = [LogRecord(time_unix_nano=0, observed_time_unix_nano=0)]
scope_logs = ScopeLogs(scope=inst_scope, log_records=log_records)
logs_data = LogsData(resource_logs=resource_logs)

print('--------------------')
print(f'log_records == {log_records}')

print('--------------------')
print(f'logs_data == {logs_data}')

print('--------------------')
print(f'scope_logs == {scope_logs}')

print('--------------------')
print(f'resource_logs == {resource_logs}')

print('--------------------')
print(f'resource1 == {resource1}')

print('--------------------')
logs_data_dict_obj = MessageToDict(logs_data)
print(f'logs_data_dict_obj == {logs_data_dict_obj}')

print('--------------------')
logs_data_json = json.dumps(logs_data_dict_obj, indent=4)
print(f'logs_data_json == {logs_data_json}')

print('--------------------')
s = logs_data.SerializeToString()
print(f'logs_data.SerializeToString == {s}')
