#!/usr/bin/env python3
"""
Pull Request Summary Commenter

This script posts the generated PR summary as a comment on the pull request.
"""

import argparse
import os
import sys
from typing import Optional


def post_pr_comment(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    summary_file: str,
    github_token: str,
) -> bool:
    """Post PR summary as a comment."""
    try:
        import requests
    except ImportError:
        print(
            "Error: requests library not found. Install with: pip install requests",
            file=sys.stderr,
        )
        return False

    # Read summary content
    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_content = f.read()
    except FileNotFoundError:
        print(f"Error: Summary file {summary_file} not found", file=sys.stderr)
        return False

    # GitHub API endpoint
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Policy-as-Code-PR-Summary",
    }

    data = {"body": summary_content}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        print(f"Successfully posted PR summary comment for PR #{pr_number}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Post PR summary as comment")
    parser.add_argument(
        "--pr-number", type=int, required=True, help="Pull request number"
    )
    parser.add_argument("--repo-owner", required=True, help="Repository owner")
    parser.add_argument("--repo-name", required=True, help="Repository name")
    parser.add_argument(
        "--summary-file", required=True, help="Path to summary markdown file"
    )

    args = parser.parse_args()

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    success = post_pr_comment(
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        pr_number=args.pr_number,
        summary_file=args.summary_file,
        github_token=github_token,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
