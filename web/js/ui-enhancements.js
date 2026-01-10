/**
 * Enhanced UI functions for Google Stats
 * - Table formatting for script outputs
 * - Select2 dropdown utilities
 * - Better data visualization
 */

// Format script output with better HTML tables
function formatScriptOutput(data) {
    // Check if output contains CSV-like data or pipe-delimited tables
    const lines = data.trim().split('\n');

    // Look for pipe-delimited tables (|---|---|)
    const hasTable = lines.some(line => line.includes('|') && line.includes('---'));

    if (hasTable) {
        return formatPipeTable(lines);
    }

    // Look for CSV-like comma-separated data with headers
    const hasCSV = lines.length > 2 && lines[0].includes(',') && lines[1].includes(',');

    if (hasCSV && !data.includes('<')) {
        return formatCSVTable(lines);
    }

    // Default: wrap in pre tag with syntax highlighting
    return `<pre class="bg-light p-3 rounded">${escapeHtml(data)}</pre>`;
}

// Format pipe-delimited markdown tables to HTML
function formatPipeTable(lines) {
    let html = '<div class="data-table-output"><table class="table table-sm table-striped table-hover table-bordered">';
    let inTable = false;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        if (line.includes('|')) {
            // Check if separator line
            if (line.includes('---')) {
                continue;
            }

            const cells = line.split('|').filter(c => c.trim() !== '').map(c => c.trim());

            if (!inTable) {
                html += '<thead class="table-dark"><tr>';
                cells.forEach(cell => {
                    html += `<th>${escapeHtml(cell)}</th>`;
                });
                html += '</tr></thead><tbody>';
                inTable = true;
            } else {
                html += '<tr>';
                cells.forEach(cell => {
                    html += `<td>${escapeHtml(cell)}</td>`;
                });
                html += '</tr>';
            }
        } else if (line && inTable) {
            // Non-table line after table started
            html += '</tbody></table></div>';
            html += `<div class="alert alert-info mt-2">${escapeHtml(line)}</div>`;
            inTable = false;
        } else if (line && !inTable) {
            // Regular text before table
            if (line.includes('✅') || line.includes('✓')) {
                html += `<div class="alert alert-success mb-2"><i class="fas fa-check-circle"></i> ${escapeHtml(line)}</div>`;
            } else if (line.includes('❌') || line.includes('ERROR')) {
                html += `<div class="alert alert-danger mb-2"><i class="fas fa-exclamation-triangle"></i> ${escapeHtml(line)}</div>`;
            } else if (line.includes('⚠️') || line.includes('WARNING')) {
                html += `<div class="alert alert-warning mb-2"><i class="fas fa-exclamation-circle"></i> ${escapeHtml(line)}</div>`;
            } else if (line.includes('ℹ️') || line.includes('INFO')) {
                html += `<div class="alert alert-info mb-2"><i class="fas fa-info-circle"></i> ${escapeHtml(line)}</div>`;
            } else {
                html += `<div class="mb-2 text-muted">${escapeHtml(line)}</div>`;
            }
        }
    }

    if (inTable) {
        html += '</tbody></table></div>';
    }

    return html;
}

// Format CSV data to HTML table
function formatCSVTable(lines) {
    if (lines.length < 2) return '<pre class="bg-light p-3 rounded">' + escapeHtml(lines.join('\n')) + '</pre>';

    let html = '<div class="data-table-output"><table class="table table-sm table-striped table-hover table-bordered"><thead class="table-dark"><tr>';

    // Header row
    const headers = parseCSVLine(lines[0]);
    headers.forEach(header => {
        html += `<th>${escapeHtml(header)}</th>`;
    });
    html += '</tr></thead><tbody>';

    // Data rows
    for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim()) {
            const cells = parseCSVLine(lines[i]);
            html += '<tr>';
            cells.forEach(cell => {
                html += `<td>${escapeHtml(cell)}</td>`;
            });
            html += '</tr>';
        }
    }

    html += '</tbody></table></div>';
    return html;
}

// Parse CSV line respecting quotes
function parseCSVLine(line) {
    const cells = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            cells.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }

    cells.push(current.trim());
    return cells;
}

// Escape HTML special characters
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export table data to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.querySelector(`#${tableId} table`);
    if (!table) {
        alert('No table data to export');
        return;
    }

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(col => {
            let data = col.textContent.trim();
            // Escape quotes
            data = data.replace(/"/g, '""');
            // Wrap in quotes if contains comma
            if (data.includes(',')) {
                data = `"${data}"`;
            }
            csvRow.push(data);
        });
        csv.push(csvRow.join(','));
    });

    // Create download link
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
