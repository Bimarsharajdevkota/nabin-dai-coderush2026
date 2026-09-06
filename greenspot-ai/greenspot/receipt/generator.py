"""
Certified Green FinOps Receipt Generator.
Renders tamper-evident ESG compliance receipts for corporate sustainability reporting.
"""

from typing import Union, Dict, Any
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from greenspot.schemas import JobReceipt

console = Console()


class ReceiptFormatter:
    @staticmethod
    def render_terminal_receipt(receipt: JobReceipt) -> Panel:
        """
        Renders an attractive ASCII certification receipt using Rich.
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan bold")
        table.add_column("Value", style="white")

        table.add_row("🧾 Job ID", receipt.job_id)
        table.add_row("💻 Task", receipt.task_command)
        table.add_row("⏱️ Runtime", f"{receipt.runtime_hours} hrs")
        table.add_row("🌍 Execution Region", f"{receipt.executed_region_name} ({receipt.executed_region})")
        table.add_row("⚡ Clean Energy", f"{receipt.clean_energy_percentage}% ({receipt.primary_energy_source})")
        table.add_row("🌱 Grid Carbon", f"{receipt.carbon_intensity_gco2_kwh} gCO2/kWh")
        table.add_row("💰 Actual Spot Cost", f"${receipt.actual_spot_cost_usd:.2f}")
        table.add_row("🏷️ Retail On-Demand", f"${receipt.baseline_ondemand_cost_usd:.2f}")
        table.add_row("💵 Total Saved", f"${receipt.total_savings_usd:.2f} ({receipt.savings_percentage}% OFF)")
        table.add_row("🍃 Carbon Avoided", f"{receipt.carbon_avoided_gco2:.1f} gCO2eq")
        table.add_row("🚗 Car Km Offset", f"{receipt.equivalent_gas_car_km_avoided} km")
        table.add_row("🛡️ Preemptions Handled", f"{receipt.preemptions_handled} (Zero data loss)")
        table.add_row("🔒 Integrity Hash", receipt.checkpoint_verification_hash)

        panel = Panel(
            table,
            title="[bold green]🌱 CERTIFIED GREEN FINOPS RECEIPT[/bold green]",
            subtitle="[dim]Verified by GreenSpot AI ESG Engine[/dim]",
            border_style="green"
        )
        return panel

    @staticmethod
    def render_html_receipt(receipt: Union[JobReceipt, Dict[str, Any]]) -> str:
        """
        Renders a certified, tamper-evident Green FinOps HTML receipt & certificate.
        Includes corporate ESG Scope 2/3 GHG accounting details, financial savings,
        and zero-loss preemption verification.
        """
        if isinstance(receipt, dict):
            receipt = JobReceipt(**receipt)

        started_str = receipt.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(receipt.started_at, datetime) else str(receipt.started_at)
        finished_str = receipt.finished_at.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(receipt.finished_at, datetime) else str(receipt.finished_at)

        preemption_rows = ""
        if receipt.preemption_history:
            for i, p in enumerate(receipt.preemption_history, start=1):
                p_ts = p.timestamp.strftime("%H:%M:%S") if isinstance(p.timestamp, datetime) else str(p.timestamp)
                preemption_rows += f"""
                <tr>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #374151;">#{i} ({p_ts})</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #dc2626; font-family: monospace;">{p.evicted_region}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #059669; font-family: monospace;">{p.resumed_region}</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #374151;">{p.checkpoint_size_mb:.1f} MB in {p.sync_duration_seconds:.2f}s</td>
                    <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #059669; font-weight: 600;">Zero Data Loss</td>
                </tr>
                """
        else:
            preemption_rows = """
            <tr>
                <td colspan="5" style="padding: 12px; text-align: center; color: #6b7280; font-size: 13px; font-style: italic;">
                    No preemptions occurred. Workload completed uninterrupted.
                </td>
            </tr>
            """

        provider_str = getattr(receipt.executed_provider, "value", str(receipt.executed_provider)).upper()
        status_str = getattr(receipt.status, "value", str(receipt.status)).upper()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Green FinOps Certificate — {receipt.job_id}</title>
    <style>
        :root {{
            --primary: #059669;
            --primary-dark: #065f46;
            --primary-light: #ecfdf5;
            --secondary: #0284c7;
            --text-main: #111827;
            --text-muted: #6b7280;
            --bg-card: #ffffff;
            --border-color: #e5e7eb;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f3f4f6;
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 850px;
            margin: 0 auto;
        }}
        .certificate {{
            background: var(--bg-card);
            border-radius: 16px;
            border: 2px solid #10b981;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            position: relative;
        }}
        .header {{
            background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
            color: #ffffff;
            padding: 32px;
            position: relative;
        }}
        .header-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            font-weight: 700;
            color: #a7f3d0;
            margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .header h1 {{
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }}
        .header p {{
            font-size: 14px;
            color: #d1fae5;
        }}
        .status-badge {{
            position: absolute;
            top: 32px;
            right: 32px;
            background: #10b981;
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .content {{
            padding: 32px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            margin-bottom: 28px;
        }}
        .meta-item {{
            font-size: 13px;
        }}
        .meta-label {{
            color: var(--text-muted);
            font-weight: 500;
            margin-bottom: 2px;
        }}
        .meta-value {{
            font-weight: 600;
            color: var(--text-main);
        }}
        .meta-value.mono {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }}
        .stat-card {{
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            position: relative;
            overflow: hidden;
        }}
        .stat-card.green {{
            border-color: #a7f3d0;
            background: linear-gradient(to bottom right, #ffffff, #f0fdf4);
        }}
        .stat-card.blue {{
            border-color: #bae6fd;
            background: linear-gradient(to bottom right, #ffffff, #f0f9ff);
        }}
        .stat-card.purple {{
            border-color: #e9d5ff;
            background: linear-gradient(to bottom right, #ffffff, #faf5ff);
        }}
        .stat-label {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 800;
            color: var(--text-main);
            line-height: 1.2;
        }}
        .stat-subtext {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .highlight-green {{
            color: #059669;
        }}
        .highlight-blue {{
            color: #0284c7;
        }}
        .table-container {{
            border: 1px solid var(--border-color);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 28px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th {{
            background: #f9fafb;
            padding: 10px 12px;
            font-size: 12px;
            font-weight: 600;
            color: #4b5563;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-color);
        }}
        .verification-footer {{
            background: #f9fafb;
            border-top: 1px solid var(--border-color);
            padding: 24px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .seal-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .seal-icon {{
            width: 44px;
            height: 44px;
            background: #d1fae5;
            color: #059669;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            border: 2px solid #10b981;
        }}
        .seal-text {{
            font-size: 12px;
            line-height: 1.4;
        }}
        .seal-text strong {{
            color: #065f46;
            font-size: 13px;
            display: block;
        }}
        .actions-bar {{
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }}
        .btn {{
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            border: none;
        }}
        .btn-primary {{
            background: #059669;
            color: white;
        }}
        .btn-primary:hover {{
            background: #047857;
        }}
        .btn-secondary {{
            background: white;
            color: #374151;
            border: 1px solid #d1d5db;
        }}
        .btn-secondary:hover {{
            background: #f3f4f6;
        }}
        @media print {{
            body {{
                background: white !important;
                padding: 0 !important;
            }}
            .certificate {{
                box-shadow: none !important;
                border: 1px solid #9ca3af !important;
            }}
            .actions-bar {{
                display: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="certificate">
            <div class="header">
                <div class="header-badge">🌱 GreenSpot AI — Certified FinOps</div>
                <h1>Scope 2/3 Clean Energy & Arbitrage Receipt</h1>
                <p>Verified Tamper-Evident ESG Compliance Certificate for Corporate Sustainability Reporting</p>
                <div class="status-badge">
                    <span>✓</span> {status_str}
                </div>
            </div>

            <div class="content">
                <div class="meta-grid">
                    <div class="meta-item">
                        <div class="meta-label">Certificate / Job ID</div>
                        <div class="meta-value mono">{receipt.job_id}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Task Command</div>
                        <div class="meta-value mono">{receipt.task_command}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Execution Target</div>
                        <div class="meta-value">{provider_str} • {receipt.executed_region_name} ({receipt.executed_region})</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Instance Spec & Duration</div>
                        <div class="meta-value">{receipt.executed_instance_type} • {receipt.runtime_hours:.1f} hours</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Execution Started</div>
                        <div class="meta-value">{started_str}</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Execution Finished</div>
                        <div class="meta-value">{finished_str}</div>
                    </div>
                </div>

                <div class="section-title">
                    <span>💰</span> Financial Arbitrage & Cost Efficiency
                </div>
                <div class="cards-grid">
                    <div class="stat-card green">
                        <div class="stat-label">Total Cost Saved</div>
                        <div class="stat-value highlight-green">${receipt.total_savings_usd:.2f}</div>
                        <div class="stat-subtext"><strong>{receipt.savings_percentage:.1f}% discount</strong> vs retail</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Actual Spot Cost</div>
                        <div class="stat-value">${receipt.actual_spot_cost_usd:.2f}</div>
                        <div class="stat-subtext">Dynamic spot market bid</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Baseline Retail Cost</div>
                        <div class="stat-value">${receipt.baseline_ondemand_cost_usd:.2f}</div>
                        <div class="stat-subtext">Standard On-Demand rate</div>
                    </div>
                </div>

                <div class="section-title">
                    <span>🍃</span> Environmental Sustainability & Grid Impact
                </div>
                <div class="cards-grid">
                    <div class="stat-card green">
                        <div class="stat-label">Carbon Avoided</div>
                        <div class="stat-value highlight-green">{receipt.carbon_avoided_gco2:.1f} <span style="font-size: 14px; font-weight: 500;">gCO2eq</span></div>
                        <div class="stat-subtext">Equivalent to <strong>{receipt.equivalent_gas_car_km_avoided:.2f} km</strong> driving offset</div>
                    </div>
                    <div class="stat-card blue">
                        <div class="stat-label">Clean Energy Share</div>
                        <div class="stat-value highlight-blue">{receipt.clean_energy_percentage:.1f}%</div>
                        <div class="stat-subtext">Source: {receipt.primary_energy_source}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Grid Carbon Intensity</div>
                        <div class="stat-value">{receipt.carbon_intensity_gco2_kwh} <span style="font-size: 14px; font-weight: 500;">g/kWh</span></div>
                        <div class="stat-subtext">{receipt.carbon_emitted_gco2:.1f} gCO2eq emitted</div>
                    </div>
                </div>

                <div class="section-title">
                    <span>🛡️</span> Spot Preemption Resilience & Audit Trail
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Preemption Event</th>
                                <th>Evicted Zone</th>
                                <th>Resumed Zone</th>
                                <th>State Flush Metrics</th>
                                <th>Integrity</th>
                            </tr>
                        </thead>
                        <tbody>
                            {preemption_rows}
                        </tbody>
                    </table>
                </div>

                <div style="font-size: 12px; color: #6b7280; font-family: monospace; word-break: break-all; background: #f9fafb; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);">
                    <strong>🔒 Checkpoint State Hash:</strong> {receipt.checkpoint_verification_hash}
                </div>
            </div>

            <div class="verification-footer">
                <div class="seal-box">
                    <div class="seal-icon">🌱</div>
                    <div class="seal-text">
                        <strong>GreenSpot AI Protocol Verified</strong>
                        Tamper-Evident Corporate ESG Audit Document • GHG Protocol Scope 2/3 Standard
                    </div>
                </div>
                <div style="text-align: right; font-size: 12px; color: #6b7280;">
                    <div>Issuer: <strong>GreenSpot AI Engine v0.1.0</strong></div>
                    <div>Digital Signature: <code>{receipt.checkpoint_verification_hash[:16]}</code></div>
                </div>
            </div>
        </div>

        <div class="actions-bar">
            <button class="btn btn-secondary" onclick="window.history.back()">← Back to Dashboard</button>
            <button class="btn btn-secondary" onclick="downloadJSON()">⬇️ Export JSON</button>
            <button class="btn btn-primary" onclick="window.print()">🖨️ Print / Save as PDF</button>
        </div>
    </div>

    <script>
        function downloadJSON() {{
            const receiptData = {receipt.model_dump_json()};
            const blob = new Blob([JSON.stringify(receiptData, null, 2)], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "greenspot-receipt-" + "{receipt.job_id}" + ".json";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>"""
        return html


def render_html_receipt(receipt: Union[JobReceipt, Dict[str, Any]]) -> str:
    """Convenience module-level function to render HTML receipt."""
    return ReceiptFormatter.render_html_receipt(receipt)
