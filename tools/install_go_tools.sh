#!/bin/bash
# filepath: /Users/mac/VulnAI/tools/install_go_tools.sh

# This script installs Go-based security tools for the VulnLearnAI project

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Go is not installed. Installing Go..."
    
    # Download the latest Go for macOS
    curl -LO https://go.dev/dl/go1.21.6.darwin-amd64.pkg
    
    # Install Go
    sudo installer -pkg go1.21.6.darwin-amd64.pkg -target /
    
    # Clean up
    rm go1.21.6.darwin-amd64.pkg
    
    # Add Go to PATH if not already there
    if [[ ! "$PATH" == *"/usr/local/go/bin"* ]]; then
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.zshrc
        echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.zshrc
        source ~/.zshrc
    fi
    
    echo "Go has been installed successfully."
else
    echo "Go is already installed."
fi

# Install Go-based security tools
echo "Installing Go-based security tools..."

# Install Nuclei
echo "Installing Nuclei..."
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Install Subfinder
echo "Installing Subfinder..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install httpx
echo "Installing httpx..."
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install Katana (Web Crawler)
echo "Installing Katana..."
go install -v github.com/projectdiscovery/katana/cmd/katana@latest

# Install Naabu (Port Scanner)
echo "Installing Naabu..."
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Install Gau (URL Extractor)
echo "Installing Gau..."
go install -v github.com/lc/gau/v2/cmd/gau@latest

# Download Nuclei templates
echo "Downloading Nuclei templates..."
nuclei -update-templates

echo "All Go tools have been installed successfully!"
echo "Make sure $HOME/go/bin is in your PATH variable to use these tools."
echo "The tools are ready to use with VulnLearnAI."
