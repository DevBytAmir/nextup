import pytest


@pytest.mark.parametrize("path", ["/number", "/counter", "/admin", "/tv"])
def test_page_route_serves_html(client, path):
    res = client.get(path)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert '<div id="app">' in res.text
