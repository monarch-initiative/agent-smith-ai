from monarch_assistant.utility_agent import _python_type_to_json_schema
import typing

def test_python_type_to_json_schema_str():
    assert _python_type_to_json_schema(str) == {'type': 'string'}

def test_python_type_to_json_schema_number():
    assert _python_type_to_json_schema(int) == {'type': 'number'}
    assert _python_type_to_json_schema(float) == {'type': 'number'}

def test_python_type_to_json_schema_bool():
    assert _python_type_to_json_schema(bool) == {'type': 'boolean'}


def test_python_type_to_json_schema_dicts():
    type = typing.Dict[str, int]
    assert _python_type_to_json_schema(type) == {
        'type': 'object',
        'properties': {
            'key': {'type': 'string'},
            'value': {'type': 'number'}
        }
    }

    type = typing.Dict[str, typing.Dict[str, int]]
    assert _python_type_to_json_schema(type) == {
        'type': 'object',
        'properties': {
            'key': {'type': 'string'},
            'value': {
                'type': 'object',
                'properties': {
                    'key': {'type': 'string'},
                    'value': {'type': 'number'}
                }
            }
        }
    }

def test_python_type_to_json_schema_lists():
    type = typing.List[int]
    assert _python_type_to_json_schema(type) == {
        'type': 'array',
        'items': {'type': 'number'}
    }

    type = typing.List[typing.Dict[str, int]]
    assert _python_type_to_json_schema(type) == {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'key': {'type': 'string'},
                'value': {'type': 'number'}
            }
        }
    }

    type = typing.List[typing.List[str]]
    assert _python_type_to_json_schema(type) == {
        'type': 'array',
        'items': {
            'type': 'array',
            'items': {'type': 'string'}
        }
    }