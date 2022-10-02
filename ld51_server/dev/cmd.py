from ld51_server.models import Message


def print_message_schema():
    print(Message.schema_json())
