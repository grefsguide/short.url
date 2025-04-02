from locust import HttpUser, task, between
import secrets

class ShortenerUser(HttpUser):
    wait_time = between(1, 3)
    short_code = None

    def gen_short_code(self, length: int = 10) -> str:
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @task
    def log(self):
        self.client.post(
            "/auth/logout"
        )
    @task
    def create_link(self):
        self.short_code = self.gen_short_code()
        self.client.post(
            "/api/links/shorten",
            json={
            "original_url": "https://example.com/test",
            "custom_alias": f"{self.short_code}"
                 }
        )

    @task(3)
    def redirect_link(self):
        if self.short_code:
            self.client.get(f"/api/links/{self.short_code}")

