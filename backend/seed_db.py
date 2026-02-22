
import os
from db_manager import DBManager
from datetime import datetime

ROOT = os.path.dirname(__file__)
DB_PATH = os.path.join(ROOT, "assistant.db")

def main():
    mgr = DBManager(DB_PATH)

    samples = [
        ("wifi", "Why does my WiFi keep disconnecting?",
         "Try forgetting the SSID, rejoining, toggling airplane mode, flushing DNS, and rebooting. If others are affected on the same AP, escalate as network incident.",
         "wifi,wireless,disconnect,ssid"),
        ("vpn", "Why is my VPN not connecting?",
         "Check basic internet connectivity, verify system date/time, restart VPN client, reload profile from portal, and capture the error code for escalation.",
         "vpn,tunnel,remote access"),
        ("performance", "Why is my laptop so slow?",
         "Restart, verify CPU/RAM in Task Manager, ensure at least 10% disk is free, disable heavy startup apps, and run Endpoint Health remediation.",
         "slow,lag,performance,slowness"),
        ("outlook", "Outlook not syncing when remote",
         "Confirm VPN, restart Outlook, run Send/Receive, repair profile, and validate mailbox size.",
         "outlook,email,sync,mail"),
        ("smart card", "Smart card is not detected",
         "Reinsert the card, try a different reader/port, restart smart card services, reboot, and test card on another device.",
         "smart card,piv,badge"),
        ("automation", "What can we automate in endpoint operations?",
         "Automate device onboarding/offboarding, role-based software installs, health checks, patch compliance, and certificate renewals.",
         "automation,scripting,workflow"),
    ]

    for cat, q, a, kws in samples:
        mgr.insert_kb(cat, q, a, kws)

    mgr.insert_log("VPN tunnel failure code 720 on LAPTOP-123", datetime.utcnow().isoformat())
    mgr.insert_health(82, 69, "degraded", datetime.utcnow().isoformat())

    print("Seeded knowledge base, example logs, and health row.")

if __name__ == "__main__":
    main()
