#!/usr/bin/env python3
"""
Flask server with SSE (Server-Sent Events) for the Banking Simulator.

Provides:
- REST API endpoints for banking operations
- SSE endpoint for real-time event streaming
- Web interface to monitor events
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import json
import uuid
import time
from datetime import datetime, timezone
from threading import Thread, Lock
from collections import deque
from typing import Dict, Any, List

from banking_datastore import BankingDataStore
from mcp_server import BankingAnalyzer

app = Flask(__name__)
CORS(app)

# Event stream management
event_queue = deque(maxlen=100)  # Keep last 100 events
event_lock = Lock()
clients = set()


def generate_event(event_type: str, data: Dict[str, Any]) -> str:
    """Generate SSE formatted event."""
    event = {
        'id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'type': event_type,
        'data': data
    }
    with event_lock:
        event_queue.append(event)
    return f"data: {json.dumps(event)}\n\n"


@app.route('/')
def index():
    """Serve SSE dashboard."""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Banking Simulator — Real-time Events</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: system-ui, -apple-system, Arial, sans-serif; background: #f5f5f5; }
            header { background: #0b5; color: #033; padding: 16px 20px; }
            .container { display: flex; height: calc(100vh - 56px); }
            .left { width: 40%; border-right: 1px solid #ddd; padding: 16px; overflow-y: auto; background: white; }
            .right { flex: 1; padding: 16px; overflow-y: auto; }
            .event { background: white; border: 1px solid #eee; border-radius: 4px; padding: 12px; margin-bottom: 12px; }
            .event-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
            .event-type { font-weight: 600; color: #0b5; }
            .event-time { font-size: 0.85rem; color: #999; }
            .event-data { font-size: 0.9rem; color: #555; font-family: monospace; }
            .tool-section { background: white; border: 1px solid #ddd; border-radius: 4px; padding: 12px; margin-bottom: 12px; }
            .tool-section h3 { margin-bottom: 8px; color: #0b5; }
            button { background: #0b5; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
            button:hover { background: #09a; }
            input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 8px; }
            .status { position: fixed; bottom: 16px; right: 16px; padding: 12px 16px; border-radius: 4px; font-size: 0.9rem; }
            .connected { background: #0b5; color: white; }
            .disconnected { background: #d00; color: white; }
            .tool-result { background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; padding: 8px; margin-top: 8px; max-height: 200px; overflow-y: auto; font-size: 0.85rem; }
        </style>
    </head>
    <body>
        <header>
            <strong>Banking Simulator</strong> — Real-time Event Streaming
        </header>

        <div class="container">
            <section class="left">
                <h2 style="margin-bottom: 16px;">Tools</h2>

                <div class="tool-section">
                    <h3>Dormant Accounts</h3>
                    <label>Days Inactive: <input id="dormantDays" value="180" type="number"></label>
                    <button onclick="runTool('dormant_accounts')">Run</button>
                    <div id="dormantResult" class="tool-result"></div>
                </div>

                <div class="tool-section">
                    <h3>Dormant with Large TX</h3>
                    <label>Days: <input id="dormantTxDays" value="180" type="number"></label>
                    <label>Amount: $<input id="dormantTxAmount" value="1000" type="number"></label>
                    <button onclick="runTool('dormant_with_large_tx')">Run</button>
                    <div id="dormantTxResult" class="tool-result"></div>
                </div>

                <div class="tool-section">
                    <h3>Salary Deposits</h3>
                    <label>Min Amount: $<input id="salaryMin" value="500" type="number"></label>
                    <button onclick="runTool('salary_deposits')">Run</button>
                    <div id="salaryResult" class="tool-result"></div>
                </div>

                <div class="tool-section">
                    <h3>High Balance</h3>
                    <label>Min Balance: $<input id="balanceMin" value="100000" type="number"></label>
                    <button onclick="runTool('high_balance')">Run</button>
                    <div id="balanceResult" class="tool-result"></div>
                </div>
            </section>

            <section class="right">
                <h2 style="margin-bottom: 16px;">Real-time Events</h2>
                <div id="events" style="display: flex; flex-direction: column-reverse;"></div>
            </section>
        </div>

        <div id="status" class="status disconnected">● Disconnected</div>

        <script>
            let eventSource;
            let eventCount = 0;

            function connectSSE() {
                eventSource = new EventSource('/sse');
                document.getElementById('status').textContent = '● Connected';
                document.getElementById('status').className = 'status connected';

                eventSource.onmessage = function(event) {
                    const msg = JSON.parse(event.data);
                    eventCount++;
                    const eventDiv = document.createElement('div');
                    eventDiv.className = 'event';
                    eventDiv.innerHTML = `
                        <div class="event-header">
                            <span class="event-type">${msg.type}</span>
                            <span class="event-time">${new Date(msg.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div class="event-data">${JSON.stringify(msg.data, null, 2)}</div>
                    `;
                    const eventsDiv = document.getElementById('events');
                    eventsDiv.insertBefore(eventDiv, eventsDiv.firstChild);
                    // Keep only last 50 events visible
                    while (eventsDiv.children.length > 50) {
                        eventsDiv.removeChild(eventsDiv.lastChild);
                    }
                };

                eventSource.onerror = function() {
                    document.getElementById('status').textContent = '● Disconnected';
                    document.getElementById('status').className = 'status disconnected';
                    eventSource.close();
                    setTimeout(connectSSE, 3000);
                };
            }

            async function runTool(tool) {
                const params = {};
                let resultDiv;

                switch(tool) {
                    case 'dormant_accounts':
                        params.days = parseInt(document.getElementById('dormantDays').value) || 180;
                        resultDiv = document.getElementById('dormantResult');
                        break;
                    case 'dormant_with_large_tx':
                        params.days = parseInt(document.getElementById('dormantTxDays').value) || 180;
                        params.amount = parseFloat(document.getElementById('dormantTxAmount').value) || 1000;
                        resultDiv = document.getElementById('dormantTxResult');
                        break;
                    case 'salary_deposits':
                        params.min_amount = parseFloat(document.getElementById('salaryMin').value) || 500;
                        resultDiv = document.getElementById('salaryResult');
                        break;
                    case 'high_balance':
                        params.min_balance = parseFloat(document.getElementById('balanceMin').value) || 100000;
                        resultDiv = document.getElementById('balanceResult');
                        break;
                }

                try {
                    resultDiv.textContent = 'Loading...';
                    const res = await fetch(`/api/tool/${tool}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(params)
                    });
                    const data = await res.json();
                    resultDiv.textContent = `Found ${data.count} results: ${data.summary}`;
                } catch (err) {
                    resultDiv.textContent = `Error: ${err.message}`;
                }
            }

            // Connect on load
            connectSSE();

            // Simulate some events for demo
            setTimeout(() => {
                fetch('/api/simulate-event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ event_type: 'welcome', message: 'Connected to Banking Simulator SSE' })
                });
            }, 500);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)


@app.route('/sse')
def sse():
    """SSE endpoint for streaming events."""
    def event_stream():
        # Send any buffered events first
        with event_lock:
            for event in event_queue:
                yield f"data: {json.dumps(event)}\n\n"
        
        # Keep connection open and stream new events
        last_sent = len(event_queue)
        while True:
            with event_lock:
                if len(event_queue) > last_sent:
                    for event in list(event_queue)[last_sent:]:
                        yield f"data: {json.dumps(event)}\n\n"
                    last_sent = len(event_queue)
            time.sleep(0.5)

    return app.response_class(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )


@app.route('/api/tool/<tool_name>', methods=['POST'])
def run_tool(tool_name: str):
    """API endpoint to run banking analysis tools."""
    data = request.get_json() or {}
    
    try:
        if tool_name == 'dormant_accounts':
            days = data.get('days', 180)
            result = BankingAnalyzer.get_dormant_accounts(days_inactive=days)
            generate_event('tool_executed', {
                'tool': tool_name,
                'params': {'days': days},
                'count': len(result),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return jsonify({
                'tool': tool_name,
                'count': len(result),
                'summary': f'{len(result)} dormant accounts (>{days} days)',
                'data': result[:5]  # Return top 5
            })

        elif tool_name == 'dormant_with_large_tx':
            days = data.get('days', 180)
            amount = data.get('amount', 1000)
            result = BankingAnalyzer.get_dormant_with_large_transactions(
                days_inactive=days, threshold_amount=amount)
            generate_event('tool_executed', {
                'tool': tool_name,
                'params': {'days': days, 'amount': amount},
                'count': len(result)
            })
            return jsonify({
                'tool': tool_name,
                'count': len(result),
                'summary': f'{len(result)} dormant accounts with past transactions > ${amount}',
                'data': result[:5]
            })

        elif tool_name == 'salary_deposits':
            min_amt = data.get('min_amount', 500)
            result = BankingAnalyzer.get_accounts_with_salary_deposits(min_amount=min_amt)
            generate_event('tool_executed', {
                'tool': tool_name,
                'params': {'min_amount': min_amt},
                'count': len(result)
            })
            return jsonify({
                'tool': tool_name,
                'count': len(result),
                'summary': f'{len(result)} accounts with salary deposits > ${min_amt}',
                'data': result[:5]
            })

        elif tool_name == 'high_balance':
            min_bal = data.get('min_balance', 100000)
            result = BankingAnalyzer.get_accounts_with_high_balance(min_balance=min_bal)
            generate_event('tool_executed', {
                'tool': tool_name,
                'params': {'min_balance': min_bal},
                'count': len(result),
                'total_balance': sum(acc['balance'] for acc in result)
            })
            return jsonify({
                'tool': tool_name,
                'count': len(result),
                'summary': f'{len(result)} accounts with balance > ${min_bal:,.0f}',
                'data': result[:5]
            })

        else:
            return jsonify({'error': f'Unknown tool: {tool_name}'}), 400

    except Exception as e:
        generate_event('error', {'tool': tool_name, 'error': str(e)})
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulate-event', methods=['POST'])
def simulate_event():
    """Simulate an event (for testing)."""
    data = request.get_json() or {}
    generate_event(data.get('event_type', 'test'), data.get('message', {}))
    return jsonify({'status': 'ok'})


@app.route('/api/stats')
def stats():
    """Get event statistics."""
    with event_lock:
        event_types = {}
        for event in event_queue:
            t = event.get('type', 'unknown')
            event_types[t] = event_types.get(t, 0) + 1
    
    return jsonify({
        'total_events': len(event_queue),
        'event_types': event_types,
        'queue_size': len(event_queue),
        'max_queue_size': event_queue.maxlen
    })


if __name__ == '__main__':
    print("Starting Banking Simulator SSE Server...")
    print("Open: http://localhost:5010")
    print("SSE Endpoint: http://localhost:5010/sse")
    print("API Stats: http://localhost:5010/api/stats")
    app.run(debug=False, host='0.0.0.0', port=5010, threaded=True)
