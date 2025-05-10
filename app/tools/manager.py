import os
import subprocess
import json
from pathlib import Path

class ToolsManager:
    def __init__(self, base_dir="tools"):
        self.base_dir = Path(base_dir)
        self.tools_dir = self.base_dir / "security"
        self.venv_dir = self.base_dir / "virtualenv"
        self.wordlists_dir = self.base_dir / "wordlists"
        self.tools_metadata_file = self.base_dir / "tools_metadata.json"
        self.preconfigured_tools_file = Path("../../../opt/vscodium/tools_metadata.json")
        
        # Create necessary directories
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.venv_dir.mkdir(parents=True, exist_ok=True)
        self.wordlists_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        if not self.tools_metadata_file.exists():
            self._save_tools_metadata({})

    def _save_tools_metadata(self, data):
        with open(self.tools_metadata_file, "w") as f:
            json.dump(data, f, indent=4)

    def _load_tools_metadata(self):
        if self.tools_metadata_file.exists():
            with open(self.tools_metadata_file, "r") as f:
                return json.load(f)
        return {}

    def create_virtualenv(self, env_name="vulnlearn_env"):
        env_path = self.venv_dir / env_name
        if not env_path.exists():
            subprocess.run(["python3", "-m", "venv", str(env_path)], check=True)
        return env_path

    def get_preconfigured_tools(self):
        """Get list of available preconfigured tools"""
        if self.preconfigured_tools_file.exists():
            with open(self.preconfigured_tools_file, "r") as f:
                return json.load(f)
        return {}

    def install_tool(self, tool_name, git_repo_url=None, install_cmds=None, category=None, description=None):
        """
        Install a tool by cloning its repo and running install commands inside virtualenv.
        Can install either a preconfigured tool by name or a custom tool with provided details.
        """
        # Check if it's a preconfigured tool
        preconfigured = self.get_preconfigured_tools()
        if tool_name in preconfigured and not git_repo_url:
            tool_info = preconfigured[tool_name]
            git_repo_url = tool_info["git_repo_url"]
            install_cmds = tool_info["install_commands"]
            category = tool_info["category"]
            description = tool_info["description"]

        tool_path = self.tools_dir / tool_name
        if tool_path.exists():
            return f"Tool {tool_name} already installed."

        # Clone repo if URL provided
        if git_repo_url:
            subprocess.run(["git", "clone", git_repo_url, str(tool_path)], check=True)
        else:
            tool_path.mkdir(parents=True, exist_ok=True)

        # Create virtualenv
        venv_path = self.create_virtualenv(f"venv_{tool_name}")

        # Run install commands inside virtualenv
        if install_cmds:
            for cmd in install_cmds:
                full_cmd = f"source {venv_path}/bin/activate && cd {tool_path} && {cmd}"
                subprocess.run(full_cmd, shell=True, check=True, executable="/bin/bash")

        # Update metadata
        metadata = self._load_tools_metadata()
        metadata[tool_name] = {
            "path": str(tool_path),
            "git_repo": git_repo_url,
            "category": category,
            "description": description,
            "venv_path": str(venv_path),
            "installed": True
        }
        self._save_tools_metadata(metadata)
        return f"Tool {tool_name} installed successfully."

    def list_tools(self):
        metadata = self._load_tools_metadata()
        return metadata

    def remove_tool(self, tool_name):
        metadata = self._load_tools_metadata()
        if tool_name not in metadata:
            return f"Tool {tool_name} not found."
        tool_path = Path(metadata[tool_name]["path"])
        if tool_path.exists():
            for root, dirs, files in os.walk(tool_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(tool_path)
        del metadata[tool_name]
        self._save_tools_metadata(metadata)
        return f"Tool {tool_name} removed successfully."
