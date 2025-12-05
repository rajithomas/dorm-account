#!/usr/bin/env python3
"""Test all four FastMCP tools"""

import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client


async def test_tool(session, tool_name, arguments):
    """Test a single tool call"""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"Arguments: {arguments}")
    print(f"{'='*60}")
    
    try:
        result = await session.call_tool(tool_name, arguments=arguments)
        print(f"✓ Success!")
        
        # Parse and display result
        if result.content:
            for content in result.content:
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    print(f"Returned {len(data)} results")
                    if data:
                        print(f"First result: {json.dumps(data[0], indent=2)}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def main():
    # Test tools by calling the analyzer directly
    print("Testing FastMCP Banking Simulator Tools")
    print("=" * 60)
    
    from mcp_server import BankingAnalyzer
    from mcp.types import TextContent
    
    tests = [
        ("get_dormant_accounts", 180, None),
        ("get_dormant_with_large_transactions", 180, 1000),
        ("get_accounts_with_salary_deposits", 500, None),
        ("get_accounts_with_high_balance", 100000, None),
    ]
    
    passed = 0
    failed = 0
    
    for tool_name, arg1, arg2 in tests:
        print(f"\n{'='*60}")
        print(f"Testing: {tool_name}")
        if arg2 is not None:
            print(f"Arguments: {arg1}, {arg2}")
        else:
            print(f"Arguments: {arg1}")
        print(f"{'='*60}")
        
        try:
            # Call the analyzer method
            if tool_name == "get_dormant_accounts":
                result = BankingAnalyzer.get_dormant_accounts(arg1)
            elif tool_name == "get_dormant_with_large_transactions":
                result = BankingAnalyzer.get_dormant_with_large_transactions(arg1, arg2)
            elif tool_name == "get_accounts_with_salary_deposits":
                result = BankingAnalyzer.get_accounts_with_salary_deposits(arg1)
            elif tool_name == "get_accounts_with_high_balance":
                result = BankingAnalyzer.get_accounts_with_high_balance(arg1)
            
            # Verify we can serialize to JSON (what FastMCP returns)
            json_result = json.dumps(result, indent=2)
            text_content = TextContent(type="text", text=json_result)
            
            print(f"✓ Success!")
            print(f"Returned {len(result)} results")
            if result:
                print(f"First result sample:")
                print(json.dumps(result[0], indent=2))
            
            passed += 1
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
