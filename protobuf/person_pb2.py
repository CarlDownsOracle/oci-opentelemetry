# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sample.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0csample.proto\"\x91\x02\n\x06Person\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\x05\x12\r\n\x05\x65mail\x18\x03 \x01(\t\x12#\n\x06phones\x18\x04 \x03(\x0b\x32\x13.Person.PhoneNumber\x1aO\n\x0bPhoneNumber\x12\x0e\n\x06number\x18\x01 \x01(\t\x12\x30\n\x04type\x18\x02 \x01(\x0e\x32\x11.Person.PhoneType:\x0fPHONE_TYPE_HOME\"h\n\tPhoneType\x12\x1a\n\x16PHONE_TYPE_UNSPECIFIED\x10\x00\x12\x15\n\x11PHONE_TYPE_MOBILE\x10\x01\x12\x13\n\x0fPHONE_TYPE_HOME\x10\x02\x12\x13\n\x0fPHONE_TYPE_WORK\x10\x03\"&\n\x0b\x41\x64\x64ressBook\x12\x17\n\x06people\x18\x01 \x03(\x0b\x32\x07.Person')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'sample_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_PERSON']._serialized_start=17
  _globals['_PERSON']._serialized_end=290
  _globals['_PERSON_PHONENUMBER']._serialized_start=105
  _globals['_PERSON_PHONENUMBER']._serialized_end=184
  _globals['_PERSON_PHONETYPE']._serialized_start=186
  _globals['_PERSON_PHONETYPE']._serialized_end=290
  _globals['_ADDRESSBOOK']._serialized_start=292
  _globals['_ADDRESSBOOK']._serialized_end=330
# @@protoc_insertion_point(module_scope)
