import io
import json
import logging
import os
import requests
from fdk import response

"""
This sample OCI Function implementation maps OCI Logging CloudEvents format to DataDog REST API 'send-logs' contract.  
It is designed to be compatible with OCI Service, Audit and Custom Logs and supports DataDog 'ddtag' field conventions.

Please see these resources for more details:

https://docs.datadoghq.com/api/latest/logs/#send-logs
https://docs.datadoghq.com/getting_started/tagging/
https://github.com/cloudevents/spec/blob/v1.0/json-format.md
https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionspassingconfigparams.htm
"""

# Use OCI Application or Function configurations to override these environment variable defaults.

api_endpoint = os.getenv('DATADOG_LOGGING_API_ENDPOINT', 'not-configured')
api_token = os.getenv('DATADOG_API_KEY', 'not-configured')
is_forwarding = eval(os.getenv('FORWARD_TO_DATADOG', "False"))

ddsource = os.getenv('DDSOURCE', 'type')
ddservice = os.getenv('DDSERVICE', 'source')
ddhostname = os.getenv('DDHOSTNAME', 'hostname')
ddmessage = os.getenv('DDMESSAGE', 'message')
ddlog = os.getenv('DDLOG', 'oci')
ddtag_keys = os.getenv('DDTAG_KEYS', None)
ddtag_set = set()

# Set all registered loggers to the configured log_level

logging_level = os.getenv('LOGGING_LEVEL', 'INFO')
loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
[logger.setLevel(logging.getLevelName(logging_level)) for logger in loggers]

# Exception stack trace logging

is_tracing = eval(os.getenv('ENABLE_TRACING', "False"))


def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function Entry Point
    :param ctx: InvokeContext
    :param data: data payload
    :return: plain text response indicating success or error
    """

    preamble = "fn {} / events {} / logging level {} / forwarding {}"

    try:
        event_list = json.loads(data.getvalue())
        logging.getLogger().info(preamble.format(ctx.FnName(), len(event_list), logging_level, is_forwarding))
        converted_event_list = handle_log_events(event_list=event_list)
        send_to_datadog(event_list=converted_event_list)

    except (Exception, ValueError) as ex:
        logging.getLogger().error('error handling logging payload: {}'.format(str(ex)))
        if is_tracing:
            logging.getLogger().error(ex)


def handle_log_events(event_list):
    """
    :param event_list: the list of CloudEvent formatted log records.
    :return: the list of DataDog formatted log records
    """

    result_list = []
    for event in event_list:
        single_result = transform_cloud_event_to_datadog_format(log_record=event)
        result_list.append(single_result)
        logging.getLogger().debug(single_result)

    return result_list


def transform_cloud_event_to_datadog_format(log_record: dict):
    """
    Transform CloudEvents to DataDog format.
    See: https://docs.datadoghq.com/api/latest/logs/#send-logs
    See: https://github.com/cloudevents/spec/blob/v1.0/json-format.md
    :param log_record: CloudEvent log record
    :return: DataDog formatted log record
    """

    result = {
        'ddsource': get_dictionary_value(log_record, ddsource),
        'service' : get_dictionary_value(log_record, ddservice),
        'hostname': get_dictionary_value(log_record, ddhostname),
        'message' : get_dictionary_value(log_record, ddmessage),
        'ddtags' :  get_ddtags(log_record),
        ddlog : log_record,
    }
    return result


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


def get_ddtags(log_record: dict):
    """
    Assembles ddtags from selected CloudEvent attributes.
    See https://docs.datadoghq.com/getting_started/tagging/
    :param log_record: the log record to scan
    :return: string of comma-separated, key:value pairs matching DataDog ddtag format
    """

    result = []

    for tag in get_ddtag_set():
        value = get_dictionary_value(dictionary=log_record, target_key=tag)
        if value is None:
            continue

        if isinstance(value, str) and ':' in value:
            logging.getLogger().warning('ddtag contains a \':\' / ignoring {} ({})'.format(key, value))
            continue

        ddtag = '{}:{}'.format(tag, value)
        result.append(ddtag)

    ddtags = ",".join(result)
    return ddtags


def get_ddtag_set():
    """
    :return: the set CloudEvent payload keys that we would like to have converted to ddtags.
    """

    global ddtag_set

    if len(ddtag_set) == 0 and ddtag_keys:
        split_and_stripped_tags = [x.strip() for x in ddtag_keys.split(',')]
        tag_set.update(split_and_stripped_tags)
        logging.getLogger().debug("ddtag key set / {} ".format (ddtag_set))

    return ddtag_set


def send_to_datadog (event_list):
    """
    Sends each transformed event to DataDog Endpoint.
    :param event_list: list of events in DataDog format
    :return: None
    """

    if is_forwarding is False:
        logging.getLogger().debug("DataDog forwarding is disabled - nothing sent")
        return

    # creating a session and adapter to avoid recreating
    # a new connection pool between each POST call

    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
        session.mount('https://', adapter)

        for event in event_list:
            dd_headers = {'Content-type': 'application/json', 'DD-API-KEY': api_token}
            response = session.post(api_endpoint, data=json.dumps(event), headers=dd_headers)
            if response.status_code != 202:
                raise Exception ('error sending to DataDog', response.text)

    finally:
        session.close()


def local_test_mode(filename):
    """
    This routine reads a local json CloudEvents file, converting the contents to DataDog format.
    :param filename: cloud events json file exported from OCI Logging UI or CLI.
    :return: None
    """

    logging.getLogger().info("local testing started")

    with open(filename, 'r') as f:
        data = json.load(f)
        log_results = get_dictionary_value(data, 'results')
        transformed_results = list()

        # find the 'logContent' sub-dictionary starting point to match
        # what the Function will receive per event

        for event in log_results:
            log_record = get_dictionary_value(data, 'logContent')
            transformed_result = transform_cloud_event_to_datadog_format(log_record)
            transformed_results.append(transformed_result)

        logging.getLogger().debug(json.dumps(transformed_results, indent=4))
        send_to_datadog(event_list=transformed_results)

    logging.getLogger().info("local testing completed")


"""
Local Debugging 
"""

if __name__ == "__main__":
    local_test_mode('../oci.log.data.2.json')

