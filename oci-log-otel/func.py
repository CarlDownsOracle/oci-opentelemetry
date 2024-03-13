#
# oci-opentelemetry-logs version 1.0.
#
# Copyright (c) 2022, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

import io
import json
import logging
import os
import requests
from fdk import response

from google.protobuf.internal.well_known_types import Timestamp
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.common.v1.common_pb2 import InstrumentationScope, KeyValueList, KeyValue, AnyValue, ArrayValue
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, LogsData, ResourceLogs, ScopeLogs
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

API_ENDPOINT = os.getenv('OTEL_COLLECTOR_LOGS_API_ENDPOINT', 'not-configured')

"""
These settings generate a reasonable mapping:

    LOG_RESOURCE_ATTRIBUTES = 'source time oracle'
    LOG_SCOPE_ATTRIBUTES = 'type'
    LOG_RECORD_ATTRIBUTES = 'data id datetime'
"""

LOG_RESOURCE_ATTRIBUTES = os.getenv('LOG_RESOURCE_ATTRIBUTES', 'source time oracle').split(" ")
LOG_SCOPE_ATTRIBUTES = os.getenv('LOG_SCOPE_ATTRIBUTES', 'type').split(" ")
LOG_RECORD_ATTRIBUTES = os.getenv('LOG_RECORD_ATTRIBUTES', 'id data datetime').split(" ")

# Set all registered loggers to the configured log_level

logging_level = os.getenv('LOGGING_LEVEL', 'INFO')
loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
[logger.setLevel(logging.getLevelName(logging_level)) for logger in loggers]


def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function Entry Point
    :param ctx: InvokeContext
    :param data: data payload
    :return: plain text response indicating success or error
    """

    preamble = "fn {} / events {} / logging level {}"

    try:
        event_list = json.loads(data.getvalue())
        logging.info(preamble.format(ctx.FnName(), len(event_list), logging_level))
        logs_data = assemble_otel_logs_data(event_list=event_list)
        logs_data_json = serialize_otel_message_to_json(logs_data)
        send_to_otel_collector(logs_data_json=logs_data_json)

    except (Exception, ValueError) as ex:
        logging.error('error handling logging payload: {}'.format(str(ex)))


def assemble_otel_logs_data(event_list: dict):

    resource_logs = assemble_otel_resource_logs_list(event_list)
    logs_data = LogsData(resource_logs=resource_logs)
    return logs_data


def assemble_otel_resource_logs_list(event_list: dict):

    resource_logs_list = []
    for event in event_list:
        resource_logs = assemble_otel_resource_logs(log_record=event)
        resource_logs_list.append(resource_logs)
        # logging.debug(resource_log)

    return resource_logs_list


def assemble_otel_resource_logs(log_record: dict):

    resource = assemble_otel_resource(log_record)
    scope_logs = assemble_otel_scope_logs(log_record)
    resource_logs = ResourceLogs(resource=resource, scope_logs=scope_logs)
    return resource_logs


def assemble_otel_resource(log_record: dict):
    
    attributes = assemble_otel_attributes(log_record, LOG_RESOURCE_ATTRIBUTES)
    resource = Resource(attributes=attributes)
    return resource


def assemble_otel_attributes(log_record: dict, target_keys: list):

    combined_list = []

    for target_key in target_keys:
        value = get_dictionary_value(log_record, target_key)

        if isinstance(value, dict):
            for k, v in value.items():
                combined_list.append(assemble_otel_attribute(k, v))
        else:
            combined_list.append(assemble_otel_attribute(target_key, value))

    return combined_list


def assemble_otel_attribute(k, v):

    if v is None:
        logging.debug(f'dictionary key {k} / value is is None ... ignoring because PROTOBUF does not support null')
        return KeyValue(key=k, value=None)

    if isinstance(v, bool):
        return KeyValue(key=k, value=AnyValue(bool_value=v))

    elif isinstance(v, int):
        return KeyValue(key=k, value=AnyValue(int_value=v))

    elif isinstance(v, str):
        return KeyValue(key=k, value=AnyValue(string_value=v))

    elif isinstance(v, float):
        return KeyValue(key=k, value=AnyValue(double_value=v))

    elif isinstance(v, list):
        return assemble_otel_attribute_list_value(k, v)

    elif isinstance(v, dict):
        return assemble_otel_attribute_dictionary_value(k, v)

    else:
        raise ValueError(f'dictionary key {k} / value is not supported yet / {v}')


def assemble_otel_attribute_dictionary_value(k, v):

    kvlist = []

    for k2, v2 in v.items():
        kvlist.append(assemble_otel_attribute(k2, v2))

    key_value = KeyValue(key=k, value=AnyValue(kvlist_value=KeyValueList(values=kvlist)))
    return key_value


def assemble_otel_attribute_list_value(k, v):

    values_list = []
    for list_value in v:
        if isinstance(list_value, int):
            values_list.append(AnyValue(int_value=list_value))

        elif isinstance(list_value, str):
            values_list.append(AnyValue(string_value=list_value))

        elif isinstance(list_value, bool):
            values_list.append(AnyValue(bool_value=list_value))

        elif isinstance(list_value, float):
            values_list.append(AnyValue(double_value=list_value))

        else:
            raise ValueError(f'attribute_list assigned to key {k} / value is not supported yet / {v}')

    array_value = KeyValue(key=k, value=AnyValue(array_value=ArrayValue(values=values_list)))
    return array_value


def assemble_otel_scope_logs(log_record: dict):

    inst_scope = assemble_otel_scope(log_record)
    log_records = assemble_otel_log_records(log_record)
    scope_logs = ScopeLogs(scope=inst_scope, log_records=log_records)
    return [scope_logs]


def assemble_otel_log_records(log_record: dict):

    datetime = log_record.get('datetime')
    attributes = assemble_otel_attributes(log_record, LOG_RECORD_ATTRIBUTES)
    log_record = LogRecord(time_unix_nano=datetime, observed_time_unix_nano=0, attributes=attributes)
    return [log_record]


def assemble_otel_scope(log_record: dict):

    attributes = assemble_otel_attributes(log_record, LOG_SCOPE_ATTRIBUTES)
    inst_scope = InstrumentationScope(attributes=attributes)
    return inst_scope


def get_dictionary_value(dictionary: dict, target_key: str):
    """
    Recursive method to find value within a dictionary which may also have nested lists / dictionaries.
    :param dictionary: the dictionary to scan
    :param target_key: the key we are looking for
    :return: If a target_key exists multiple times in the dictionary, the first one found will be returned.
    """

    target_value = dictionary.get(target_key)
    if target_value:
        return target_value

    for key, value in dictionary.items():
        if isinstance(value, dict):
            target_value = get_dictionary_value(dictionary=value, target_key=target_key)
            if target_value:
                return target_value

        elif isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict):
                    target_value = get_dictionary_value(dictionary=entry, target_key=target_key)
                    if target_value:
                        return target_value


def send_to_otel_collector(logs_data_json):
    """
    """

    # creating a session and adapter to avoid recreating
    # a new connection pool between each POST call

    session = None
    
    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
        session.mount('https://', adapter)

        http_headers = {'Content-type': 'application/json'}
        post_response = session.post(API_ENDPOINT, data=json.dumps(logs_data_json), headers=http_headers)
        if post_response.status_code != 200:
            raise Exception(f'error sending to OpenTelemetry Collector / {post_response.text}')

    finally:
        session.close()


def serialize_otel_message_to_json(logs_data: LogsData):
    logs_data_dict_obj = MessageToDict(logs_data)
    logs_data_json = json.dumps(logs_data_dict_obj, indent=2)
    return logs_data_json


def local_test_mode(filename):
    """
    """

    logging.info("local testing started")

    with open(filename, 'r') as f:
        contents = json.load(f)
        if isinstance(contents, dict):
            contents = [contents]

        logs_data = assemble_otel_logs_data(event_list=contents)
        logs_data_json = serialize_otel_message_to_json(logs_data)
        logging.info(logs_data_json)

    logging.info("local testing completed")


"""
Local Debugging 
"""

if __name__ == "__main__":
    local_test_mode('../data/oci_log.json')
    # local_test_mode('../data/oci_log.2.json')
    # local_test_mode('../data/audit.1.json')
    # local_test_mode('../data/oci_logs.json')

