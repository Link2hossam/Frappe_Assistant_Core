# How to Use delete_document

## Overview

The `delete_document` tool permanently removes a Frappe document. This action is **irreversible**.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doctype` | string | **Yes** | — | Exact DocType name |
| `name` | string | **Yes** | — | Document name/ID |

## Response Format

```json
{
  "success": true,
  "result": {
    "success": true,
    "doctype": "ToDo",
    "name": "ckot534a7s",
    "message": "ToDo 'ckot534a7s' deleted successfully"
  }
}
```

## Best Practices

1. **Always confirm with the user** — deletion is permanent.
2. **Check dependencies first** — a document linked to others cannot be deleted; resolve the links first (see below).
3. **Resolve links explicitly** — if deletion fails because other documents reference this one, remove or reassign those links, or cancel/delete the dependent documents, then retry. Forced deletion is intentionally not available through this tool because it leaves orphaned references.
4. **Cancel before deleting** — submitted documents (`docstatus=1`) must be cancelled first.

## Edge Cases

- **Linked documents** — you can't delete an Item that Sales Invoices reference; remove/reassign the references or delete the dependent documents first.
- **Submitted documents** — must be cancelled (`docstatus=2`) before deletion.
- **System records** — some records (Administrator user, default roles) cannot be deleted.
- **Permission required** — user needs "delete" permission on the DocType.
