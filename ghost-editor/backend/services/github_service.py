import shutil
import tempfile
import uuid
import git
import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        pass

    def clone_repository(self, repo_url: str) -> str:
        """Clones a repository into a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="ghost_editor_")
        logger.info(f"Cloning {repo_url} into {temp_dir}")
        try:
            git.Repo.clone_from(repo_url, temp_dir)
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    def get_pr_diff(self, repo_dir: str, pr_number: int):
        """Fetches the diff for a specific PR."""
        try:
            repo = git.Repo(repo_dir)
            
            # Fetch the PR branch
            # GitHub uses the refs/pull/ID/head mapping
            refspec = f"pull/{pr_number}/head:pr-{pr_number}"
            origin = repo.remotes.origin
            origin.fetch(refspec)
            
            # Create the diff against main (assuming 'main' or 'master' is the target branch)
            # You might need to query the GitHub API to find the exact base branch
            try:
                base_branch = 'main'
                diff_text = repo.git.diff(f"origin/{base_branch}...pr-{pr_number}")
            except git.exc.GitCommandError:
                # Fallback to master if main doesn't exist
                base_branch = 'master'
                diff_text = repo.git.diff(f"origin/{base_branch}...pr-{pr_number}")

            return diff_text
            
        except Exception as e:
            logger.error(f"Error fetching PR diff for PR #{pr_number}: {e}")
            return None
        
    def cleanup_repo(self, repo_dir: str):
        """Removes the cloned repository directory."""
        if os.path.exists(repo_dir):
            logger.info(f"Cleaning up {repo_dir}")
            shutil.rmtree(repo_dir, ignore_errors=True)

github_service = GitHubService()
