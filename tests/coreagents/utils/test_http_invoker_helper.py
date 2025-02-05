from utils import http_invoker_helper


def test_compose_url_with_params():
    url_template: str = "http://127.0.0.1/person/{name}/age/{age_number}"
    params: dict = {
        "age_number": 30,
        "name": "John Doe"
    }

    assert http_invoker_helper.compose_url(url_template, params) == "http://127.0.0.1/person/John%20Doe/age/30"
