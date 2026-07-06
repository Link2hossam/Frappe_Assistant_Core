# Frappe Assistant Core - AI Assistant integration for Frappe Framework
# Copyright (C) 2025 Paul Clinton
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class AssistantAuditLog(Document):
    """Assistant Audit Log DocType controller."""

    def before_insert(self):
        """Set default values before inserting."""
        if not self.timestamp:
            self.timestamp = now()

        # Set IP address if available
        if hasattr(frappe.local, "request_ip") and not self.ip_address:
            self.ip_address = frappe.local.request_ip

    def validate(self):
        """Validate audit log entry."""
        # Ensure required fields are set
        if not self.user:
            self.user = frappe.session.user

        if not self.timestamp:
            self.timestamp = now()

    def before_save(self):
        """Enforce append-only immutability.

        The audit trail is the accountability record for everything the LLM does,
        so an existing entry must never be edited. Inserts are allowed (is_new());
        any later save is rejected — even from code paths that pass
        ignore_permissions=True, since controller hooks still run.

        Residual: frappe.db.set_value / raw SQL bypass controllers entirely. Guarding
        against a determined System Manager at that level requires cryptographic
        chaining (see docs/review/03-decisions.md, ADR-3 option C) and is out of scope
        for this change, which closes the desk/REST and ORM tamper paths.
        """
        if not self.is_new():
            frappe.throw(
                _("Assistant Audit Log entries are immutable and cannot be modified after creation."),
                frappe.PermissionError,
            )

    def on_trash(self):
        """Block individual ORM deletes.

        Retention deletion runs as a scheduled raw-SQL bulk DELETE (see
        assistant_core/server.py::cleanup_old_logs), which does not trigger this
        controller hook. Any ORM-level delete — including delete_doc(ignore_permissions=True)
        — is rejected here so audit history cannot be purged one row at a time.
        """
        frappe.throw(
            _(
                "Assistant Audit Log entries cannot be deleted individually. "
                "They are removed only by the scheduled retention job."
            ),
            frappe.PermissionError,
        )

    def get_formatted_execution_time(self):
        """Get formatted execution time."""
        if self.execution_time:
            if self.execution_time < 1:
                return f"{self.execution_time * 1000:.0f}ms"
            else:
                return f"{self.execution_time:.2f}s"
        return "N/A"


@frappe.whitelist()
def get_audit_statistics():
    """Get audit statistics for dashboard."""
    today = frappe.utils.today()

    # Total actions today
    total_today = frappe.db.count("Assistant Audit Log", filters={"creation": [">=", today]})

    # Success rate today
    successful_today = frappe.db.count(
        "Assistant Audit Log", filters={"creation": [">=", today], "status": "Success"}
    )

    success_rate = (successful_today / total_today * 100) if total_today > 0 else 0

    # Most used tools today
    most_used_tools = frappe.db.sql(
        """
        SELECT tool_name, COUNT(*) as count
        FROM `tabAssistant Audit Log`
        WHERE DATE(creation) = %s AND tool_name IS NOT NULL
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT 5
    """,
        (today,),
        as_dict=True,
    )

    # Average execution time
    avg_execution_time = (
        frappe.db.sql(
            """
        SELECT AVG(execution_time) as avg_time
        FROM `tabAssistant Audit Log`
        WHERE DATE(creation) = %s AND execution_time IS NOT NULL
    """,
            (today,),
        )[0][0]
        or 0
    )

    return {
        "total_actions_today": total_today,
        "success_rate": round(success_rate, 2),
        "most_used_tools": most_used_tools,
        "average_execution_time": round(avg_execution_time, 3) if avg_execution_time else 0,
    }


def get_context(context):
    context.title = _("Assistant Audit Log")
    context.docs = get_audit_logs()


def get_audit_logs():
    return frappe.get_all("Assistant Audit Log", fields=["*"], order_by="creation desc")
