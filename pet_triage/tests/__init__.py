# ============================================================================
# Tests Package
# ============================================================================
"""
Pet Triage AI Backend Test Suite

Test modules:
- test_shared_constants.py    - shared/constants.py tests
- test_shared_red_flags.py    - shared/red_flags.py tests
- test_shared_schemas.py      - shared/schemas.py tests
- test_shared_prompts.py      - shared/prompts.py tests
- test_shared_errors.py       - shared/errors.py tests
- test_input_guardrails.py    - input_guardrails.py tests
- test_output_guardrails.py   - output_guardrails.py tests
- test_llm_setup.py           - llm_setup.py tests
- test_prompts.py             - prompts.py tests
- run_all_tests.py            - unified test runner

Usage:
    python -m tests.run_all_tests           # Run all tests
    python tests/run_all_tests.py --shared  # Run shared module tests only
    python tests/run_all_tests.py --quick   # Run without API calls
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
