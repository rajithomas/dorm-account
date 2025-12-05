"""
FastMCP HTTP server for Banking Simulator tools.
Exposes the same four banking tools via FastMCP on port 8300.
"""

import json
from fastmcp.server import FastMCP
from mcp.types import TextContent
from mcp_server import BankingAnalyzer


app = FastMCP(name="banking-simulator-fastmcp")


@app.tool(description="Find accounts with no transactions for N days (default: 180).")
async def get_dormant_accounts_tool(days_inactive: int = 180) -> list[TextContent]:
    result = BankingAnalyzer.get_dormant_accounts(days_inactive)
    return [TextContent(json.dumps(result, indent=2))]


@app.tool(description="Find dormant accounts with at least one large transaction in the past.")
async def get_dormant_with_large_transactions_tool(days_inactive: int = 180, threshold_amount: float = 1000) -> list[TextContent]:
    result = BankingAnalyzer.get_dormant_with_large_transactions(days_inactive, threshold_amount)
    return [TextContent(json.dumps(result, indent=2))]


@app.tool(description="Find accounts with salary/deposit transactions above a threshold.")
async def get_accounts_with_salary_deposits_tool(threshold_amount: float = 500) -> list[TextContent]:
    result = BankingAnalyzer.get_accounts_with_salary_deposits(threshold_amount)
    return [TextContent(json.dumps(result, indent=2))]


@app.tool(description="Find accounts with balance above a threshold, sorted by balance descending.")
async def get_accounts_with_high_balance_tool(threshold_amount: float = 100000) -> list[TextContent]:
    result = BankingAnalyzer.get_accounts_with_high_balance(threshold_amount)
    return [TextContent(json.dumps(result, indent=2))]


if __name__ == "__main__":
    # Run as HTTP/streamable endpoint on port 8300
    app.run(transport="streamable-http", host="0.0.0.0", port=8300)
