from src.auth.models import User
from src.url.models import Link, Tag


def test_search_by_url(client, db):
    link = Link(
        original_url="https://example.com/search-test",
        short_code="search123"
    )
    db.add(link)
    db.commit()


    response = client.get("/api/links/search?search_term=search-test")
    assert response.status_code == 200
    results = response.json()
    assert any(item["short_code"] == "search123" for item in results)


def test_search_by_tag(client, db):

    tag = Tag(name="special")
    link = Link(
        original_url="https://tag-test.com",
        short_code="tag123",
        tag=tag
    )
    db.add_all([tag, link])
    db.commit()


    response = client.get("/api/links/search?tag_name=special")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["tag_name"] == "special"


def test_empty_search_results(client):
    response = client.get("/api/links/search?original_url=non-existent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ссылки не найдены"


def test_combined_search(client, db):

    tag = Tag(name="combined")
    link = Link(
        original_url="https://combined.com/test",
        short_code="comb123",
        tag=tag
    )
    db.add_all([tag, link])
    db.commit()


    response = client.get(
        "/api/links/search?"
        "search_term=combined&"
        "tag_name=combined"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1