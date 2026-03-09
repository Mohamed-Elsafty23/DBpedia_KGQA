#!/bin/bash
# Deploy to HuggingFace with YAML frontmatter in README

FRONTMATTER="---
title: DBpedia KGQA
emoji: 🔍
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: \"6.9.0\"
app_file: app.py
pinned: false
---

"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cp -r . "$TEMP_DIR"
cd "$TEMP_DIR"

# Add frontmatter to README
TEMP_README=$(mktemp)
echo -n "$FRONTMATTER" > "$TEMP_README"
cat README.md >> "$TEMP_README"
mv "$TEMP_README" README.md

# Create orphan branch and push
git checkout --orphan hf-temp
git reset
git add --all -- ':!architecture.png' ':!architecture.drawio'
git commit -m "Deploy to HuggingFace"
git push hf hf-temp:main --force
git checkout main
git branch -D hf-temp

# Cleanup
cd -
rm -rf "$TEMP_DIR"
echo "✅ Deployed to HuggingFace with YAML frontmatter"
