# PromptStrike Helm Deployment Test Report

**Date**: Wed Jul  9 19:27:35 PDT 2025
**Test Suite**: Comprehensive Helm Deployment
**Environment**: Darwin 24.5.0

## Test Summary

- **Total Tests**: 13
- **Passed**: 12
- **Failed**: 1
- **Success Rate**: 92%

## Detailed Results

✅ Core tool: helm: PASSED - Found at /usr/local/bin/helm
✅ Core tool: kubectl: PASSED - Found at /usr/local/bin/kubectl
✅ Kind availability: PASSED - Kind tool available
✅ Minikube availability: PASSED - Minikube tool available
❌ EKS tools availability: FAILED - AWS CLI or eksctl not found
✅ Helm repo add: PASSED - Command executed successfully
✅ Helm repo update: PASSED - Command executed successfully
✅ Chart search: PASSED - Command executed successfully
✅ Chart inspection: PASSED - Command executed successfully
✅ Template rendering: PASSED - Command executed successfully
✅ Enhanced deployment test: PASSED - All available deployment tests completed successfully
✅ Helm operations coverage: PASSED - All Helm operations tested in deployment scripts
✅ Sidecar functionality coverage: PASSED - All sidecar functions tested in deployment scripts

## Environment Information

### Tools Available
- /usr/local/bin/helm
- /usr/local/bin/kubectl
- /usr/local/bin/kind
- /usr/local/bin/minikube

### System Information
- OS: Darwin
- Architecture: x86_64
- Date: Wed Jul  9 19:27:35 PDT 2025

## Conclusion

⚠️ **MOSTLY PASSED** - Minor issues detected, review failed tests
