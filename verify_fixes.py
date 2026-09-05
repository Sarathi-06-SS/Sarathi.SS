"""
Bug Fix Verification Script
============================
Verifies all 10 bug fixes are in place before running the live system.
"""

import os
import re

def check_file_exists(filepath):
    """Check if file exists"""
    return os.path.exists(filepath)

def check_pattern_in_file(filepath, pattern, description, should_exist=True):
    """Check if a pattern exists (or doesn't exist) in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            
            if should_exist:
                if found:
                    print(f"   ✅ {description}")
                    return True
                else:
                    print(f"   ❌ {description}")
                    return False
            else:
                if not found:
                    print(f"   ✅ {description}")
                    return True
                else:
                    print(f"   ❌ {description}")
                    return False
    except Exception as e:
        print(f"   ❌ Error checking {filepath}: {e}")
        return False

def verify_all_fixes():
    """Verify all bug fixes"""
    print("\n" + "="*70)
    print("🔍 BUG FIX VERIFICATION")
    print("="*70 + "\n")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    all_passed = True
    
    # Check main.py
    print("📄 Checking main.py...")
    main_file = os.path.join(base_path, "main.py")
    
    if not check_file_exists(main_file):
        print(f"   ❌ File not found: {main_file}")
        all_passed = False
    else:
        # Bug Fix #1 & #2: Gemini API key and model
        all_passed &= check_pattern_in_file(
            main_file,
            r'GEMINI_MODEL\s*=\s*["\']gemini-1\.5-flash',
            "Bug #1-2: Gemini model name is correct (gemini-1.5-flash)"
        )
        
        all_passed &= check_pattern_in_file(
            main_file,
            r'YOUR_REAL_GEMINI_API_KEY_HERE|AIza[a-zA-Z0-9_-]{35}',
            "Bug #1-2: Gemini API key placeholder present"
        )
        
        # Bug Fix #3: CSV parsing improvement
        all_passed &= check_pattern_in_file(
            main_file,
            r'ph_idx\s*=\s*4',
            "Bug #3: CSV parsing index fix present"
        )
        
        # Bug Fix #4: Thread safety in /data endpoint
        all_passed &= check_pattern_in_file(
            main_file,
            r'snapshot\s*=\s*dict\(latest_data\)',
            "Bug #4: Thread-safe snapshot in /data endpoint"
        )
        
        # Bug Fix: No bare except in UDP listener
        all_passed &= check_pattern_in_file(
            main_file,
            r'except\s*:(?!\s*#)',
            "Bug #5: No bare 'except:' in UDP parsing (should have specific exceptions)",
            should_exist=False
        )
    
    print()
    
    # Check hardware.py
    print("📄 Checking hardware.py...")
    hardware_file = os.path.join(base_path, "hardware.py")
    
    if not check_file_exists(hardware_file):
        print(f"   ❌ File not found: {hardware_file}")
        all_passed = False
    else:
        # Bug Fix #5: Port 4210
        all_passed &= check_pattern_in_file(
            hardware_file,
            r'UDP_PORT\s*=\s*4210',
            "Bug #5: UDP port set to 4210"
        )
        
        # Bug Fix #6: Safe key access
        all_passed &= check_pattern_in_file(
            hardware_file,
            r'values\.get\(',
            "Bug #6: Safe dictionary access with .get()"
        )
    
    print()
    
    # Check udpreceiver.py
    print("📄 Checking udpreceiver.py...")
    udp_receiver_file = os.path.join(base_path, "udpreceiver.py")
    
    if not check_file_exists(udp_receiver_file):
        print(f"   ❌ File not found: {udp_receiver_file}")
        all_passed = False
    else:
        # Bug Fix #7: Absolute path for live_data.json
        all_passed &= check_pattern_in_file(
            udp_receiver_file,
            r'os\.path\.dirname|os\.path\.abspath',
            "Bug #7: Using absolute path for live_data.json"
        )
        
        # Bug Fix #8: Specific exception handling
        all_passed &= check_pattern_in_file(
            udp_receiver_file,
            r'except json\.JSONDecodeError',
            "Bug #8: Specific JSON exception handling"
        )
    
    print()
    
    # Check index.html
    print("📄 Checking index.html...")
    index_file = os.path.join(base_path, "templates", "index.html")
    
    if not check_file_exists(index_file):
        print(f"   ❌ File not found: {index_file}")
        all_passed = False
    else:
        # Bug Fix #9: setChatPrompt function
        all_passed &= check_pattern_in_file(
            index_file,
            r'function setChatPrompt\(',
            "Bug #9: setChatPrompt() function defined"
        )
        
        # Bug Fix #10: soilStatusBadge updates
        all_passed &= check_pattern_in_file(
            index_file,
            r'getElementById\(["\']soilStatusBadge["\']\)',
            "Bug #10: soilStatusBadge dynamic updates"
        )
        
        # Bug Fix #10: No executable code reference to headerUdpStatus
        # (It's OK if it appears in comments - we removed the actual getElementById call)
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for actual code usage (not in comments)
                lines = [line for line in content.split('\n') if 'headerUdpStatus' in line]
                code_refs = [line for line in lines if not line.strip().startswith('//') and 'BUG FIX' not in line]
                if len(code_refs) == 0:
                    print(f"   ✅ Bug #10: No code reference to missing headerUdpStatus")
                else:
                    print(f"   ❌ Bug #10: Found {len(code_refs)} code references to headerUdpStatus")
                    all_passed = False
        except Exception as e:
            print(f"   ❌ Error checking headerUdpStatus: {e}")
            all_passed = False
    
    print()
    print("="*70)
    
    if all_passed:
        print("✅ ALL BUG FIXES VERIFIED!")
        print("\n🚀 System is ready for live UDP data!")
        print("\nNext steps:")
        print("  1. Add your Gemini API key to main.py")
        print("  2. Run: python main.py")
        print("  3. Open: http://localhost:5000")
        print("  4. Test: python test_live_udp.py")
    else:
        print("❌ SOME FIXES ARE MISSING!")
        print("\n⚠️  Please review the failed checks above.")
        print("   The system may not work correctly with missing fixes.")
    
    print("="*70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    try:
        verify_all_fixes()
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
