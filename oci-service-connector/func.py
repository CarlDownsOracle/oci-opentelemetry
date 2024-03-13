#
# oci-tag-enrichment-task version 1.0.
#
# Copyright (c) 2023, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

import io
import json
import logging
import os
import oci
from fdk import response

# -------------------------------------------
# Module Variables
# -------------------------------------------

"""
This OCI Function Task is designed to enrich a given event list by retrieving and adding OCI tags associated
with OCIDs present in the event.

Configure TARGET_OCID_KEYS with a comma-separated list of OCID keys (l-values).  The tags for each corresponding OCID,
if present in the payload, will be retrieved and added.  Note that target OCID keys can exist anywhere in the 
event JSON payload, regardless of nested position.  The default value is a sampling of some well-known OCID
keys but is by no means exhaustive.
"""

target_ocid_keys = os.getenv('TARGET_OCID_KEYS', 'compartmentId,vcnId,subnetId,vnicId,vnicsubnetocid').split(',')

"""
The default for TARGET_OCID_KEYS above is a superset of keys that will never all be present in any one
event.  TARGET_OCID_KEYS_WARN_IF_NOT_FOUND defaults to False to suppress log warnings for keys not found in 
the event payload.
"""

target_ocid_keys_warn_if_not_found = eval(os.getenv('TARGET_OCID_KEYS_WARN_IF_NOT_FOUND', "False"))

"""
The TAG_ASSEMBLY_KEY is the l-value under which the tag assembly will be added to the event payload.
"""

tag_assembly_key = os.getenv('TAG_ASSEMBLY_KEY', 'tags')

"""
The TAG_ASSEMBLY_OMIT_EMPTY_RESULTS parameter Determines whether empty objects will be emitted 
for 'freeform', 'defined' or 'system' tag types when there are none found.  Downstream logic may 
require these to be present even if empty.  If that is the case, set TAG_ASSEMBLY_OMIT_EMPTY_RESULTS to False.
"""

tag_assembly_omit_empty_results = eval(os.getenv('TAG_ASSEMBLY_OMIT_EMPTY_RESULTS', "True"))

"""
OCI supports 'freeform', 'defined' and 'system' tag types.  These parameters determine whether the function 
will include a given type.
"""

include_freeform_tags = eval(os.getenv('INCLUDE_FREEFORM_TAGS', "True"))
include_defined_tags = eval(os.getenv('INCLUDE_DEFINED_TAGS', "True"))
include_system_tags = eval(os.getenv('INCLUDE_SYSTEM_TAGS', "True"))

"""
The OCI Search API performs the look-up for us.  Resource principal permissions must be
granted to the task function 'resource' for it to have access.

See: https://docs.oracle.com/en-us/iaas/Content/connector-hub/overview.htm#Authenti
"""

signer = oci.auth.signers.get_resource_principals_signer()
search_client = oci.resource_search.ResourceSearchClient(config={}, signer=signer)

"""
Set all registered loggers to the configured log_level
"""

logging_level = os.getenv('LOGGING_LEVEL', 'INFO')
loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]
[logger.setLevel(logging.getLevelName(logging_level)) for logger in loggers]

"""
The cache avoids having to lookup OCID tags more than once.
"""

tag_cache = {}

# -------------------------------------------
# Functions
# -------------------------------------------


def handler(ctx, data: io.BytesIO = None):
    """
    OCI Function Entry Point
    :param ctx: InvokeContext
    :param data: data payload
    :return: events with OCI tags added.
    """

    preamble = " {} / event count = {} / logging level = {}"

    try:
        payload = json.loads(data.getvalue())
        logging.getLogger().info(preamble.format(ctx.FnName(), len(payload), logging_level))
        add_tags_to_payload(payload)

        return response.Response(ctx,
                                 status_code=200,
                                 response_data=json.dumps(payload, indent=4),
                                 headers={"Content-Type": "application/json"})

    except (Exception, ValueError) as ex:
        logging.getLogger().error(f'error handling task function payload: {ex}')
        raise


def add_tags_to_payload(payload):
    """
    :param payload: payload is either a single event dictionary or a list of events.
    :return: the original payload (single event or list) with tags added.
    """

    if isinstance(payload, list):
        for event in payload:
            event_tags = assemble_event_tags(event)
            event[tag_assembly_key] = event_tags

    else:
        event_tags = assemble_event_tags(payload)
        payload[tag_assembly_key] = event_tags


def assemble_event_tags(event: dict):
    """
    Collects tags for each of the target ocids.
    :param event: dictionary of the task's event.
    :return: a dictionary of the assembled tags.  A dictionary makes it possible to support collection and
    return of tags for multiple ocids.
    """

    global tag_cache
    combined_tags = {}

    for target_ocid_key in target_ocid_keys:

        target_ocid = get_dictionary_value(event, target_ocid_key)
        logging.debug(f'target_ocid / {target_ocid_key} / {target_ocid}')

        if target_ocid is None:
            if target_ocid_keys_warn_if_not_found:
                logging.warning(f'target_ocid_key / not found / {target_ocid_key}')
                logging.debug(f'event / {event}')
            continue

        if isinstance(target_ocid, str) is False:
            logging.error(f'target_ocid / not a string !!! / {target_ocid}')
            logging.error(f'event / {event}')
            continue

        cached_tags = tag_cache.get(target_ocid)
        if cached_tags is not None:
            logging.debug(f'using cache / {target_ocid} / {cached_tags}')
            combined_tags[target_ocid] = cached_tags
            continue

        ocid_tags = retrieve_ocid_tags(target_ocid)
        combined_tags[target_ocid] = ocid_tags
        tag_cache[target_ocid] = ocid_tags

    logging.debug(f'combined_tags / {combined_tags}')
    return combined_tags


def retrieve_ocid_tags(ocid):
    """
    uses the OCI Search API to find the object metadata for the given ocid.
    :param ocid:
    :return: extracted tags for the given ocid.
    """

    ocid_tags = {}

    if ocid is None:
        return ocid_tags

    logging.debug(f'searching / {ocid}')
    structured_search = oci.resource_search.models.StructuredSearchDetails(
            query="query all resources where identifier = '{}'".format(ocid),
            matching_context_type=oci.resource_search.models.SearchDetails.MATCHING_CONTEXT_TYPE_NONE,
            type='Structured')

    search_response = search_client.search_resources(structured_search)
    # logging.debug(f'search_response.data / {search_response.data}')

    if hasattr(search_response, 'data'):

        resource_summary_collection = search_response.data
        for resource_summary in resource_summary_collection.items:

            if ocid != resource_summary.identifier:
                raise Exception(f'identifier mismatch / {ocid} / {resource_summary.identifier}')

            logging.debug(f'resource_summary / {resource_summary}')

            collect_tags(ocid_tags, 'freeform', include_freeform_tags, resource_summary.freeform_tags)
            collect_tags(ocid_tags, 'defined', include_defined_tags, resource_summary.defined_tags)
            collect_tags(ocid_tags, 'system', include_system_tags, resource_summary.system_tags)

    logging.debug(f'ocid_tags / {ocid} / {ocid_tags}')
    return ocid_tags


def collect_tags(dictionary, tag_type_key, inclusion_flag, results):
    """
    :param dictionary: add tags to this dict
    :param tag_type_key: label to use in the payload
    :param inclusion_flag: flag indicating if the type
    :param results: the tags for the given type
    :return: None
    """

    if inclusion_flag is False:
        return

    if not results and tag_assembly_omit_empty_results is True:
        return

    dictionary[tag_type_key] = results


def get_dictionary_value(dictionary: dict, target_key: str):
    """
    Recursive method to find value within a dictionary which may also have nested lists / dictionaries.
    :param dictionary: the dictionary to scan
    :param target_key: the key we are looking for
    :return: If a target_key exists multiple times in the dictionary, the first one found will be returned.
    """

    if dictionary is None:
        raise Exception(f'dictionary is None / {target_key}')

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
