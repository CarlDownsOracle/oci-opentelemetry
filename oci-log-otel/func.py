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
from dateutil import parser

from google.protobuf.internal.well_known_types import Timestamp
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.common.v1.common_pb2 import InstrumentationScope, KeyValueList, KeyValue, AnyValue, ArrayValue
from opentelemetry.proto.logs.v1.logs_pb2 import LogRecord, LogsData, ResourceLogs, ScopeLogs
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

API_ENDPOINT = os.getenv('OTEL_COLLECTOR_LOGS_API_ENDPOINT', 'not-configured')

# Mapping behavior

OTEL_RESOURCE_ATTR_MAP = os.getenv('OTEL_RESOURCE_ATTR_MAP', 'oracle').split(" ")
OTEL_SCOPE_ATTR_MAP = os.getenv('OTEL_SCOPE_ATTR_MAP', '').split(" ")
OTEL_LOG_RECORD_ATTR_MAP = os.getenv('OTEL_LOG_RECORD_ATTR_MAP', 'id source time type data').split(" ")

# What happens if a mapped key is not found in the OCI payload?

RAISE_MISSING_MAP_KEY = eval(os.getenv('RAISE_MISSING_MAP_KEY', "True"))
LOG_MISSING_MAP_KEY = eval(os.getenv('LOG_MISSING_MAP_KEY', "True"))

# Log the OCI and OTEL full record contents to OCI logging (not recommended in production!!)

LOG_RECORD_CONTENT = eval(os.getenv('LOG_RECORD_CONTENT', "False"))

# Set all registered loggers to the configured log_level

LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
[logger.setLevel(logging.getLevelName(LOGGING_LEVEL)) for logger in loggers]


def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function Entry Point
    :param ctx: InvokeContext
    :param data: data payload
    :return: plain text response indicating success or error
    """

    logging.debug(f'LOGGING_LEVEL / {LOGGING_LEVEL}')
    logging.debug(f'RAISE_MISSING_MAP_KEY / {RAISE_MISSING_MAP_KEY}')
    logging.debug(f'LOG_MISSING_MAP_KEY / {LOG_MISSING_MAP_KEY}')
    logging.debug(f'LOG_RECORD_CONTENT / {LOG_RECORD_CONTENT}')
    logging.debug(f'OTEL_RESOURCE_ATTR_MAP / {OTEL_RESOURCE_ATTR_MAP}')
    logging.debug(f'OTEL_SCOPE_ATTR_MAP / {OTEL_SCOPE_ATTR_MAP}')
    logging.debug(f'OTEL_LOG_RECORD_ATTR_MAP / {OTEL_LOG_RECORD_ATTR_MAP}')

    try:
        event_list = json.loads(data.getvalue())
        logging.info(f'fn {ctx.FnName()} / log event count {len(event_list)}')

        logs_data = assemble_otel_logs_data(event_list=event_list)
        logs_data_json = serialize_otel_message_to_json(logs_data)
        send_to_otel_collector(logs_data_json=logs_data_json)

    except (Exception, ValueError) as ex:
        logging.error('function error / {}'.format(str(ex)))


def assemble_otel_logs_data(event_list: dict):

    resource_logs = assemble_otel_resource_logs_list(event_list)
    logs_data = LogsData(resource_logs=resource_logs)
    return logs_data


def assemble_otel_resource_logs_list(event_list: dict):

    resource_logs_list = []
    for event in event_list:
        resource_logs = assemble_otel_resource_logs(log_record=event)
        resource_logs_list.append(resource_logs)

    return resource_logs_list


def assemble_otel_resource_logs(log_record: dict):

    if LOG_RECORD_CONTENT is True:
        logging.info(f'OCI log / {json.dumps(log_record)}')

    resource = assemble_otel_resource(log_record)
    scope_logs = assemble_otel_scope_logs(log_record)
    resource_logs = ResourceLogs(resource=resource, scope_logs=scope_logs)

    if LOG_RECORD_CONTENT is True:
        logging.info(f'OTEL log / {serialize_otel_message_to_json(resource_logs)}')

    return resource_logs


def assemble_otel_resource(log_record: dict):
    
    attributes = assemble_otel_attributes(log_record, OTEL_RESOURCE_ATTR_MAP)
    resource = Resource(attributes=attributes)
    return resource


def assemble_otel_attributes(log_record: dict, target_keys: list):

    if len(target_keys) == 0:
        return

    combined_list = []

    for target_key in target_keys:
        if not target_key:
            continue

        value = get_dictionary_value(log_record, target_key)

        if isinstance(value, dict):
            for k, v in value.items():
                combined_list.append(assemble_otel_attribute(k, v))
        else:
            combined_list.append(assemble_otel_attribute(target_key, value))

    return combined_list


def assemble_otel_attribute(k, v):

    if v is None:
        message = f'OCI log record key / {k} / has no value'
        if RAISE_MISSING_MAP_KEY:
            raise ValueError(message)

        if LOG_MISSING_MAP_KEY:
            logging.debug(message)

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
    """
    see https://opentelemetry.io/docs/specs/otel/logs/data-model/#field-timestamp
    """

    time_str = get_dictionary_value(log_record, 'time')
    time_unix_nano = get_unix_time_nano(time_str)

    attributes = assemble_otel_attributes(log_record, OTEL_LOG_RECORD_ATTR_MAP)
    log_record = LogRecord(attributes=attributes)
    log_record.time_unix_nano = time_unix_nano

    return [log_record]


def get_unix_time_nano(timestamp_str: str):

    timestamp_dt = parser.parse(timestamp_str)
    timestamp_int = int(round(timestamp_dt.timestamp()))
    return adjust_unix_time_to_nano(timestamp_int)


def adjust_unix_time_to_nano(timestamp_int: int):
    """
    See nano unix date examples
    https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/#examples
    """

    # spec calls for 1*10^18
    while timestamp_int < 1000000000000000000:
        timestamp_int *= 10

    return timestamp_int


def assemble_otel_scope(log_record: dict):

    attributes = assemble_otel_attributes(log_record, OTEL_SCOPE_ATTR_MAP)
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
        post_response = session.post(API_ENDPOINT, data=logs_data_json, headers=http_headers)

        if post_response.status_code not in [200, 202]:
            raise RuntimeError(f'POST Error / {post_response.status_code} / {post_response.text}')
        else:
            logging.info(f'POST Success / {post_response.status_code} / {post_response.text}')

    finally:
        session.close()


def serialize_otel_message_to_json(logs_data: LogsData, use_indention=False):
    logs_data_dict_obj = MessageToDict(logs_data)

    if use_indention is True:
        logs_data_json = json.dumps(logs_data_dict_obj, indent=2)
    else:
        logs_data_json = json.dumps(logs_data_dict_obj)

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
        logs_data_json = serialize_otel_message_to_json(logs_data, use_indention=True)
        logging.info(logs_data_json)

    logging.info("local testing completed")


"""
Local Debugging 
"""

if __name__ == "__main__":
    logging.info(f'LOGGING_LEVEL / {LOGGING_LEVEL}')
    logging.info(f'RAISE_MISSING_MAP_KEY / {RAISE_MISSING_MAP_KEY}')
    logging.info(f'LOG_MISSING_MAP_KEY / {LOG_MISSING_MAP_KEY}')
    logging.info(f'LOG_RECORD_CONTENT / {LOG_RECORD_CONTENT}')
    logging.info(f'OTEL_RESOURCE_ATTR_MAP / {OTEL_RESOURCE_ATTR_MAP}')
    logging.info(f'OTEL_SCOPE_ATTR_MAP / {OTEL_SCOPE_ATTR_MAP}')
    logging.info(f'OTEL_LOG_RECORD_ATTR_MAP / {OTEL_LOG_RECORD_ATTR_MAP}')

    local_test_mode('../data/oci_log.json')
    # local_test_mode('../data/oci_log.2.json')
    # local_test_mode('../data/audit.1.json')
    # local_test_mode('../data/oci_logs.json')

