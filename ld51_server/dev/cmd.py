from ld51_server.protocol import Message


def print_message_schema():
    print(Message.schema_json())
