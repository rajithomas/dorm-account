#!/usr/bin/env python3
"""
MCP Server for Banking Simulator.

Implements the Model Context Protocol (MCP) with four banking analysis tools.
Can be used with Claude or other MCP-compatible clients.

Usage:
  python3 mcp_server_mcp.py
  
Configure in Claude/MCP client settings to use this server.
"""

import json
import sys
from typing import Any, Dict, List
import asyncio

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

import mcp.types as types

from banking_datastore import BankingDataStore
from mcp_server import BankingAnalyzer


# Create MCP server
server = Server("banking-simulator")


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute a banking analysis tool."""
    
    if name == "get_dormant_accounts":
        days = arguments.get("days_inactive", 180)
        result = BankingAnalyzer.get_dormant_accounts(days_inactive=days)
        summary = f"Found {len(result)} dormant accounts (inactive for >{days} days)"
        return [TextContent(
            type="text",
            text=json.dumps({
                "summary": summary,
                "count": len(result),
                "accounts": result[:10]  # Return top 10
            }, indent=2)
        )]

    elif name == "get_dormant_with_large_transactions":
        days = arguments.get("days_inactive", 180)
        amount = arguments.get("threshold_amount", 1000.0)
        result = BankingAnalyzer.get_dormant_with_large_transactions(
            days_inactive=days, threshold_amount=amount)
        summary = f"Found {len(result)} dormant accounts with past transactions > ${amount}"
        return [TextContent(
            type="text",
            text=json.dumps({
                "summary": summary,
                "count": len(result),
                "accounts": result[:10]
            }, indent=2)
        )]

    elif name == "get_accounts_with_salary_deposits":
        min_amount = arguments.get("min_amount", 500.0)
        result = BankingAnalyzer.get_accounts_with_salary_deposits(min_amount=min_amount)
        summary = f"Found {len(result)} accounts with salary deposits > ${min_amount}"
        return [TextContent(
            type="text",
            text=json.dumps({
                "summary": summary,
                "count": len(result),
                "accounts": result[:10]
            }, indent=2)
        )]

    elif name == "get_accounts_with_high_balance":
        min_balance = arguments.get("min_balance", 100000.0)
        result = BankingAnalyzer.get_accounts_with_high_balance(min_balance=min_balance)
        total = sum(acc["balance"] for acc in result)
        summary = f"Found {len(result)} accounts with balance > ${min_balance:,.0f} (total: ${total:,.0f})"
        return [TextContent(
            type="text",
            text=json.dumps({
                "summary": summary,
                "count": len(result),
                "total_balance": total,
                "accounts": result[:10]
            }, indent=2)
        )]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


def setup_tools():
    """Register all banking analysis tools using the list_tools decorator."""
    
    @server.list_tools()
    async def list_tools_handler():
        """List available banking analysis tools."""
        return [
            Tool(
                name="get_dormant_accounts",
                description="Find accounts that are dormant (no transactions for N days)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days_inactive": {
                            "type": "integer",
                            "description": "Number of days of inactivity to consider dormant (default: 180)",
                            "default": 180
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_dormant_with_large_transactions",
                description="Find dormant accounts that had large transactions in the past",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days_inactive": {
                            "type": "integer",
                            "description": "Days of inactivity threshold (default: 180)",
                            "default": 180
                        },
                        "threshold_amount": {
                            "type": "number",
                            "description": "Minimum transaction amount in dollars (default: 1000)",
                            "default": 1000.0
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_accounts_with_salary_deposits",
                description="Find accounts with salary/deposit transactions above a threshold",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "min_amount": {
                            "type": "number",
                            "description": "Minimum deposit amount in dollars (default: 500)",
                            "default": 500.0
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_accounts_with_high_balance",
                description="Find accounts with balance above a threshold",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "min_balance": {
                            "type": "number",
                            "description": "Minimum balance in dollars (default: 100000)",
                            "default": 100000.0
                        }
                    },
                    "required": []
                }
            )
        ]


async def main():
    """Run the MCP server."""
    setup_tools()
    
    print(f"[Banking Simulator MCP Server started]", file=sys.stderr)
    print(f"Tools available:", file=sys.stderr)
    for tool in [
        "get_dormant_accounts",
        "get_dormant_with_large_transactions", 
        "get_accounts_with_salary_deposits",
        "get_accounts_with_high_balance"
    ]:
        print(f"  - {tool}", file=sys.stderr)
    
    # Use stdio transport for MCP communication
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
