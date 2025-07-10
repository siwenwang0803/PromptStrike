# 🎯 Final DOD Validation Steps

## Quick Validation (2 minutes)

### 1. Test GitHub Pages
```bash
curl -f https://siwenwang0803.github.io/RedForge
```
**Expected**: Should return HTML page (not 404)

### 2. Test Helm Repository Index
```bash
curl -f https://siwenwang0803.github.io/RedForge/index.yaml
```
**Expected**: Should return YAML content (not 404)

### 3. Run Full DOD Validation
```bash
./validate_final_dod.sh
```
**Expected**: All tests pass with green checkmarks

## Comprehensive Validation (5 minutes)

### 1. Manual Helm Commands
```bash
# Add repository
helm repo add redforge https://siwenwang0803.github.io/RedForge

# Update repository index
helm repo update

# Search for charts
helm search repo redforge

# Test installation (dry-run)
helm install guardrail redforge/redforge-sidecar \
  -n ps \
  --set openai.apiKey="test-key" \
  --create-namespace \
  --dry-run
```

### 2. Screenshot Evidence Collection
```bash
# Generate evidence file
./validate_final_dod.sh

# View evidence
cat helm_install_evidence.txt

# Take screenshots of:
# - helm search repo redforge (showing available charts)
# - helm install --dry-run output (showing successful validation)
# - helm_install_evidence.txt content
```

## Alternative Validation Methods

### Option A: Check GitHub Actions
1. Go to: https://github.com/siwenwang0803/RedForge/actions
2. Look for "Release Helm Chart" workflow
3. Verify latest run shows "success" ✅

### Option B: Check GitHub Pages Settings
1. Go to: https://github.com/siwenwang0803/RedForge/settings/pages
2. Verify "Your site is live at: https://siwenwang0803.github.io/RedForge"
3. Click the URL to test accessibility

### Option C: Check Repository Files
1. Go to: https://github.com/siwenwang0803/RedForge/tree/gh-pages
2. Look for `index.yaml` and `.tgz` files
3. Verify chart packages are present

## Troubleshooting

### If index.yaml returns 404:
- Wait 5-10 more minutes (GitHub Pages can be slow)
- Check GitHub Actions workflow completed successfully
- Verify gh-pages branch has content

### If helm commands fail:
- Ensure Helm 3.x is installed: `helm version`
- Clear Helm cache: `helm repo remove redforge; rm -rf ~/.cache/helm`
- Try again with verbose output: `helm repo add --debug`

### If chart installation fails:
- This is expected due to missing CRDs (Gatekeeper, Prometheus)
- The important part is that helm can FIND and VALIDATE the chart
- Dry-run success = DOD requirement met

## Success Criteria

**✅ DOD Complete when:**
1. `curl` commands return content (not 404)
2. `helm repo add` succeeds without errors
3. `helm search repo redforge` shows charts
4. `helm install --dry-run` validates successfully (even if it warns about CRDs)

**📸 Screenshot Evidence:**
- Terminal showing successful `helm search repo redforge`
- Contents of `helm_install_evidence.txt` file
- Successful `helm install --dry-run` command

## Timeline

- **If GitHub Pages is ready**: Validation takes 2-3 minutes
- **If GitHub Pages is propagating**: Wait 10-15 minutes, then validate
- **Total time from workflow completion**: Usually 15-20 minutes max