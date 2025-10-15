#!/bin/bash

# Quick script to push code to repository
# Make sure to update the repository URL and branch name

# Configuration
REPO_URL="https://github.com/yourusername/recommendation-gen.git"  # Update this
BRANCH_NAME="main"  # or "master" depending on your repo
COMMIT_MESSAGE="Enhanced validation system with patient-specific search queries"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Pushing recommendation-gen to repository...${NC}"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📁 Initializing git repository...${NC}"
    git init
fi

# Add all files
echo -e "${YELLOW}📝 Adding files to git...${NC}"
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}ℹ️  No changes to commit${NC}"
    exit 0
fi

# Commit changes
echo -e "${YELLOW}💾 Committing changes...${NC}"
git commit -m "$COMMIT_MESSAGE"

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo -e "${YELLOW}🔗 Adding remote origin...${NC}"
    git remote add origin "$REPO_URL"
fi

# Push to repository
echo -e "${YELLOW}⬆️  Pushing to repository...${NC}"
git push -u origin "$BRANCH_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully pushed to repository!${NC}"
    echo -e "${GREEN}🔗 Repository: $REPO_URL${NC}"
    echo -e "${GREEN}🌿 Branch: $BRANCH_NAME${NC}"
else
    echo -e "${RED}❌ Failed to push to repository${NC}"
    echo -e "${YELLOW}💡 Make sure you have:${NC}"
    echo -e "${YELLOW}   - Valid repository URL${NC}"
    echo -e "${YELLOW}   - Proper authentication (SSH key or token)${NC}"
    echo -e "${YELLOW}   - Write access to the repository${NC}"
    exit 1
fi




