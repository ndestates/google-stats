# Bulk Delete Audiences Guide

This guide explains how to use the bulk delete feature for Google Analytics 4 audiences.

## Overview

The bulk delete feature allows you to delete multiple audiences at once based on:
- **Name pattern matching** (case-insensitive)
- **Status filtering** (inactive only)
- **Combination of both**

## Prerequisites

- Activated Python virtual environment
- GA4 credentials configured
- `scripts/audience_management.py` script

## Usage Examples

### 1. Preview Deletion (Dry Run) - RECOMMENDED FIRST STEP

Always start with `--dry-run` to see what will be deleted:

```bash
# Preview deletion of all audiences containing "Listing"
python3 scripts/audience_management.py --action bulk-delete --pattern "Listing" --dry-run

# Preview deletion of all inactive audiences
python3 scripts/audience_management.py --action bulk-delete --inactive-only --dry-run

# Preview deletion of inactive audiences matching pattern
python3 scripts/audience_management.py --action bulk-delete --pattern "Test" --inactive-only --dry-run
```

### 2. Delete by Pattern

Delete all audiences whose name contains a specific text (case-insensitive):

```bash
# Delete all audiences containing "Listing"
python3 scripts/audience_management.py --action bulk-delete --pattern "Listing"

# Delete all audiences containing "Test"
python3 scripts/audience_management.py --action bulk-delete --pattern "Test"

# Delete all audiences containing "Combination"
python3 scripts/audience_management.py --action bulk-delete --pattern "Combination"
```

### 3. Delete Inactive Audiences Only

Delete all audiences with inactive status:

```bash
# Delete all inactive audiences
python3 scripts/audience_management.py --action bulk-delete --inactive-only
```

### 4. Combine Pattern and Status

Delete audiences matching both criteria:

```bash
# Delete inactive audiences containing "Old"
python3 scripts/audience_management.py --action bulk-delete --pattern "Old" --inactive-only

# Delete inactive test audiences
python3 scripts/audience_management.py --action bulk-delete --pattern "Test" --inactive-only
```

### 5. Delete All Audiences

**⚠️ WARNING: This will delete ALL audiences after confirmation**

```bash
# Preview all audiences
python3 scripts/audience_management.py --action bulk-delete --dry-run

# Delete all audiences (requires confirmation)
python3 scripts/audience_management.py --action bulk-delete
```

## Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--pattern "text"` | Match audiences containing this text (case-insensitive) | `--pattern "Listing"` |
| `--inactive-only` | Only match inactive audiences | `--inactive-only` |
| `--dry-run` | Preview without deleting | `--dry-run` |

## Workflow Recommendations

### Safe Workflow

1. **List audiences** to see what you have:
   ```bash
   python3 scripts/audience_management.py --action list
   ```

2. **Preview deletion** with dry run:
   ```bash
   python3 scripts/audience_management.py --action bulk-delete --pattern "YourPattern" --dry-run
   ```

3. **Review the list** carefully

4. **Execute deletion** (requires typing "yes" to confirm):
   ```bash
   python3 scripts/audience_management.py --action bulk-delete --pattern "YourPattern"
   ```

### Common Use Cases

#### Cleanup Test Audiences
```bash
# Preview
python3 scripts/audience_management.py --action bulk-delete --pattern "Test" --dry-run

# Delete
python3 scripts/audience_management.py --action bulk-delete --pattern "Test"
```

#### Remove Old Listing Audiences
```bash
# Preview
python3 scripts/audience_management.py --action bulk-delete --pattern "[Listing]" --dry-run

# Delete
python3 scripts/audience_management.py --action bulk-delete --pattern "[Listing]"
```

#### Clean Up Inactive Price Band Audiences
```bash
# Preview
python3 scripts/audience_management.py --action bulk-delete --pattern "Combination" --inactive-only --dry-run

# Delete
python3 scripts/audience_management.py --action bulk-delete --pattern "Combination" --inactive-only
```

## Safety Features

1. **Dry Run Mode**: Preview changes before applying
2. **Confirmation Prompt**: Must type "yes" to confirm deletion
3. **Detailed Preview**: Shows all audiences that will be deleted
4. **Status Display**: Shows active/inactive status for each audience
5. **Error Handling**: Reports failed deletions separately

## Output Example

```
📋 Found 15 audience(s) matching criteria:
================================================================================
1. [13216330243] [Listing] - Luxury Apartment
2. [13216330244] [Listing] - Family Home
3. [13216330245] [Listing] - Studio Flat
...

================================================================================

⚠️ Are you sure you want to delete 15 audience(s)? Type 'yes' to confirm: yes

🗑️ Deleting audiences...
✅ Archived audience ID: 13216330243
✅ Archived audience ID: 13216330244
✅ Archived audience ID: 13216330245
...

✅ Bulk deletion complete:
   Deleted: 15
   Failed: 0
```

## Alternative: Interactive Delete

For more manual control, use the interactive delete feature:

```bash
python3 scripts/audience_management.py --action delete-interactive
```

This allows you to:
- See all audiences numbered
- Select specific numbers or ranges (e.g., "1,3,5" or "17-50")
- Delete only selected audiences

## Troubleshooting

### No audiences match criteria
Check your pattern or try without filters:
```bash
python3 scripts/audience_management.py --action list
```

### Permission errors
Ensure your service account has Analytics Admin API access with edit permissions.

### Partial failures
The script will report which deletions failed and continue with others.

## Best Practices

1. **Always use --dry-run first**
2. **Backup important audiences** before bulk operations
3. **Check usage** before deleting:
   ```bash
   python3 scripts/audience_management.py --action show-usage
   ```
4. **Use specific patterns** to avoid accidental deletions
5. **Test with small batches** if unsure

## Related Commands

- `--action list` - List all audiences
- `--action delete-interactive` - Interactive deletion
- `--action show-usage` - Check audience usage
- `--action analyze` - Analyze audience performance

## Notes

- Deletion in GA4 actually "archives" audiences (they're not permanently removed)
- Archived audiences can be viewed in GA4 UI but won't be active
- Use caution with bulk operations
- Pattern matching is case-insensitive
