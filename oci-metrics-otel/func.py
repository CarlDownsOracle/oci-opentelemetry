#
# oci-opentelemetry-metrics version 1.0.
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
from opentelemetry.proto.metrics.v1.metrics_pb2 import MetricsData, ScopeMetrics, ResourceMetrics, Metric, Sum, Gauge, \
    Histogram, Summary, HistogramDataPoint, NumberDataPoint
from opentelemetry.proto.resource.v1.resource_pb2 import Resource

# Set these environment variables via Function configuration

API_ENDPOINT = os.getenv('OTEL_COLLECTOR_METRICS_API_ENDPOINT', 'not-configured')
OTEL_METRIC_RESOURCE_ATTR_MAP = os.getenv('OTEL_METRIC_RESOURCE_ATTR_MAP', 'dimensions compartmentId').split(" ")
OTEL_METRIC_SCOPE_ATTR_MAP = os.getenv('OTEL_METRIC_SCOPE_ATTR_MAP', 'namespace').split(" ")
OTEL_DATAPOINT_ATTR_MAP = os.getenv('OTEL_DATAPOINT_ATTR_MAP', 'count').split(" ")

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

    preamble = "fn {} / metric events {} / logging level {}"

    logging.debug(f'LOGGING_LEVEL / {LOGGING_LEVEL}')
    logging.debug(f'RAISE_MISSING_MAP_KEY / {RAISE_MISSING_MAP_KEY}')
    logging.debug(f'LOG_MISSING_MAP_KEY / {LOG_MISSING_MAP_KEY}')
    logging.debug(f'LOG_RECORD_CONTENT / {LOG_RECORD_CONTENT}')
    logging.debug(f'OTEL_METRIC_RESOURCE_ATTR_MAP / {OTEL_METRIC_RESOURCE_ATTR_MAP}')
    logging.debug(f'OTEL_METRIC_SCOPE_ATTR_MAP / {OTEL_METRIC_SCOPE_ATTR_MAP}')
    logging.debug(f'OTEL_DATAPOINT_ATTR_MAP / {OTEL_DATAPOINT_ATTR_MAP}')

    try:
        event_list = json.loads(data.getvalue())
        logging.info(f'fn {ctx.FnName()} / metric event count {len(event_list)}')

        logs_data = assemble_otel_metrics_data(event_list=event_list)
        logs_data_json = serialize_otel_message_to_json(logs_data)
        send_to_otel_collector(logs_data_json=logs_data_json)

    except (Exception, ValueError) as ex:
        logging.error('error handling logging payload: {}'.format(str(ex)))


def assemble_otel_metrics_data(event_list: dict):

    resource_metrics = assemble_otel_resource_metrics_list(event_list)
    metrics_data = MetricsData(resource_metrics=resource_metrics)
    return metrics_data


def assemble_otel_resource_metrics_list(event_list: dict):

    resource_metrics_list = []
    for event in event_list:
        resource_metrics = assemble_otel_resource_metrics(log_record=event)
        resource_metrics_list.append(resource_metrics)

    return resource_metrics_list


def assemble_otel_resource_metrics(log_record: dict):

    if LOG_RECORD_CONTENT is True:
        logging.info(f'OCI metric / {json.dumps(log_record)}')

    resource = assemble_otel_resource(log_record)
    scope_metrics = assemble_otel_scope_metrics(log_record)
    resource_metrics = ResourceMetrics(resource=resource, scope_metrics=scope_metrics)

    if LOG_RECORD_CONTENT is True:
        logging.info(f'OTEL metric / {serialize_otel_message_to_json(resource_metrics)}')

    return resource_metrics


def assemble_otel_scope_metrics(log_record: dict):

    scope = assemble_otel_scope(log_record)
    metrics = assemble_otel_metrics(log_record)
    scope_metrics = ScopeMetrics(scope=scope, metrics=metrics)
    return [scope_metrics]


def assemble_otel_metrics(log_record: dict):

    name = get_dictionary_value(log_record, 'name')
    display_name = get_dictionary_value(log_record, 'displayName')
    unit = get_dictionary_value(log_record, 'unit')

    # generate an OTEL metric entry for each OCI data point

    metrics = []
    oci_datapoints = get_dictionary_value(log_record, 'datapoints')
    for oci_datapoint in oci_datapoints:
        timestamp = adjust_unix_time_to_nano(oci_datapoint.get('timestamp'))
        attributes = assemble_otel_attributes(oci_datapoint, OTEL_DATAPOINT_ATTR_MAP)
        data_point = NumberDataPoint(attributes=attributes)
        data_point.time_unix_nano = timestamp
        data_point.as_double = float(oci_datapoint.get('value'))
        unit = unit
        gauge = Gauge(data_points=[data_point])
        metric = Metric(name=name, description=display_name, unit=unit, gauge=gauge)
        metrics.append(metric)

    return metrics


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
    attributes = assemble_otel_attributes(log_record, OTEL_METRIC_SCOPE_ATTR_MAP)
    inst_scope = InstrumentationScope(attributes=attributes)
    return inst_scope


def assemble_otel_resource(log_record: dict):

    attributes = assemble_otel_attributes(log_record, OTEL_METRIC_RESOURCE_ATTR_MAP)
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

        logs_data = assemble_otel_metrics_data(event_list=contents)
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
    logging.info(f'OTEL_METRIC_RESOURCE_ATTR_MAP / {OTEL_METRIC_RESOURCE_ATTR_MAP}')
    logging.info(f'OTEL_METRIC_SCOPE_ATTR_MAP / {OTEL_METRIC_SCOPE_ATTR_MAP}')
    logging.info(f'OTEL_DATAPOINT_ATTR_MAP / {OTEL_DATAPOINT_ATTR_MAP}')
    
    local_test_mode('../data/oci.metrics.json')

