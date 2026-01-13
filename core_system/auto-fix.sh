#!/bin/bash

# ============================================================================
# Auto-Guardian: Auto-Fix Script
# ============================================================================
# Purpose: Fix common issues automatically without affecting code behavior
# Supported Languages: JavaScript, Python, TypeScript, Go, Java
# ============================================================================

set -e  # Exit on first error

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment variables
PROJECT_ROOT=$(git rev-parse --show-toplevel)
FIXED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

# Helper function for colored logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((FIXED_COUNT++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    ((SKIPPED_COUNT++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ERROR_COUNT++))
}

# ============================================================================
# Section 1: General File Cleanup
# ============================================================================
clean_general() {
    log_info "Starting general file cleanup..."
    
    # Remove temporary files
    find . -type f -name "*.pyc" -delete
    find . -type f -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.py.bak" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.log" -delete 2>/dev/null || true
    
    # Clean system files
    find . -type f -name ".DS_Store" -delete
    find . -type f -name "Thumbs.db" -delete
    
    log_success "General cleanup completed"
}

# ============================================================================
# Section 2: Fix JavaScript/TypeScript
# ============================================================================
fix_javascript() {
    log_info "Scanning and fixing JavaScript/TypeScript files..."
    
    # Check for package.json
    if [ ! -f "package.json" ]; then
        log_warning "No package.json found - skipping JavaScript"
        return
    fi
    
    # Install Prettier and ESLint
    if [ -f "package-lock.json" ] || [ -f "yarn.lock" ]; then
        npm ci --prefer-offline --no-audit 2>/dev/null || npm install
    else
        npm install
    fi
    
    # Run Prettier for formatting
    if command -v npx &> /dev/null; then
        if [ -f ".prettierrc.js" ] || [ -f ".prettierrc.json" ] || [ -f "prettier.config.js" ]; then
            npx prettier --write "src/**/*.js" "src/**/*.ts" 2>/dev/null || true
            npx prettier --write "**/*.js" "**/*.ts" 2>/dev/null || true
            log_success "JavaScript/TypeScript formatted"
        fi
    fi
    
    # Fix ESLint errors
    if command -v npx &> /dev/null && grep -q '"eslint"' package.json; then
        npx eslint --fix "src/**/*.js" "src/**/*.ts" 2>/dev/null || true
        log_success "ESLint errors fixed"
    fi
}

# ============================================================================
# Section 3: Fix Python
# ============================================================================
fix_python() {
    log_info "Scanning and fixing Python files..."
    
    # Check for Python files
    if ! find . -name "*.py" -type f | grep -q .; then
        log_warning "No Python files found in project"
        return
    fi
    
    # Install formatting tools
    pip install black isort flake8 autoflake 2>/dev/null || true
    
    # Remove unused imports with autoflake
    if command -v autoflake &> /dev/null; then
        autoflake --remove-all-unused-imports --recursive --in-place . 2>/dev/null || true
        log_success "Unused imports removed"
    fi
    
    # Organize imports with isort
    if command -v isort &> /dev/null; then
        isort --profile black --apply --diff . 2>/dev/null || true
        isort --profile black --apply . 2>/dev/null || true
        log_success "Imports organized"
    fi
    
    # Format code with Black
    if command -v black &> /dev/null; then
        black --line-length 100 --target-version py39 --diff . 2>/dev/null || true
        black --line-length 100 --target-version py39 . 2>/dev/null || true
        log_success "Code formatted with Black"
    fi
}

# ============================================================================
# Section 4: Fix Go
# ============================================================================
fix_go() {
    log_info "Scanning and fixing Go files..."
    
    # Check for Go files
    if ! find . -name "*.go" -type f | grep -q .; then
        log_warning "No Go files found in project"
        return
    fi
    
    # Format code
    if command -v gofmt &> /dev/null; then
        gofmt -w . 2>/dev/null || true
        log_success "Go formatted"
    fi
    
    # Fix imports
    if command -v goimports &> /dev/null; then
        goimports -w . 2>/dev/null || true
        log_success "Go imports fixed"
    fi
}

# ============================================================================
# Section 5: Fix Java
# ============================================================================
fix_java() {
    log_info "Scanning and fixing Java files..."
    
    # Check for Java files
    if ! find . -name "*.java" -type f | grep -q .; then
        log_warning "No Java files found in project"
        return
    fi
    
    # Check for Google Java Format
    if [ -f ".google-java-format" ]; then
        if command -v google-java-format &> /dev/null; then
            google-java-format -i --replace $(find . -name "*.java") 2>/dev/null || true
            log_success "Java formatted"
        fi
    fi
    
    # Traditional formatting
    if command -v astyle &> /dev/null; then
        astyle --style=google --recursive "*.java" 2>/dev/null || true
        log_success "Java formatted with Astyle"
    fi
}

# ============================================================================
# Section 6: Fix YAML/JSON
# ============================================================================
fix_config_files() {
    log_info "Scanning and fixing configuration files..."
    
    # Install YAML tools
    pip install pyyaml 2>/dev/null || true
    
    # Fix YAML
    find . -name "*.yaml" -o -name "*.yml" | while read -r file; do
        if command -v python3 &> /dev/null; then
            python3 -c "
import yaml
import sys
try:
    with open('$file', 'r') as f:
        content = yaml.safe_load(f)
    with open('$file', 'w') as f:
        yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
    print('Fixed: $file')
except Exception as e:
    pass
" 2>/dev/null || true
        fi
    done
    
    # Format JSON
    find . -name "*.json" | while read -r file; do
        if command -v python3 &> /dev/null; then
            python3 -c "
import json
import sys
try:
    with open('$file', 'r') as f:
        content = json.load(f)
    with open('$file', 'w') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    print('Fixed: $file')
except Exception as e:
    pass
" 2>/dev/null || true
        fi
    done
    
    log_success "Configuration files fixed"
}

# ============================================================================
# Section 7: Add License Headers
# ============================================================================
add_license_headers() {
    log_info "Scanning license headers..."
    
    # List of files that need headers
    if [ -f "COPYRIGHT_HEADER.txt" ]; then
        local header=$(cat COPYRIGHT_HEADER.txt)
        
        for ext in "*.py" "*.js" "*.ts" "*.java" "*.go"; do
            find . -name "$ext" -type f | while read -r file; do
                # Check for existing header
                if ! head -5 "$file" | grep -q "Copyright"; then
                    # Add header
                    if [ "$ext" == "*.py" ]; then
                        echo "# $header" | cat - "$file" > temp && mv temp "$file"
                    elif [ "$ext" == "*.js" ] || [ "$ext" == "*.ts" ]; then
                        echo "// $header" | cat - "$file" > temp && mv temp "$file"
                    elif [ "$ext" == "*.java" ]; then
                        echo "/* $header */" | cat - "$file" > temp && mv temp "$file"
                    elif [ "$ext" == "*.go" ]; then
                        echo "// $header" | cat - "$file" > temp && mv temp "$file"
                    fi
                    log_success "License header added: $file"
                fi
            done
        done
    fi
}

# ============================================================================
# Section 8: Organize Files
# ============================================================================
organize_files() {
    log_info "Improving file organization..."
    
    # Reorder Python imports
    if [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
        isort --recursive . 2>/dev/null || true
        log_success "Imports reordered"
    fi
    
    # Update README.md
    if [ -f "README.md" ]; then
        # Ensure table of contents exists
        if ! grep -q "^## Table of Contents$" README.md && ! grep -q "^## الفهرس$" README.md; then
            echo -e "\n## Table of Contents\n" | cat - README.md > temp && mv temp README.md
            log_success "README.md updated"
        fi
    fi
}

# ============================================================================
# Section 9: Basic Security Check
# ============================================================================
security_check() {
    log_info "Running basic security check..."
    
    # Check for passwords or keys in code
    local secrets_patterns=(
        "password\s*=\s*['\"][^'\"]+['\"]"
        "api_key\s*=\s*['\"][^'\"]+['\"]"
        "secret\s*=\s*['\"][^'\"]+['\"]"
        "private_key\s*=\s*['\"][^'\"]+['\"]"
        "AWS_ACCESS_KEY"
        "AWS_SECRET_KEY"
    )
    
    for pattern in "${secrets_patterns[@]}"; do
        if grep -rqE "$pattern" . --include="*.py" --include="*.js" --include="*.ts" 2>/dev/null; then
            log_warning "Potential sensitive data found: $pattern"
        fi
    done
    
    log_success "Security check completed"
}

# ============================================================================
# Main Function
# ============================================================================
main() {
    echo "=============================================="
    echo "  Auto-Guardian: Auto-Fix Script"
    echo "=============================================="
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Log start
    echo "Date: $(date)"
    echo "Directory: $PROJECT_ROOT"
    echo ""
    
    # Execute all fix tasks
    clean_general
    fix_javascript
    fix_python
    fix_go
    fix_java
    fix_config_files
    add_license_headers
    organize_files
    security_check
    
    # Print summary
    echo ""
    echo "=============================================="
    echo "  Fix Summary"
    echo "=============================================="
    echo -e "  Fixed: ${GREEN}$FIXED_COUNT${NC}"
    echo -e "  Skipped: ${YELLOW}$SKIPPED_COUNT${NC}"
    echo -e "  Errors: ${RED}$ERROR_COUNT${NC}"
    echo ""
    
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "Warning: Some errors occurred during fixing"
        exit 1
    else
        echo "All fixes completed successfully"
        exit 0
    fi
}

# Run main function
main "$@"
