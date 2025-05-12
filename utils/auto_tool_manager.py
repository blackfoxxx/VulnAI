#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/auto_tool_manager.py
"""
This script automates the process of adding new tools to VulnLearnAI.
It can:
1. Detect tool programming language
2. Install tools automatically based on language
3. Generate metadata for new tools
4. Update the training data to include new tools
"""

import os
import sys
import json
import argparse
import subprocess
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import requests
import shutil
import tempfile

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error

# Constants
TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
TOOLS_METADATA_PATH = os.path.join(TOOLS_DIR, "tools_metadata.json")
TRAINING_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tools_training_data.jsonl")
TEMP_DIR = os.path.join(tempfile.gettempdir(), "vulnai_tools")


class ToolLanguageDetector:
    """Detects the programming language of a tool based on its repository."""
    
    LANGUAGE_MARKERS = {
        "go": [
            "go.mod", 
            "go.sum", 
            ".go"
        ],
        "python": [
            "requirements.txt", 
            "setup.py", 
            ".py", 
            "Pipfile",
            "pyproject.toml"
        ],
        "javascript": [
            "package.json", 
            "package-lock.json", 
            "node_modules", 
            ".js",
            ".ts"
        ],
        "ruby": [
            "Gemfile", 
            "Gemfile.lock", 
            ".rb", 
            ".gemspec"
        ],
        "rust": [
            "Cargo.toml", 
            "Cargo.lock", 
            ".rs"
        ],
        "c": [
            "Makefile", 
            ".c", 
            ".h"
        ],
        "cpp": [
            "CMakeLists.txt", 
            ".cpp", 
            ".hpp", 
            ".cxx"
        ],
    }
    
    def __init__(self):
        os.makedirs(TEMP_DIR, exist_ok=True)
    
    def _clone_repo(self, repo_url: str) -> str:
        """Clone a git repository to a temporary directory and return the path."""
        repo_name = os.path.basename(urlparse(repo_url).path).replace('.git', '')
        repo_path = os.path.join(TEMP_DIR, repo_name)
        
        # Check if repo already exists
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            
        try:
            log_info(f"Cloning repository {repo_url} to {repo_path}")
            subprocess.run(
                ["git", "clone", "--depth=1", repo_url, repo_path],
                check=True,
                capture_output=True,
                text=True
            )
            return repo_path
        except subprocess.CalledProcessError as e:
            log_error(f"Failed to clone repository: {e}")
            return ""
    
    def _check_for_language_markers(self, repo_path: str) -> Dict[str, int]:
        """Check for language markers in the repository."""
        if not repo_path:
            return {}
            
        language_scores = {lang: 0 for lang in self.LANGUAGE_MARKERS}
        
        # Walk through the repository
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
                
            # Check files for language markers
            for file in files:
                file_path = os.path.join(root, file)
                
                for lang, markers in self.LANGUAGE_MARKERS.items():
                    for marker in markers:
                        if marker.startswith('.'):  # File extension
                            if file.endswith(marker):
                                language_scores[lang] += 1
                        else:  # File name
                            if file == marker:
                                language_scores[lang] += 5  # Higher score for exact matches
        
        return language_scores
    
    def detect_language(self, repo_url: str) -> str:
        """Detect the primary programming language of a repository."""
        repo_path = self._clone_repo(repo_url)
        if not repo_path:
            return "unknown"
            
        language_scores = self._check_for_language_markers(repo_path)
        
        # GitHub API fallback if no clear winner
        max_score = max(language_scores.values()) if language_scores else 0
        if max_score < 3:
            github_language = self._get_github_language(repo_url)
            if github_language:
                return github_language.lower()
        
        # Get the language with the highest score
        if language_scores:
            primary_language = max(language_scores.items(), key=lambda x: x[1])
            if primary_language[1] > 0:
                return primary_language[0]
        
        return "unknown"
    
    def _get_github_language(self, repo_url: str) -> str:
        """Get the primary language from GitHub API."""
        # Extract owner and repo from URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2 or 'github.com' not in parsed_url.netloc:
            return ""
            
        owner, repo = path_parts[0], path_parts[1].replace('.git', '')
        
        # Call GitHub API
        try:
            response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/languages")
            if response.status_code == 200:
                languages = response.json()
                if languages:
                    # Return the language with the highest byte count
                    return max(languages.items(), key=lambda x: x[1])[0]
        except Exception as e:
            log_error(f"Failed to get language from GitHub API: {e}")
        
        return ""
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            log_error(f"Failed to clean up temporary directory: {e}")


class ToolInstaller:
    """Installs security tools based on their programming language."""
    
    def __init__(self):
        # Check for required dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        # Check for Git
        try:
            subprocess.run(
                ["git", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            log_error("Git is not installed. Please install Git to use this tool.")
            sys.exit(1)
    
    def _install_go_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a Go-based security tool."""
        if not self._check_go_installed():
            if not self._install_go():
                return False
        
        log_info(f"Installing Go tool: {tool_id}")
        
        # Handle default go install case
        if not install_commands:
            # Extract the Go package path from the repo URL
            parsed_url = urlparse(repo_url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) < 2 or 'github.com' not in parsed_url.netloc:
                log_error(f"Invalid GitHub repository URL: {repo_url}")
                return False
                
            owner, repo = path_parts[0], path_parts[1].replace('.git', '')
            go_package = f"github.com/{owner}/{repo}"
            
            log_info(f"Installing {go_package} using 'go install'")
            try:
                subprocess.run(
                    ["go", "install", f"{go_package}@latest"],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Go tool: {e}")
                return False
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Go tool: {e}")
                return False
        
        return True
    
    def _install_python_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a Python-based security tool."""
        log_info(f"Installing Python tool: {tool_id}")
        
        # Clone the repository if needed
        repo_path = ""
        for cmd in install_commands:
            if not cmd.startswith("pip") and not cmd.startswith("python"):
                # Might need to clone the repo first
                detector = ToolLanguageDetector()
                repo_path = detector._clone_repo(repo_url)
                if not repo_path:
                    return False
                break
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                if repo_path:
                    # Run the command in the repository directory
                    subprocess.run(
                        cmd,
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                else:
                    # Run the command in the current directory
                    subprocess.run(
                        cmd,
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True
                    )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Python tool: {e}")
                return False
        
        return True
    
    def _install_javascript_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a JavaScript-based security tool."""
        log_info(f"Installing JavaScript tool: {tool_id}")
        
        # Check if Node.js is installed
        if not self._check_nodejs_installed():
            log_error("Node.js is not installed. Please install Node.js to use this tool.")
            return False
        
        # Default to npm install if no commands provided
        if not install_commands:
            detector = ToolLanguageDetector()
            repo_path = detector._clone_repo(repo_url)
            if not repo_path:
                return False
                
            try:
                log_info(f"Running: npm install in {repo_path}")
                subprocess.run(
                    ["npm", "install"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                # Link the package globally if it has a bin entry
                subprocess.run(
                    ["npm", "link"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install JavaScript tool: {e}")
                return False
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install JavaScript tool: {e}")
                return False
        
        return True
    
    def _install_ruby_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a Ruby-based security tool."""
        log_info(f"Installing Ruby tool: {tool_id}")
        
        # Check if Ruby is installed
        if not self._check_ruby_installed():
            log_error("Ruby is not installed. Please install Ruby to use this tool.")
            return False
        
        # Default to gem install if no commands provided
        if not install_commands:
            # Try to extract the gem name from the repo URL
            parsed_url = urlparse(repo_url)
            repo_name = os.path.basename(parsed_url.path).replace('.git', '')
            
            try:
                log_info(f"Running: gem install {repo_name}")
                subprocess.run(
                    ["gem", "install", repo_name],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Ruby tool: {e}")
                return False
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Ruby tool: {e}")
                return False
        
        return True
    
    def _install_rust_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a Rust-based security tool."""
        log_info(f"Installing Rust tool: {tool_id}")
        
        # Check if Cargo is installed
        if not self._check_cargo_installed():
            log_error("Rust/Cargo is not installed. Please install Rust to use this tool.")
            return False
        
        # Default to cargo install if no commands provided
        if not install_commands:
            try:
                log_info(f"Running: cargo install --git {repo_url}")
                subprocess.run(
                    ["cargo", "install", "--git", repo_url],
                    check=True,
                    capture_output=True,
                    text=True
                )
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Rust tool: {e}")
                return False
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install Rust tool: {e}")
                return False
        
        return True
    
    def _install_c_cpp_tool(self, tool_id: str, repo_url: str, install_commands: List[str]) -> bool:
        """Install a C/C++-based security tool."""
        log_info(f"Installing C/C++ tool: {tool_id}")
        
        # Check if GCC/G++ is installed
        if not self._check_gcc_installed():
            log_error("GCC/G++ is not installed. Please install a C/C++ compiler to use this tool.")
            return False
        
        # C/C++ tools typically need to be compiled from source
        if not install_commands:
            detector = ToolLanguageDetector()
            repo_path = detector._clone_repo(repo_url)
            if not repo_path:
                return False
                
            try:
                # Typical build process: configure, make, make install
                if os.path.exists(os.path.join(repo_path, "configure")):
                    log_info("Running: ./configure")
                    subprocess.run(
                        ["./configure"],
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                
                log_info("Running: make")
                subprocess.run(
                    ["make"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                log_info("Running: sudo make install")
                subprocess.run(
                    ["sudo", "make", "install"],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                return True
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install C/C++ tool: {e}")
                return False
        
        # Use provided install commands
        for cmd in install_commands:
            try:
                log_info(f"Running: {cmd}")
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                log_error(f"Failed to install C/C++ tool: {e}")
                return False
        
        return True
    
    def _check_go_installed(self) -> bool:
        """Check if Go is installed."""
        try:
            subprocess.run(
                ["go", "version"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _install_go(self) -> bool:
        """Install Go if not already installed."""
        log_info("Go is not installed. Installing Go...")
        
        try:
            # Download the latest Go for macOS
            subprocess.run(
                ["curl", "-LO", "https://go.dev/dl/go1.21.6.darwin-amd64.pkg"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Install Go
            subprocess.run(
                ["sudo", "installer", "-pkg", "go1.21.6.darwin-amd64.pkg", "-target", "/"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Clean up
            os.remove("go1.21.6.darwin-amd64.pkg")
            
            # Add Go to PATH if not already there
            home_dir = os.path.expanduser("~")
            zshrc_path = os.path.join(home_dir, ".zshrc")
            
            with open(zshrc_path, "a") as f:
                f.write('export PATH=$PATH:/usr/local/go/bin\n')
                f.write('export PATH=$PATH:$HOME/go/bin\n')
            
            # Source the .zshrc file
            subprocess.run(
                ["source", zshrc_path],
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            
            log_info("Go has been installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            log_error(f"Failed to install Go: {e}")
            return False
    
    def _check_nodejs_installed(self) -> bool:
        """Check if Node.js is installed."""
        try:
            subprocess.run(
                ["node", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_ruby_installed(self) -> bool:
        """Check if Ruby is installed."""
        try:
            subprocess.run(
                ["ruby", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_cargo_installed(self) -> bool:
        """Check if Cargo (Rust) is installed."""
        try:
            subprocess.run(
                ["cargo", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_gcc_installed(self) -> bool:
        """Check if GCC/G++ is installed."""
        try:
            subprocess.run(
                ["gcc", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def install_tool(self, tool_id: str, tool_info: Dict[str, Any]) -> bool:
        """Install a security tool based on its language."""
        repo_url = tool_info.get("git_repo_url", "")
        if not repo_url:
            log_error(f"No git repository URL provided for tool: {tool_id}")
            return False
        
        install_commands = tool_info.get("install_commands", [])
        language = tool_info.get("language", "")
        
        # Detect language if not provided
        if not language:
            detector = ToolLanguageDetector()
            language = detector.detect_language(repo_url)
            detector.cleanup()
        
        # Install based on language
        if language == "go":
            return self._install_go_tool(tool_id, repo_url, install_commands)
        elif language == "python":
            return self._install_python_tool(tool_id, repo_url, install_commands)
        elif language == "javascript":
            return self._install_javascript_tool(tool_id, repo_url, install_commands)
        elif language == "ruby":
            return self._install_ruby_tool(tool_id, repo_url, install_commands)
        elif language == "rust":
            return self._install_rust_tool(tool_id, repo_url, install_commands)
        elif language in ["c", "cpp"]:
            return self._install_c_cpp_tool(tool_id, repo_url, install_commands)
        else:
            log_error(f"Unsupported language for tool {tool_id}: {language}")
            return False


class ToolMetadataGenerator:
    """Generates metadata for security tools."""
    
    def __init__(self):
        self.detector = ToolLanguageDetector()
    
    def _extract_description_from_repo(self, repo_url: str) -> str:
        """Extract a description from the repository."""
        repo_path = self.detector._clone_repo(repo_url)
        if not repo_path:
            return ""
            
        # Check for README files
        readme_paths = [
            os.path.join(repo_path, "README.md"),
            os.path.join(repo_path, "README"),
            os.path.join(repo_path, "readme.md"),
            os.path.join(repo_path, "Readme.md"),
        ]
        
        for readme_path in readme_paths:
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # Try to extract the first meaningful paragraph
                    lines = content.split("\n")
                    paragraph = ""
                    
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("![") and len(line) > 10:
                            paragraph = line
                            break
                    
                    if paragraph:
                        # Clean up markdown and limit length
                        paragraph = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', paragraph)  # Remove links
                        paragraph = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', paragraph)  # Remove emphasis
                        
                        if len(paragraph) > 150:
                            paragraph = paragraph[:147] + "..."
                            
                        return paragraph
                except Exception as e:
                    log_error(f"Failed to read README: {e}")
        
        return ""
    
    def _extract_command_from_help(self, tool_id: str, language: str) -> str:
        """Extract command template from tool help output."""
        try:
            # Try running the tool with --help or -h
            try:
                output = subprocess.run(
                    [tool_id, "--help"],
                    check=True,
                    capture_output=True,
                    text=True
                ).stdout
            except subprocess.CalledProcessError:
                output = subprocess.run(
                    [tool_id, "-h"],
                    check=False,  # Don't fail if this also fails
                    capture_output=True,
                    text=True
                ).stdout
            
            # Try to extract a basic command pattern
            lines = output.split("\n")
            usage_line = ""
            
            for line in lines:
                if "USAGE:" in line or "Usage:" in line or "usage:" in line:
                    usage_line = line
                    break
            
            if usage_line:
                # Extract just the command part
                parts = usage_line.split(":", 1)
                if len(parts) > 1:
                    command_part = parts[1].strip()
                    
                    # Replace specific arguments with placeholders
                    command_part = re.sub(r'<([^>]+)>', r'{\1}', command_part)
                    command_part = re.sub(r'\[([^\]]+)\]', r'{\1}', command_part)
                    
                    return command_part
            
            # Fallback to a simple template
            if language == "go":
                return f"{tool_id} {{target_url}}"
            elif language == "python":
                return f"python3 {tool_id} {{target_url}}"
            elif language == "javascript":
                return f"npx {tool_id} {{target_url}}"
            
            return f"{tool_id} {{target_url}}"
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If tool isn't in PATH yet, return a generic template
            if language == "go":
                return f"{tool_id} {{target_url}}"
            elif language == "python":
                return f"python3 {tool_id} {{target_url}}"
            elif language == "javascript":
                return f"npx {tool_id} {{target_url}}"
            
            return f"{tool_id} {{target_url}}"
    
    def _generate_natural_language_patterns(self, tool_id: str, name: str, description: str) -> List[str]:
        """Generate natural language patterns for tool detection."""
        patterns = [
            f"run {name.lower()}",
            f"use {name.lower()}",
            f"execute {name.lower()}",
            f"start {name.lower()} scan",
            f"scan with {name.lower()}"
        ]
        
        # Extract keywords from description
        if description:
            words = re.findall(r'\b\w+\b', description.lower())
            keywords = [word for word in words if len(word) > 3 and word not in ['with', 'this', 'that', 'from', 'tool']]
            
            if keywords:
                keywords = keywords[:3]  # Limit to top 3 keywords
                for keyword in keywords:
                    patterns.append(f"find {keyword}")
                    patterns.append(f"scan for {keyword}")
        
        return patterns
    
    def generate_metadata(self, tool_id: str, repo_url: str) -> Dict[str, Any]:
        """Generate metadata for a security tool."""
        # Detect language
        language = self.detector.detect_language(repo_url)
        
        # Generate tool name (capitalize tool_id)
        name = tool_id.capitalize()
        
        # Extract description
        description = self._extract_description_from_repo(repo_url)
        if not description:
            description = f"A security tool for {name}"
        
        # Determine category based on keywords in description
        category = "other"
        web_keywords = ["web", "http", "url", "site", "application", "crawler", "fuzzer"]
        network_keywords = ["network", "port", "scan", "discovery", "enumeration"]
        recon_keywords = ["reconnaissance", "recon", "discovery", "subdomain", "information"]
        
        description_lower = description.lower()
        if any(keyword in description_lower for keyword in web_keywords):
            category = "web_security"
        elif any(keyword in description_lower for keyword in network_keywords):
            category = "network"
        elif any(keyword in description_lower for keyword in recon_keywords):
            category = "reconnaissance"
        
        # Generate command
        command = self._extract_command_from_help(tool_id, language)
        
        # Generate natural language patterns
        patterns = self._generate_natural_language_patterns(tool_id, name, description)
        
        # Create metadata
        metadata = {
            "name": name,
            "description": description,
            "git_repo_url": repo_url,
            "language": language,
            "install_commands": [],  # Will be populated by the installer
            "category": category,
            "command": command,
            "expected_output": f"{name} scan results",
            "usage_example": f"Run {name} on https://example.com",
            "parameter_template": {
                "target_url": "https://example.com"
            },
            "default_param": "target_url",
            "natural_language_patterns": patterns
        }
        
        # Add language-specific install commands
        if language == "go":
            metadata["install_commands"] = [
                f"go install -v {repo_url.replace('https://github.com/', 'github.com/')}@latest"
            ]
        elif language == "python":
            metadata["install_commands"] = [
                "python3 -m pip install -r requirements.txt"
            ]
        
        return metadata
    
    def cleanup(self):
        """Clean up temporary files."""
        self.detector.cleanup()


class TrainingDataUpdater:
    """Updates training data to include new tools."""
    
    def __init__(self, training_data_path: str):
        self.training_data_path = training_data_path
    
    def generate_examples(self, tool_id: str, tool_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate training examples for a tool."""
        name = tool_info.get("name", tool_id.capitalize())
        description = tool_info.get("description", "")
        command = tool_info.get("command", f"{tool_id} {{target_url}}")
        category = tool_info.get("category", "other")
        
        examples = []
        
        # Example 1: What is the tool used for?
        examples.append({
            "messages": [
                {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                {"role": "user", "content": f"What is {name} used for?"},
                {"role": "assistant", "content": f"{name} is {description}. It's a {category} tool that helps security professionals in their assessments."}
            ]
        })
        
        # Example 2: How to use the tool
        examples.append({
            "messages": [
                {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                {"role": "user", "content": f"How do I use {name} to scan a website?"},
                {"role": "assistant", "content": f"To use {name}, you can run the following command:\n\n```\n{command.format(target_url='https://example.com')}\n```\n\nThis will scan the target website and provide results based on {name}'s capabilities."}
            ]
        })
        
        # Example 3: When to use the tool
        examples.append({
            "messages": [
                {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                {"role": "user", "content": f"When should I use {name}?"},
                {"role": "assistant", "content": f"{name} is most effective when you need to {description.lower()}. It's particularly useful for {category} assessments and can help identify potential vulnerabilities or issues."}
            ]
        })
        
        return examples
    
    def update_training_data(self, tool_id: str, tool_info: Dict[str, Any]) -> bool:
        """Update training data with examples for a new tool."""
        examples = self.generate_examples(tool_id, tool_info)
        
        try:
            # Read existing training data if it exists
            existing_examples = []
            if os.path.exists(self.training_data_path):
                with open(self.training_data_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            existing_examples.append(json.loads(line))
            
            # Add new examples
            with open(self.training_data_path, "w", encoding="utf-8") as f:
                # Write existing examples
                for example in existing_examples:
                    f.write(json.dumps(example) + "\n")
                
                # Write new examples
                for example in examples:
                    f.write(json.dumps(example) + "\n")
            
            log_info(f"Added {len(examples)} training examples for {tool_id}")
            return True
        except Exception as e:
            log_error(f"Failed to update training data: {e}")
            return False


class AutoToolManager:
    """Main class for managing security tools automatically."""
    
    def __init__(self):
        self.tools_metadata_path = TOOLS_METADATA_PATH
        self.training_data_path = TRAINING_DATA_PATH
        
        # Load existing tools metadata
        self.tools_metadata = self._load_tools_metadata()
        
        # Initialize components
        self.detector = ToolLanguageDetector()
        self.installer = ToolInstaller()
        self.metadata_generator = ToolMetadataGenerator()
        self.training_updater = TrainingDataUpdater(self.training_data_path)
    
    def _load_tools_metadata(self) -> Dict[str, Any]:
        """Load existing tools metadata."""
        try:
            if os.path.exists(self.tools_metadata_path):
                with open(self.tools_metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log_error(f"Failed to load tools metadata: {e}")
            return {}
    
    def _save_tools_metadata(self) -> bool:
        """Save tools metadata."""
        try:
            with open(self.tools_metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.tools_metadata, f, indent=4)
            return True
        except Exception as e:
            log_error(f"Failed to save tools metadata: {e}")
            return False
    
    def add_tool(self, tool_id: str, repo_url: str, install: bool = True, update_training: bool = True) -> bool:
        """Add a new security tool."""
        # Check if tool already exists
        if tool_id in self.tools_metadata:
            log_error(f"Tool '{tool_id}' already exists in the metadata.")
            return False
        
        log_info(f"Adding new tool: {tool_id} from {repo_url}")
        
        # Generate metadata
        tool_info = self.metadata_generator.generate_metadata(tool_id, repo_url)
        
        # Install the tool if requested
        if install:
            log_info(f"Installing tool: {tool_id}")
            if not self.installer.install_tool(tool_id, tool_info):
                log_error(f"Failed to install tool: {tool_id}")
                # Continue anyway to add metadata
        
        # Add to metadata
        self.tools_metadata[tool_id] = tool_info
        
        # Update the metadata file
        if not self._save_tools_metadata():
            log_error(f"Failed to save metadata for tool: {tool_id}")
            return False
        
        # Update training data if requested
        if update_training:
            log_info(f"Updating training data for tool: {tool_id}")
            if not self.training_updater.update_training_data(tool_id, tool_info):
                log_error(f"Failed to update training data for tool: {tool_id}")
                # Continue anyway since metadata was saved
        
        log_info(f"Successfully added tool: {tool_id}")
        return True
    
    def update_tool(self, tool_id: str, install: bool = True, update_training: bool = True) -> bool:
        """Update an existing security tool."""
        # Check if tool exists
        if tool_id not in self.tools_metadata:
            log_error(f"Tool '{tool_id}' does not exist in the metadata.")
            return False
        
        tool_info = self.tools_metadata[tool_id]
        repo_url = tool_info.get("git_repo_url", "")
        
        if not repo_url:
            log_error(f"No repository URL found for tool: {tool_id}")
            return False
        
        log_info(f"Updating tool: {tool_id} from {repo_url}")
        
        # Install the tool if requested
        if install:
            log_info(f"Reinstalling tool: {tool_id}")
            if not self.installer.install_tool(tool_id, tool_info):
                log_error(f"Failed to reinstall tool: {tool_id}")
                return False
        
        # Update training data if requested
        if update_training:
            log_info(f"Updating training data for tool: {tool_id}")
            if not self.training_updater.update_training_data(tool_id, tool_info):
                log_error(f"Failed to update training data for tool: {tool_id}")
                return False
        
        log_info(f"Successfully updated tool: {tool_id}")
        return True
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a security tool from metadata."""
        # Check if tool exists
        if tool_id not in self.tools_metadata:
            log_error(f"Tool '{tool_id}' does not exist in the metadata.")
            return False
        
        log_info(f"Removing tool: {tool_id}")
        
        # Remove from metadata
        del self.tools_metadata[tool_id]
        
        # Update the metadata file
        if not self._save_tools_metadata():
            log_error(f"Failed to save metadata after removing tool: {tool_id}")
            return False
        
        log_info(f"Successfully removed tool: {tool_id}")
        return True
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all security tools."""
        tools = []
        
        for tool_id, tool_info in self.tools_metadata.items():
            tools.append({
                "id": tool_id,
                "name": tool_info.get("name", tool_id.capitalize()),
                "language": tool_info.get("language", "unknown"),
                "category": tool_info.get("category", "other"),
                "description": tool_info.get("description", "")
            })
        
        return tools
    
    def cleanup(self):
        """Clean up temporary files."""
        self.detector.cleanup()
        self.metadata_generator.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Automatically manage security tools for VulnLearnAI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add tool command
    add_parser = subparsers.add_parser("add", help="Add a new security tool")
    add_parser.add_argument("tool_id", help="ID of the tool (e.g., nuclei, subfinder)")
    add_parser.add_argument("repo_url", help="URL of the git repository")
    add_parser.add_argument("--no-install", action="store_true", help="Don't install the tool")
    add_parser.add_argument("--no-training", action="store_true", help="Don't update training data")
    
    # Update tool command
    update_parser = subparsers.add_parser("update", help="Update an existing security tool")
    update_parser.add_argument("tool_id", help="ID of the tool to update")
    update_parser.add_argument("--no-install", action="store_true", help="Don't reinstall the tool")
    update_parser.add_argument("--no-training", action="store_true", help="Don't update training data")
    
    # Remove tool command
    remove_parser = subparsers.add_parser("remove", help="Remove a security tool")
    remove_parser.add_argument("tool_id", help="ID of the tool to remove")
    
    # List tools command
    subparsers.add_parser("list", help="List all security tools")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    manager = AutoToolManager()
    
    try:
        if args.command == "add":
            success = manager.add_tool(
                args.tool_id,
                args.repo_url,
                install=not args.no_install,
                update_training=not args.no_training
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "update":
            success = manager.update_tool(
                args.tool_id,
                install=not args.no_install,
                update_training=not args.no_training
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "remove":
            success = manager.remove_tool(args.tool_id)
            sys.exit(0 if success else 1)
            
        elif args.command == "list":
            tools = manager.list_tools()
            
            print("\nSecurity Tools:")
            print("=" * 80)
            print(f"{'ID':<15} {'Name':<20} {'Language':<10} {'Category':<15} {'Description':<50}")
            print("-" * 80)
            
            for tool in tools:
                description = tool["description"]
                if len(description) > 47:
                    description = description[:47] + "..."
                    
                print(f"{tool['id']:<15} {tool['name']:<20} {tool['language']:<10} {tool['category']:<15} {description:<50}")
            
            sys.exit(0)
            
        else:
            parser.print_help()
            sys.exit(1)
            
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
