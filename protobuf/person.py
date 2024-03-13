from person_pb2 import *

person = Person()
person.id = 1234
person.name = "John Doe"
person.email = "jdoe@example.com"
phone = person.phones.add()
phone.number = "555-4321"
phone.type = Person.PHONE_TYPE_HOME

print(person)


