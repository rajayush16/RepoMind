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


async def get_pull_request(access_token: str, owner: str, repo: str, pr_number: int) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
    if response.status_code != 200:
        raise GithubApiError(f"GitHub API error ({response.status_code}): {response.text}")
    return response.json()


async def get_pull_request_files(
    access_token: str, owner: str, repo: str, pr_number: int, max_files: int = 50
) -> list[dict]:
    """Changed files + unified diff patches for a PR (paginated, capped)."""
    files: list[dict] = []
    page = 1

    async with httpx.AsyncClient(timeout=15.0) as client:
        while len(files) < max_files:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
                params={"per_page": 100, "page": page},
            )
            if response.status_code != 200:
                raise GithubApiError(f"GitHub API error ({response.status_code}): {response.text}")

            batch = response.json()
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    return files[:max_files]


async def post_issue_comment(access_token: str, owner: str, repo: str, issue_number: int, body: str) -> dict:
    """Posts a single comment on a PR (PRs are issues in GitHub's API). Never
    called automatically -- only from an endpoint that requires explicit
    confirmation from the user first."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            json={"body": body},
        )
    if response.status_code not in (200, 201):
        raise GithubApiError(f"GitHub API error ({response.status_code}): {response.text}")
    return response.json()
