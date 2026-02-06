#!/usr/bin/env python3
# ============================================================================
# run_all_tests.py - Unified Test Runner
# ============================================================================
"""
Run all tests for the Pet Triage AI Backend

This script runs tests for:
1. shared/ module (constants, schemas, red_flags, prompts, errors)
2. Core modules (config, llm_setup, prompts, input_guardrails, output_guardrails)
3. Integration tests

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --shared     # Run only shared module tests
    python tests/run_all_tests.py --core       # Run only core module tests
    python tests/run_all_tests.py --quick      # Run quick tests (no API calls)
"""

import sys
import os
import time
import traceback
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Test Result Tracking
# ============================================================================

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.start_time = None
        self.end_time = None
    
    def add_passed(self, name: str):
        self.passed.append(name)
    
    def add_failed(self, name: str, error: str):
        self.failed.append((name, error))
    
    def add_skipped(self, name: str, reason: str):
        self.skipped.append((name, reason))
    
    def summary(self) -> str:
        duration = self.end_time - self.start_time if self.end_time else 0
        lines = [
            "",
            "=" * 60,
            "TEST RESULTS SUMMARY",
            "=" * 60,
            f"Total tests: {len(self.passed) + len(self.failed) + len(self.skipped)}",
            f"  [PASS] Passed:  {len(self.passed)}",
            f"  [FAIL] Failed:  {len(self.failed)}",
            f"  [SKIP] Skipped: {len(self.skipped)}",
            f"Duration: {duration:.2f} seconds",
            "=" * 60,
        ]
        
        if self.failed:
            lines.append("\nFAILED TESTS:")
            for name, error in self.failed:
                lines.append(f"  [FAIL] {name}")
                lines.append(f"     Error: {error[:100]}...")
        
        if self.skipped:
            lines.append("\nSKIPPED TESTS:")
            for name, reason in self.skipped:
                lines.append(f"  [SKIP] {name}: {reason}")
        
        return "\n".join(lines)


results = TestResults()


# ============================================================================
# Test Runners
# ============================================================================

def run_test_module(module_name: str, test_func_name: str = "run_all_tests"):
    """Run a test module and track results"""
    print(f"\n{'='*60}")
    print(f"Running: {module_name}")
    print("="*60)
    
    try:
        module = __import__(module_name)
        test_func = getattr(module, test_func_name, None)
        
        if test_func:
            test_func()
            results.add_passed(module_name)
        else:
            results.add_skipped(module_name, f"No {test_func_name} function found")
            
    except ImportError as e:
        results.add_failed(module_name, f"Import error: {str(e)}")
        traceback.print_exc()
    except AssertionError as e:
        results.add_failed(module_name, f"Assertion failed: {str(e)}")
        traceback.print_exc()
    except Exception as e:
        results.add_failed(module_name, f"Error: {str(e)}")
        traceback.print_exc()


# ============================================================================
# Test Suites
# ============================================================================

def run_shared_module_tests():
    """Run all shared module tests"""
    print("\n" + "=" * 60)
    print("SHARED MODULE TESTS")
    print("=" * 60)
    
    # Change to tests directory for imports
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    run_test_module("test_shared_constants")
    run_test_module("test_shared_red_flags")
    run_test_module("test_shared_schemas")
    run_test_module("test_shared_prompts")
    run_test_module("test_shared_errors")


def run_core_module_tests():
    """Run all core module tests"""
    print("\n" + "=" * 60)
    print("CORE MODULE TESTS")
    print("=" * 60)
    
    # Change to tests directory for imports
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test config (should re-export from shared)
    try:
        print("\n--- Testing config.py imports ---")
        from config import SUPPORTED_SPECIES, SUPPORTED_CATEGORIES, MODEL_CONFIG
        assert len(SUPPORTED_SPECIES) == 2
        assert len(SUPPORTED_CATEGORIES) == 9
        print("  ✓ config.py imports work correctly")
        results.add_passed("config_imports")
    except Exception as e:
        results.add_failed("config_imports", str(e))
        traceback.print_exc()
    
    # Test prompts.py
    try:
        print("\n--- Testing prompts.py ---")
        from prompts import get_triage_system_prompt, build_triage_message
        prompt = get_triage_system_prompt()
        assert prompt is not None and len(prompt) > 100
        print("  ✓ prompts.py works correctly")
        results.add_passed("prompts_module")
    except Exception as e:
        results.add_failed("prompts_module", str(e))
        traceback.print_exc()
    
    # Test input_guardrails.py
    run_test_module("test_input_guardrails", "test_input_guardrails")
    
    # Test output_guardrails.py
    run_test_module("test_output_guardrails", "test_output_guardrails")


def run_llm_setup_tests(skip_api: bool = True):
    """Run LLM setup tests"""
    print("\n" + "=" * 60)
    print("LLM SETUP TESTS")
    print("=" * 60)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test ER rules (no API needed)
    run_test_module("test_llm_setup", "test_er_rules")
    run_test_module("test_llm_setup", "test_model_selection")
    
    if not skip_api:
        run_test_module("test_llm_setup", "test_api_connection")


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "=" * 60)
    print("INTEGRATION TESTS")
    print("=" * 60)
    
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        # Test that all modules can be imported together
        print("\n--- Testing module integration ---")
        
        from shared.constants import RiskLevel, SymptomCategory
        from shared.red_flags import check_immediate_er
        from shared.schemas import TriageResponse, get_fallback_response
        from config import SUPPORTED_SPECIES
        from llm_setup import get_er_template, select_model
        from input_guardrails import InputGuardrails
        from output_guardrails import OutputGuardrails
        
        print("  ✓ All modules imported successfully")
        
        # Test end-to-end flow (no API)
        print("\n--- Testing end-to-end flow (no API) ---")
        
        guardrails = InputGuardrails()
        
        # Test ER detection
        result = guardrails.validate_all(
            species="cat",
            category="Urinary & Genital",
            structured_fields={
                "sex": "male",
                "straining_no_urine": "Yes",
                "hours_since_urination": "12+"
            },
            user_description="My cat can't pee"
        )
        
        assert result["is_er"] == True, "Should detect ER case"
        print("  ✓ ER detection works")
        
        # Test normal case
        result = guardrails.validate_all(
            species="dog",
            category="Stomach Upset",
            structured_fields={"vomiting_frequency": "once"},
            user_description="My dog vomited once"
        )
        
        assert result["passed"] == True
        assert result["is_er"] == False
        print("  ✓ Normal case validation works")
        
        # Test output guardrails
        output_guardrails = OutputGuardrails()
        fallback = output_guardrails.get_fallback("Test error")
        assert "risk_level" in fallback
        assert "disclaimer" in fallback
        print("  ✓ Output guardrails work")
        
        results.add_passed("integration_tests")
        
    except Exception as e:
        results.add_failed("integration_tests", str(e))
        traceback.print_exc()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main test runner"""
    results.start_time = time.time()
    
    print("=" * 60)
    print("PET TRIAGE AI BACKEND - UNIFIED TEST SUITE")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    run_shared = "--shared" in args or not args or "--all" in args
    run_core = "--core" in args or not args or "--all" in args
    run_integration = "--integration" in args or not args or "--all" in args
    skip_api = "--quick" in args or "--no-api" in args or True  # Default skip API
    
    # Run test suites
    if run_shared:
        run_shared_module_tests()
    
    if run_core:
        run_core_module_tests()
        run_llm_setup_tests(skip_api=skip_api)
    
    if run_integration:
        run_integration_tests()
    
    # Print summary
    results.end_time = time.time()
    print(results.summary())
    
    # Return exit code
    return 0 if not results.failed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
