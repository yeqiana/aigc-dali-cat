export function distinctOptions(rows, key, label) {
  const seen = new Map();
  rows.forEach((row) => {
    const value = row[key];
    if (value === undefined || value === null || value === '') return;
    if (seen.has(value)) return;
    const text = label ? label(value) : String(value);
    seen.set(value, text === '' || text === undefined ? String(value) : text);
  });
  return Array.from(seen, ([value, text]) => ({ value, label: text }));
}

export function keywordMatch(row, keys, keyword) {
  const term = String(keyword || '').trim().toLowerCase();
  if (!term) return true;
  return keys.some((key) => {
    const value = row[key];
    if (value === undefined || value === null) return false;
    return String(value).toLowerCase().includes(term);
  });
}

export function anyFilter(filters) {
  return Object.values(filters || {}).some((value) => value !== '' && value !== null && value !== undefined);
}
