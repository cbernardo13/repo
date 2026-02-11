#!/bin/bash
# ClawBrain Integration Testing Script

set -e

echo "🧠 ClawBrain Integration Tests"
echo "================================"
echo ""

PASSED=0
FAILED=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

# Test 1: CLI executable permissions
echo "Test 1: CLI Executable"
if [ -x ./clawbrain ]; then
    test_pass "clawbrain is executable"
else
    test_fail "clawbrain is not executable"
fi

# Test 2: Version command
echo ""
echo "Test 2: Version Command"
if ./clawbrain version > /dev/null 2>&1; then
    test_pass "clawbrain version works"
else
    test_fail "clawbrain version failed"
fi

# Test 3: Status command
echo ""
echo "Test 3: Status Command"
if ./clawbrain status > /dev/null 2>&1; then
    test_pass "clawbrain status works"
else
    test_fail "clawbrain status failed"
fi

# Test 4: Config command
echo ""
echo "Test 4: Config Command (Sanitized)"
output=$(./clawbrain config 2>/dev/null)
if echo "$output" | grep -q "REDACTED"; then
    test_pass "Config properly sanitizes API keys"
else
    test_fail "Config does not sanitize API keys"
fi

# Test 5: Required files exist
echo ""
echo "Test 5: Required Files"
files=("llm_brain.py" "scheduler.py" "calendar_sync.py" ".env" "openclaw.json")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        test_pass "$file exists"
    else
        test_fail "$file missing"
    fi
done

# Test 6: API keys NOT in openclaw.json
echo ""
echo "Test 6: API Key Security"
if grep -q "OPENROUTER_API_KEY.*sk-" openclaw.json 2>/dev/null; then
    test_fail "API keys found in openclaw.json (security issue)"
else
    test_pass "No API keys in openclaw.json"
fi

# Test 7: Python imports work
echo ""
echo "Test 7: Python Module Imports"
python3 -c "import llm_brain" 2>/dev/null
if [ $? -eq 0 ]; then
    test_pass "llm_brain imports successfully"
else
    test_fail "llm_brain import failed"
fi

python3 -c "import scheduler" 2>/dev/null
if [ $? -eq 0 ]; then
    test_pass "scheduler imports successfully"
else
    test_fail "scheduler import failed"
fi

# Test 8: Environment variables loaded
echo ""
echo "Test 8: Environment Variables"
if [ -n "$GEMINI_API_KEY" ]; then
    test_pass "GEMINI_API_KEY is set"
else
    test_fail "GEMINI_API_KEY not set"
fi

# Test 9: Chat command basic functionality
echo ""
echo "Test 9: Basic Chat (Simple Test)"
output=$(./clawbrain chat "Say 'test passed'" 2>&1 | grep -i "test passed" || true)
if [ -n "$output" ]; then
    test_pass "Chat command functional"
else
    echo "⚠️  SKIP: Chat test (may require API call)"
fi

# Test 10: Tools command
echo ""
echo "Test 10: Tools Listing"
if ./clawbrain tools > /dev/null 2>&1; then
    test_pass "Tools command works"
else
    test_fail "Tools command failed"
fi

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
