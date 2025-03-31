from locust import HttpUser, task, between
import uuid

class ShortenerUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def log(self):
        self.client.post(
            "/auth/logout"
        )
    @task
    def create_link(self):
        self.client.post(
            "/api/links/shorten",
            json={
            "original_url": "https://example.com/test",
            "custom_alias": f"{uuid.uuid4()}"
                 }
        )

    @task(3)
    def redirect_link(self):
        self.client.get(f"/api/links/{uuid.uuid4()}")

