#!/bin/bash

# Setup script for Cloud9 AWS Linux 2023 instances
# This script installs Python 3.11, Terraform, and Git for both tutorial projects

set -e

echo "=================================="
echo "Cloud9 AWS Linux 2023 Setup Script"
echo "for Terraform Lambda + S3 Tutorials"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Setup common aliases
setup_common_aliases() {
    print_status "Setting up common aliases..."
    
    # Check if aliases section already exists
    if ! grep -q "# Common shell aliases" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Common shell aliases" >> ~/.bashrc
        echo "alias cls='clear'" >> ~/.bashrc
        echo "alias ll='ls -alF'" >> ~/.bashrc
        echo "alias la='ls -A'" >> ~/.bashrc
        echo "alias l='ls -CF'" >> ~/.bashrc
        echo "alias lt='ls -t -1 -long'" >> ~/.bashrc
        echo "alias ls='ls --color=auto'" >> ~/.bashrc
        echo "alias h='history'" >> ~/.bashrc
        echo "alias tree1='tree -a -L 1'" >> ~/.bashrc
        echo "alias tree2='tree -a -L 2'" >> ~/.bashrc
        echo "alias repos='cd ~/source/repos'" >> ~/.bashrc
        echo "alias c='clear'" >> ~/.bashrc
        echo "alias act='source .venv/bin/activate'" >> ~/.bashrc
        print_success "Common aliases added to ~/.bashrc"
    else
        print_success "Common aliases already exist in ~/.bashrc"
    fi
}

# Check if running on Amazon Linux
check_os() {
    if [[ ! -f /etc/os-release ]] || ! grep -q "Amazon Linux" /etc/os-release; then
        print_warning "This script is designed for Amazon Linux 2023. Proceeding anyway..."
    else
        print_status "Amazon Linux detected. Proceeding with setup..."
    fi
}

# Update system packages
update_system() {
    print_status "Updating system packages..."
    sudo yum update -y
    print_success "System packages updated"
}

# Install Python 3.11
install_python311() {
    print_status "Checking for Python 3.11..."
    
    if command -v python3.11 &> /dev/null; then
        print_success "Python 3.11 is already installed"
    else
        print_status "Installing Python 3.11..."
        # Install Python 3.11 on Amazon Linux 2023
        sudo yum install -y python3.11 python3.11-pip python3.11-devel
        print_success "Python 3.11 installed"
    fi
    
    # Verify installation
    python3.11 --version
}

# Set up Python aliases
setup_python_aliases() {
    print_status "Setting up Python aliases..."
    
    # Add aliases to .bashrc if they don't exist
    if ! grep -q "alias python=" ~/.bashrc; then
        echo "# Python 3.11 aliases for Terraform tutorials" >> ~/.bashrc
        echo "alias python=python3.11" >> ~/.bashrc
        echo "alias pip=pip3.11" >> ~/.bashrc
        print_success "Python aliases added to ~/.bashrc"
    else
        print_success "Python aliases already exist in ~/.bashrc"
    fi
    
    # Set aliases for current session
    alias python=python3.11
    alias pip=pip3.11
    
    print_status "Current Python version: $(python3.11 --version)"
    print_status "Current pip version: $(pip3.11 --version)"
}

# Install Git (usually pre-installed on Cloud9)
install_git() {
    print_status "Checking for Git..."
    
    if command -v git &> /dev/null; then
        print_success "Git is already installed: $(git --version)"
    else
        print_status "Installing Git..."
        sudo yum install -y git
        print_success "Git installed: $(git --version)"
    fi
}

# Install Terraform
install_terraform() {
    print_status "Checking for Terraform..."
    
    if command -v terraform &> /dev/null; then
        print_success "Terraform is already installed: $(terraform --version | head -n1)"
        return
    fi
    
    print_status "Installing Terraform..."
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download Terraform for Linux AMD64
    TERRAFORM_VERSION="1.7.0"
    print_status "Downloading Terraform v${TERRAFORM_VERSION}..."
    
    wget -q "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to download Terraform"
        exit 1
    fi
    
    # Unzip and install
    unzip -q "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
    sudo mv terraform /usr/local/bin/
    
    # Clean up
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    # Verify installation
    if command -v terraform &> /dev/null; then
        print_success "Terraform installed: $(terraform --version | head -n1)"
    else
        print_error "Terraform installation failed"
        exit 1
    fi
}

# Install additional useful tools
install_additional_tools() {
    print_status "Installing additional useful tools..."
    
    # Install jq for JSON parsing (useful for testing Lambda responses)
    if command -v jq &> /dev/null; then
        print_success "jq is already installed"
    else
        sudo yum install -y jq
        print_success "jq installed"
    fi
    
    # Install zip/unzip (usually pre-installed, but make sure)
    sudo yum install -y zip unzip
    print_success "zip/unzip tools verified"
    
    # Install make utility
    if command -v make &> /dev/null; then
        print_success "make is already installed"
    else
        sudo yum install -y make
        print_success "make installed"
    fi
    
    # Install essential development tools
    print_status "Installing essential development tools..."
    sudo yum groupinstall -y "Development Tools"
    print_success "Development Tools group installed"
    
    # Install additional useful utilities
    sudo yum install -y wget tree vim htop tmux
    print_success "Additional utilities (wget, tree, vim, htop, tmux) installed"
    
    # Upgrade curl to full version for better functionality
    if ! rpm -q curl-full &> /dev/null; then
        print_status "Upgrading curl to full version..."
        sudo yum install -y --allowerasing curl-full libcurl-full
        print_success "curl upgraded to full version"
    else
        print_success "curl-full already installed"
    fi
}

# Verify AWS CLI
verify_aws_cli() {
    print_status "Verifying AWS CLI..."
    
    if command -v aws &> /dev/null; then
        print_success "AWS CLI found: $(aws --version)"
        
        # Check if AWS credentials are configured
        if aws sts get-caller-identity &> /dev/null; then
            print_success "AWS credentials are configured"
            aws sts get-caller-identity --query 'Account' --output text | xargs echo "AWS Account:"
        else
            print_warning "AWS credentials not configured or insufficient permissions"
            print_status "Run 'aws configure' to set up credentials if needed"
        fi
    else
        print_warning "AWS CLI not found. Installing..."
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf awscliv2.zip aws/
        print_success "AWS CLI installed"
    fi
}

# Setup shell completions
setup_completions() {
    print_status "Setting up command completions..."
    
    # Setup AWS CLI completion
    if command -v aws &> /dev/null; then
        # Check if AWS completion is already in .bashrc
        if ! grep -q "aws_completer" ~/.bashrc; then
            print_status "Adding AWS CLI completion..."
            echo "" >> ~/.bashrc
            echo "# AWS CLI completion" >> ~/.bashrc
            echo "complete -C '/usr/local/bin/aws_completer' aws" >> ~/.bashrc
            print_success "AWS CLI completion added to ~/.bashrc"
        else
            print_success "AWS CLI completion already configured"
        fi
    fi
    
    # Setup Terraform completion
    if command -v terraform &> /dev/null; then
        # Check if Terraform completion is already in .bashrc
        if ! grep -q "terraform.*complete" ~/.bashrc; then
            print_status "Adding Terraform completion..."
            echo "" >> ~/.bashrc
            echo "# Terraform completion" >> ~/.bashrc
            echo "complete -C terraform terraform" >> ~/.bashrc
            print_success "Terraform completion added to ~/.bashrc"
        else
            print_success "Terraform completion already configured"
        fi
    fi
    
    print_success "Shell completions configured"
}

# Create workspace directories
setup_workspace() {
    print_status "Setting up workspace directories..."
    
    # Create a workspace directory if it doesn't exist
    mkdir -p ~/terraform-tutorials
    
    print_status "Workspace created at ~/terraform-tutorials"
    print_status "You can clone or copy the tutorial files there"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "=================================="
    print_success "Setup completed successfully!"
    echo "=================================="
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Reload your shell to use the new aliases:"
    echo -e "   ${YELLOW}source ~/.bashrc${NC}"
    echo ""
    echo "2. Verify installations:"
    echo -e "   ${YELLOW}python --version    # Should show Python 3.11.x${NC}"
    echo -e "   ${YELLOW}pip --version       # Should show pip for Python 3.11${NC}"
    echo -e "   ${YELLOW}terraform --version # Should show Terraform v1.7.0${NC}"
    echo -e "   ${YELLOW}git --version       # Should show Git version${NC}"
    echo ""
    echo "3. Test tab completion (after reload):"
    echo -e "   ${YELLOW}aws <TAB><TAB>       # Shows AWS CLI commands${NC}"
    echo -e "   ${YELLOW}terraform <TAB><TAB> # Shows Terraform commands${NC}"
    echo ""
    echo "4. Choose your tutorial:"
    echo -e "   ${YELLOW}cd quick-tf-intro/     # For beginners${NC}"
    echo -e "   ${YELLOW}cd sample-tf-project/  # For advanced users${NC}"
    echo ""
    echo "5. Follow the README.md in your chosen tutorial directory"
    echo ""
    print_success "Happy learning with Terraform!"
}

# Main execution
main() {
    print_status "Starting Cloud9 setup for Terraform tutorials..."
    
    check_os
    update_system
    install_python311
    setup_python_aliases
    install_git
    install_terraform
    install_additional_tools
    verify_aws_cli
    setup_completions
    setup_common_aliases
    setup_workspace
    show_next_steps
}

# Run main function
main "$@"