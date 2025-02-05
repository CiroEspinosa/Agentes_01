import jsonref

from starter.helper.oai.oai_tools_helper import openapi_to_functions


def test_openapi_to_functions():
    functions: dict[str, dict[str, list[dict]]] = {}
    try:
        with open("tests/coreagents/starter/helper/oai/openapi.json", "r") as f:
            openapi_spec = jsonref.loads(f.read())
            functions = openapi_to_functions(openapi_spec)
    except FileNotFoundError as e:
        pass

    try:
        with open("coreagents/starter/helper/oai/openapi.json", "r") as f:
            openapi_spec = jsonref.loads(f.read())
            functions = openapi_to_functions(openapi_spec)
    except FileNotFoundError as e:
        pass

    try:
        with open("openapi.json", "r") as f:
            openapi_spec = jsonref.loads(f.read())
            functions = openapi_to_functions(openapi_spec)
    except FileNotFoundError as e:
        pass

    assert len(functions) > 0
