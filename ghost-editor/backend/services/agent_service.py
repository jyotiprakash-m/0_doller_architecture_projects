import subprocess
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        pass

    def run_aider(self, repo_dir: str, prompt: str) -> Optional[str]:
         """
         Executes 'aider' in the repository directory to update documentation.
         This is a synchronous call. For production, this should run async.
         """
         logger.info(f"Running Aider in {repo_dir} with prompt: {prompt}")
         
         # Example command: aider --message "Update the README based on recent changes..."
         # Aider must be installed in the environment where the backend is running.
         try:
            # We use --yes to auto-commit and avoid interactive prompts
            cmd = ["aider", "--message", prompt, "--yes"]
            
            result = subprocess.run(
                cmd,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=False # Don't raise exception on non-zero exit, handle it
            )
            
            if result.returncode != 0:
                 logger.error(f"Aider execution failed. Stderr: {result.stderr}")
                 return f"Error: Aider failed with code {result.returncode}\n{result.stderr}"
                 
            logger.info("Aider completed successfully.")
            return result.stdout
            
         except Exception as e:
            logger.error(f"Exception running aider: {e}")
            return f"Error: {e}"

agent_service = AgentService()
