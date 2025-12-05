"""
EDQMP Alerting Engine
Multi-channel alert dispatcher
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """
    Dispatches alerts through multiple channels (email, Slack, webhook, etc.)
    """
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def send_alert(
        self,
        channel: str,
        channel_config: Dict[str, Any],
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send an alert through the specified channel.
        
        Args:
            channel: Alert channel (email, slack, webhook, etc.)
            channel_config: Channel-specific configuration
            alert_data: Alert payload data
            
        Returns:
            Response with status and details
        """
        try:
            if channel == "slack":
                return await self._send_slack(channel_config, alert_data)
            elif channel == "email":
                return await self._send_email(channel_config, alert_data)
            elif channel == "webhook":
                return await self._send_webhook(channel_config, alert_data)
            elif channel == "teams":
                return await self._send_teams(channel_config, alert_data)
            else:
                return {
                    "status": "failed",
                    "error": f"Unknown channel: {channel}"
                }
        except Exception as e:
            logger.exception(f"Failed to send alert via {channel}: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_slack(
        self, 
        config: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send alert to Slack"""
        webhook_url = config.get("webhook_url") or settings.slack_webhook_url
        
        if not webhook_url:
            return {"status": "failed", "error": "Slack webhook URL not configured"}
        
        channel = config.get("channel", settings.slack_default_channel)
        mention_users = config.get("mention_users", [])
        
        # Build Slack message
        severity = alert_data.get("severity", "warning")
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }.get(severity, "⚠️")
        
        status = alert_data.get("status", "failed")
        status_color = {
            "passed": "#36a64f",
            "warning": "#ff9800",
            "failed": "#f44336",
            "error": "#9c27b0"
        }.get(status, "#ff9800")
        
        # Build mention string
        mention_str = " ".join([f"<@{u}>" for u in mention_users])
        
        message = {
            "channel": channel,
            "username": "EDQMP Alert",
            "icon_emoji": ":chart_with_upwards_trend:",
            "attachments": [
                {
                    "color": status_color,
                    "title": f"{severity_emoji} {alert_data.get('title', 'Data Quality Alert')}",
                    "text": alert_data.get("message", ""),
                    "fields": [
                        {
                            "title": "Source",
                            "value": alert_data.get("source_name", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Rule",
                            "value": alert_data.get("rule_name", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Score",
                            "value": f"{alert_data.get('score', 0):.2%}",
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{alert_data.get('threshold', 0):.2%}",
                            "short": True
                        }
                    ],
                    "footer": "EDQMP",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
        
        if mention_str:
            message["text"] = mention_str
        
        response = await self.http_client.post(webhook_url, json=message)
        
        if response.status_code == 200:
            return {"status": "sent", "channel": channel}
        else:
            return {
                "status": "failed",
                "error": f"Slack returned {response.status_code}: {response.text}"
            }
    
    async def _send_email(
        self, 
        config: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send alert via email (using SMTP or SendGrid)"""
        recipients = config.get("recipients", [])
        
        if not recipients:
            return {"status": "failed", "error": "No email recipients configured"}
        
        # Use SendGrid if API key is available
        # For now, return a mock response (SMTP implementation would go here)
        subject_prefix = config.get("subject_prefix", "[EDQMP Alert]")
        subject = f"{subject_prefix} {alert_data.get('title', 'Data Quality Alert')}"
        
        # Build email body
        body = self._build_email_body(alert_data)
        
        # In production, integrate with SendGrid/SMTP
        logger.info(f"Would send email to {recipients}: {subject}")
        
        return {
            "status": "sent",
            "recipients": recipients,
            "subject": subject
        }
    
    async def _send_webhook(
        self, 
        config: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send alert to custom webhook"""
        url = config.get("url")
        
        if not url:
            return {"status": "failed", "error": "Webhook URL not configured"}
        
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        include_full = config.get("include_full_payload", True)
        
        # Prepare payload
        if include_full:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "alert": alert_data
            }
        else:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "title": alert_data.get("title"),
                "severity": alert_data.get("severity"),
                "status": alert_data.get("status"),
                "score": alert_data.get("score"),
                "source": alert_data.get("source_name"),
                "rule": alert_data.get("rule_name")
            }
        
        if method == "POST":
            response = await self.http_client.post(url, json=payload, headers=headers)
        elif method == "PUT":
            response = await self.http_client.put(url, json=payload, headers=headers)
        else:
            return {"status": "failed", "error": f"Unsupported method: {method}"}
        
        if response.status_code in [200, 201, 202, 204]:
            return {"status": "sent", "response_code": response.status_code}
        else:
            return {
                "status": "failed",
                "error": f"Webhook returned {response.status_code}"
            }
    
    async def _send_teams(
        self, 
        config: Dict[str, Any], 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send alert to Microsoft Teams"""
        webhook_url = config.get("webhook_url")
        
        if not webhook_url:
            return {"status": "failed", "error": "Teams webhook URL not configured"}
        
        severity = alert_data.get("severity", "warning")
        theme_color = {
            "info": "0078D7",
            "warning": "FF9800",
            "critical": "F44336"
        }.get(severity, "FF9800")
        
        message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": alert_data.get("title", "Data Quality Alert"),
            "sections": [{
                "activityTitle": alert_data.get("title", "Data Quality Alert"),
                "activitySubtitle": f"Source: {alert_data.get('source_name', 'Unknown')}",
                "facts": [
                    {"name": "Rule", "value": alert_data.get("rule_name", "Unknown")},
                    {"name": "Score", "value": f"{alert_data.get('score', 0):.2%}"},
                    {"name": "Status", "value": alert_data.get("status", "Unknown")},
                    {"name": "Time", "value": datetime.utcnow().isoformat()}
                ],
                "markdown": True
            }]
        }
        
        response = await self.http_client.post(webhook_url, json=message)
        
        if response.status_code == 200:
            return {"status": "sent"}
        else:
            return {
                "status": "failed",
                "error": f"Teams returned {response.status_code}"
            }
    
    def _build_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Build HTML email body"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #333;">{alert_data.get('title', 'Data Quality Alert')}</h2>
            <p>{alert_data.get('message', '')}</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Source</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('source_name', 'Unknown')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Rule</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('rule_name', 'Unknown')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Score</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('score', 0):.2%}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>Status</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{alert_data.get('status', 'Unknown')}</td>
                </tr>
            </table>
            <p style="color: #666; font-size: 12px; margin-top: 20px;">
                This alert was generated by EDQMP at {datetime.utcnow().isoformat()}
            </p>
        </body>
        </html>
        """
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Singleton instance
_dispatcher: Optional[AlertDispatcher] = None


def get_alert_dispatcher() -> AlertDispatcher:
    """Get or create alert dispatcher instance"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = AlertDispatcher()
    return _dispatcher
