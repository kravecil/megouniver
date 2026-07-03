from urllib.parse import parse_qs, urlparse


def get_page_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    # parsed.fragment = "?id=019ee529-454f-7e45-aced-7f2361797e11&foo=1"
    qs = parse_qs(parsed.fragment.lstrip("/?"))  # убираем '?', если есть
    page_id_values = qs.get("id", [None])[0]

    return page_id_values
