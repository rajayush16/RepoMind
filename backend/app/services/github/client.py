import httpx

GITHUB_API_BASE = "https://api.github.com"


class GithubApiError(Exception):
    pass


async def list_user_repositories(access_token: str) -> list[dict]:
    """Fetch repositories the authenticated GitHub user has access to (paginated)."""
    repos: list[dict] = []
    page = 1

    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            response = await client.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"per_page": 100, "page": page, "sort": "updated"},
            )
            if response.status_code != 200:
                raise GithubApiError(f"GitHub API error ({response.status_code}): {response.text}")

            batch = response.json()
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
            if page > 10:  # hard cap: 1000 repos, avoids unbounded pagination
                break

    return repos
