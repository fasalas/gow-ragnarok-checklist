import html
import json
import os
import re

SOURCE_HTML = r"c:\Users\Dr4gon\Downloads\GoW_Ragnarok-100Percent_Checklist.html"
OUT_DIR = r"C:\Users\Dr4gon\.gemini\antigravity\scratch\gow-ragnarok-checklist"
DATA_JSON_PATH = os.path.join(OUT_DIR, "data.json")
INDEX_HTML_PATH = os.path.join(OUT_DIR, "index.html")


def clean_info_html(raw_html: str) -> str:
    content = raw_html.strip()
    if not content:
        return ""
    # Ensure all links open in a new tab safely
    content = re.sub(
        r'<a\s+href="([^"]+)"[^>]*>',
        r'<a href="\1" target="_blank" rel="noopener noreferrer">',
        content,
    )
    # Remove outer <p>...</p> if there's only a single paragraph to keep layout compact
    single_p = re.match(r"^<p>(.*)</p>$", content, re.S)
    if single_p and "<p>" not in single_p.group(1):
        content = single_p.group(1).strip()
    return content


def strip_tags(raw_html: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", raw_html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_checklist(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    row_pattern = re.compile(
        r'<tr\s+class="checklist-item([^"]*)"[^>]*>(.*?)</tr>', re.S
    )
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.S)

    items = []
    for idx, match in enumerate(row_pattern.finditer(text), start=1):
        tr_classes = match.group(1).split()
        tr_body = match.group(2)
        initial_found = "found" in tr_classes

        tds = td_pattern.findall(tr_body)
        if len(tds) < 6:
            continue

        # TD 0: Checkbox & data attributes
        td0 = tds[0]
        loc_id_m = re.search(r'data-location-id="([^"]+)"', td0)
        cat_id_m = re.search(r'data-category-id="([^"]+)"', td0)
        map_id_m = re.search(r'data-map-id="([^"]+)"', td0)

        loc_id = loc_id_m.group(1) if loc_id_m else str(idx)
        cat_id = cat_id_m.group(1) if cat_id_m else ""
        map_id = map_id_m.group(1) if map_id_m else ""

        # TD 1: MapGenie location URL
        td1 = tds[1]
        href_m = re.search(r'href="([^"]+)"', td1)
        map_url = html.unescape(href_m.group(1)) if href_m else ""

        # TD 2: Name
        name = strip_tags(tds[2])

        # TD 3: Category
        category = strip_tags(tds[3])

        # TD 4: Map / Realm
        realm = strip_tags(tds[4])

        # TD 5: Info HTML & plain text
        info_html = clean_info_html(tds[5])
        info_text = strip_tags(tds[5])

        items.append(
            {
                "order": idx,
                "id": loc_id,
                "name": name,
                "category": category,
                "categoryId": cat_id,
                "realm": realm,
                "mapId": map_id,
                "mapUrl": map_url,
                "infoHtml": info_html,
                "infoText": info_text,
                "initialFound": initial_found,
            }
        )

    return items


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
  <meta name="theme-color" content="#111924" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <title>God of War Ragnarök — 100% Checklist</title>
  <link rel="manifest" href="manifest.json" />
  <link rel="icon" type="image/svg+xml" href="icon.svg" />
  <link rel="apple-touch-icon" href="icon.svg" />
  <style>
    :root {
      --bg-base: #0a0f16;
      --bg-surface: #121b28;
      --bg-surface-elevated: #192536;
      --bg-surface-hover: #213046;
      --bg-found: rgba(34, 197, 94, 0.08);
      --border-subtle: rgba(212, 162, 76, 0.18);
      --border-strong: rgba(212, 162, 76, 0.48);
      --gold-light: #f6d896;
      --gold: #d4a24c;
      --gold-dark: #9a6e22;
      --ice: #56ccf2;
      --ice-dark: #2f80ed;
      --success: #22c55e;
      --danger: #ef4444;
      --text-main: #eef2f7;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.45);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
      background: radial-gradient(circle at 50% 0%, #172334 0%, var(--bg-base) 65%);
      background-attachment: fixed;
      color: var(--text-main);
      line-height: 1.45;
      min-height: 100vh;
      padding-bottom: 64px;
    }

    a {
      color: var(--ice);
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }

    /* Top App Header */
    .app-header {
      background: linear-gradient(180deg, rgba(18, 27, 40, 0.98) 0%, rgba(12, 18, 28, 0.95) 100%);
      border-bottom: 1px solid var(--border-subtle);
      padding: 16px 16px 14px;
      position: relative;
      z-index: 30;
    }

    .header-inner {
      max-width: 1280px;
      margin: 0 auto;
    }

    .brand-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .brand-title-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
      flex-shrink: 0;
    }

    .brand-title {
      font-size: 1.2rem;
      font-weight: 800;
      letter-spacing: 0.02em;
      background: linear-gradient(90deg, var(--gold-light), var(--gold));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-subtitle {
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 8px 12px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-subtle);
      background: var(--bg-surface-elevated);
      color: var(--text-main);
      cursor: pointer;
      transition: all 0.15s ease;
      user-select: none;
      white-space: nowrap;
    }

    .btn:hover {
      background: var(--bg-surface-hover);
      border-color: var(--border-strong);
    }

    .btn-gold {
      background: linear-gradient(135deg, rgba(212, 162, 76, 0.22), rgba(154, 110, 34, 0.25));
      border-color: var(--gold);
      color: var(--gold-light);
    }

    .btn-gold:hover {
      background: linear-gradient(135deg, rgba(212, 162, 76, 0.35), rgba(154, 110, 34, 0.4));
    }

    .btn-danger {
      border-color: rgba(239, 68, 68, 0.4);
      color: #fca5a5;
    }

    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.15);
      border-color: var(--danger);
    }

    /* Overall Progress Bar */
    .overall-progress-card {
      margin-top: 14px;
      background: rgba(10, 15, 22, 0.65);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 14px;
    }

    .progress-stats-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 8px;
      gap: 8px;
      flex-wrap: wrap;
    }

    .progress-main-label {
      font-weight: 700;
      font-size: 0.95rem;
      color: var(--gold-light);
    }

    .progress-counts {
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .progress-counts strong {
      color: var(--text-main);
    }

    .progress-track {
      width: 100%;
      height: 10px;
      background: rgba(255, 255, 255, 0.07);
      border-radius: 999px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--ice-dark), var(--ice), var(--gold));
      border-radius: 999px;
      transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Dashboard Section (Realms & Categories) */
    .main-container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 0 12px;
    }

    .dashboard-panel {
      margin-top: 14px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
    }

    .dashboard-tabs {
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: rgba(10, 15, 22, 0.5);
    }

    .dash-tab {
      flex: 1;
      padding: 10px 14px;
      text-align: center;
      font-size: 0.84rem;
      font-weight: 700;
      color: var(--text-muted);
      background: transparent;
      border: none;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.15s ease;
    }

    .dash-tab.active {
      color: var(--gold-light);
      border-bottom-color: var(--gold);
      background: rgba(212, 162, 76, 0.07);
    }

    .dash-content {
      padding: 12px;
      display: none;
    }

    .dash-content.active {
      display: block;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
      gap: 8px;
    }

    .stat-card {
      background: var(--bg-surface-elevated);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: var(--radius-sm);
      padding: 9px 11px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .stat-card:hover {
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }

    .stat-card.selected {
      border-color: var(--gold);
      background: rgba(212, 162, 76, 0.14);
      box-shadow: 0 0 0 1px var(--gold);
    }

    .stat-card.completed {
      border-color: rgba(34, 197, 94, 0.45);
    }

    .stat-card-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 6px;
    }

    .stat-name {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-main);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .stat-fraction {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      flex-shrink: 0;
    }

    .stat-card.completed .stat-fraction {
      color: var(--success);
    }

    .mini-track {
      height: 5px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 99px;
      overflow: hidden;
    }

    .mini-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--ice), var(--gold));
      border-radius: 99px;
      transition: width 0.25s ease;
    }

    .stat-card.completed .mini-fill {
      background: var(--success);
    }

    /* Sticky Filter & Controls Bar */
    .controls-bar {
      position: sticky;
      top: 0;
      z-index: 25;
      background: rgba(12, 18, 28, 0.96);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      margin-top: 12px;
      padding: 10px 12px;
      box-shadow: var(--shadow-md);
    }

    .controls-grid {
      display: grid;
      grid-template-columns: 1.5fr 1fr 1fr 1fr;
      gap: 8px;
    }

    .search-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }

    .search-input,
    .select-input {
      width: 100%;
      padding: 9px 12px;
      font-size: 0.86rem;
      color: var(--text-main);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      outline: none;
      transition: border-color 0.15s ease;
    }

    .search-input {
      padding-right: 32px;
    }

    .search-input:focus,
    .select-input:focus {
      border-color: var(--gold);
    }

    .clear-search-btn {
      position: absolute;
      right: 8px;
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 1.1rem;
      cursor: pointer;
      display: none;
      padding: 2px 6px;
    }

    .controls-bottom-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-top: 8px;
      flex-wrap: wrap;
    }

    .status-pills {
      display: inline-flex;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 2px;
      gap: 2px;
    }

    .status-pill {
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .status-pill.active {
      background: var(--gold);
      color: #090d14;
    }

    .results-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 0.8rem;
      color: var(--text-muted);
      flex-wrap: wrap;
    }

    .link-btn {
      background: none;
      border: none;
      color: var(--gold-light);
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: underline;
    }

    /* Checklist Views */
    .checklist-section {
      margin-top: 12px;
    }

    /* Card View (Mobile & Default on small screens) */
    .cards-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 10px;
    }

    .item-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      display: flex;
      gap: 12px;
      align-items: flex-start;
      transition: background 0.15s ease, border-color 0.15s ease;
      cursor: pointer;
    }

    .item-card:hover {
      border-color: var(--border-strong);
    }

    .item-card.found {
      background: var(--bg-found);
      border-color: rgba(34, 197, 94, 0.3);
    }

    .item-card.found .item-title {
      text-decoration: line-through;
      color: var(--text-muted);
    }

    .check-wrapper {
      padding-top: 2px;
      flex-shrink: 0;
    }

    .custom-check {
      width: 24px;
      height: 24px;
      border-radius: 6px;
      border: 2px solid var(--gold);
      background: rgba(10, 15, 22, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
      color: transparent;
      font-weight: 900;
      font-size: 0.9rem;
    }

    .found .custom-check {
      background: var(--success);
      border-color: var(--success);
      color: #06130b;
    }

    .card-body {
      flex: 1;
      min-width: 0;
    }

    .card-header-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
    }

    .item-title {
      font-weight: 700;
      font-size: 0.96rem;
      color: var(--text-main);
      word-break: break-word;
    }

    .pin-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.74rem;
      font-weight: 600;
      background: rgba(86, 204, 242, 0.12);
      border: 1px solid rgba(86, 204, 242, 0.35);
      color: var(--ice);
      flex-shrink: 0;
      text-decoration: none !important;
    }

    .pin-btn:hover {
      background: rgba(86, 204, 242, 0.24);
    }

    .badges-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }

    .badge {
      font-size: 0.73rem;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .badge-realm {
      background: rgba(212, 162, 76, 0.15);
      color: var(--gold-light);
      border: 1px solid rgba(212, 162, 76, 0.32);
    }

    .badge-category {
      background: rgba(148, 163, 184, 0.14);
      color: #cbd5e1;
      border: 1px solid rgba(148, 163, 184, 0.25);
    }

    .item-info {
      margin-top: 8px;
      font-size: 0.82rem;
      color: var(--text-muted);
      background: rgba(10, 15, 22, 0.45);
      padding: 7px 9px;
      border-radius: 6px;
      border-left: 2px solid var(--gold-dark);
    }

    .item-info strong {
      color: var(--text-main);
    }

    /* Table View (Desktop) */
    .table-container {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow-x: auto;
    }

    .items-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }

    .items-table th {
      background: var(--bg-surface-elevated);
      color: var(--gold-light);
      font-weight: 700;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-strong);
      user-select: none;
      white-space: nowrap;
    }

    .items-table th.sortable {
      cursor: pointer;
    }

    .items-table th.sortable:hover {
      background: var(--bg-surface-hover);
    }

    .items-table td {
      padding: 11px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      vertical-align: middle;
    }

    .items-table tbody tr {
      cursor: pointer;
      transition: background 0.12s ease;
    }

    .items-table tbody tr:hover {
      background: var(--bg-surface-hover);
    }

    .items-table tbody tr.found {
      background: var(--bg-found);
    }

    .items-table tbody tr.found .td-name {
      text-decoration: line-through;
      color: var(--text-muted);
    }

    .td-name {
      font-weight: 700;
      color: var(--text-main);
    }

    .td-info {
      color: var(--text-muted);
      font-size: 0.83rem;
      max-width: 460px;
    }

    .td-info strong {
      color: var(--text-main);
    }

    /* Empty State */
    .empty-state {
      text-align: center;
      padding: 42px 20px;
      background: var(--bg-surface);
      border: 1px dashed var(--border-subtle);
      border-radius: var(--radius-md);
      color: var(--text-muted);
    }

    /* Modal (Sync / Backup / Export) */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.72);
      backdrop-filter: blur(4px);
      z-index: 100;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }

    .modal-backdrop.open {
      display: flex;
    }

    .modal {
      background: var(--bg-surface);
      border: 1px solid var(--border-strong);
      border-radius: var(--radius-lg);
      max-width: 520px;
      width: 100%;
      padding: 20px;
      box-shadow: var(--shadow-md);
      max-height: 90vh;
      overflow-y: auto;
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border-subtle);
    }

    .modal-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--gold-light);
    }

    .modal-close {
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 1.4rem;
      cursor: pointer;
      line-height: 1;
    }

    .modal-section {
      margin-bottom: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }

    .modal-section:last-child {
      margin-bottom: 0;
      padding-bottom: 0;
      border-bottom: none;
    }

    .modal-section h4 {
      font-size: 0.9rem;
      margin-bottom: 6px;
      color: var(--text-main);
    }

    .modal-section p {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 10px;
    }

    .modal-btn-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .sync-code-box {
      width: 100%;
      min-height: 68px;
      background: var(--bg-base);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      color: var(--text-main);
      padding: 8px;
      font-family: monospace;
      font-size: 0.78rem;
      margin-bottom: 8px;
      resize: vertical;
    }

    .toast {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%) translateY(80px);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--gold);
      color: var(--text-main);
      padding: 10px 18px;
      border-radius: 999px;
      font-size: 0.84rem;
      font-weight: 600;
      box-shadow: var(--shadow-md);
      z-index: 200;
      opacity: 0;
      transition: all 0.25s ease;
      pointer-events: none;
    }

    .toast.show {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }

    @media (max-width: 820px) {
      .controls-grid {
        grid-template-columns: 1fr 1fr;
      }
      .search-wrapper {
        grid-column: 1 / -1;
      }
    }

    @media (max-width: 520px) {
      .controls-grid {
        grid-template-columns: 1fr;
      }
      .cards-container {
        grid-template-columns: 1fr;
      }
      .stats-grid {
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      }
    }
  </style>
</head>
<body>
  <header class="app-header">
    <div class="header-inner">
      <div class="brand-row">
        <div class="brand-title-group">
          <img src="icon.svg" alt="GoW Icon" class="brand-icon" />
          <div>
            <h1 class="brand-title">GOD OF WAR RAGNARÖK</h1>
            <div class="brand-subtitle">100% Completion Checklist • 10 Realms • 23 Categories</div>
          </div>
        </div>
        <div class="header-actions">
          <button type="button" class="btn" id="toggle-dashboard-btn" title="Show or hide Realm & Category breakdown">
            <span>📊 Breakdown</span>
          </button>
          <button type="button" class="btn" id="toggle-view-btn" title="Switch between Mobile Cards and Desktop Table">
            <span id="view-mode-label">🗂️ View: Auto</span>
          </button>
          <button type="button" class="btn btn-gold" id="open-sync-btn">
            <span>💾 Backup / Sync</span>
          </button>
        </div>
      </div>

      <div class="overall-progress-card">
        <div class="progress-stats-row">
          <span class="progress-main-label" id="overall-percent-text">18.3% Complete</span>
          <span class="progress-counts">
            <strong id="overall-found-count">91</strong> / <strong id="overall-total-count">496</strong> Found
            (<span id="overall-remaining-count">405</span> left)
          </span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="overall-progress-fill"></div>
        </div>
      </div>
    </div>
  </header>

  <main class="main-container">
    <!-- Collapsible Realm & Category Progress Dashboard -->
    <section class="dashboard-panel" id="dashboard-panel">
      <div class="dashboard-tabs">
        <button type="button" class="dash-tab active" data-tab="realms">🌍 Progress by Realm (10)</button>
        <button type="button" class="dash-tab" data-tab="categories">🛡️ Progress by Category (23)</button>
      </div>
      <div class="dash-content active" id="tab-realms">
        <div class="stats-grid" id="realms-grid"></div>
      </div>
      <div class="dash-content" id="tab-categories">
        <div class="stats-grid" id="categories-grid"></div>
      </div>
    </section>

    <!-- Sticky Filter & Sort Controls -->
    <section class="controls-bar">
      <div class="controls-grid">
        <div class="search-wrapper">
          <input
            type="search"
            id="search-input"
            class="search-input"
            placeholder="Search item name, requirement, quest, or realm..."
            autocomplete="off"
          />
          <button type="button" class="clear-search-btn" id="clear-search-btn" aria-label="Clear search">×</button>
        </div>

        <select id="realm-select" class="select-input" aria-label="Filter by Realm">
          <option value="">All Realms (10)</option>
        </select>

        <select id="category-select" class="select-input" aria-label="Filter by Category">
          <option value="">All Categories (23)</option>
        </select>

        <select id="sort-select" class="select-input" aria-label="Sort items">
          <option value="order-asc">Sort: Default Order</option>
          <option value="status-unfound">Sort: Remaining First</option>
          <option value="status-found">Sort: Found First</option>
          <option value="name-asc">Sort: Name (A → Z)</option>
          <option value="name-desc">Sort: Name (Z → A)</option>
          <option value="realm-asc">Sort: Realm (A → Z)</option>
          <option value="category-asc">Sort: Category (A → Z)</option>
        </select>
      </div>

      <div class="controls-bottom-row">
        <div class="status-pills" role="group" aria-label="Filter by completion status">
          <button type="button" class="status-pill active" data-status="all">All</button>
          <button type="button" class="status-pill" data-status="unfound">Hide Found</button>
          <button type="button" class="status-pill" data-status="found">Found Only</button>
        </div>

        <div class="results-meta">
          <span id="showing-count-text">Showing 496 of 496 items</span>
          <button type="button" class="link-btn" id="reset-filters-btn" style="display: none;">Clear Filters</button>
        </div>
      </div>
    </section>

    <!-- Checklist Output -->
    <section class="checklist-section" id="checklist-output"></section>
  </main>

  <!-- Backup / Sync / Export Modal -->
  <div class="modal-backdrop" id="sync-modal">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="sync-modal-title">
      <div class="modal-header">
        <span class="modal-title" id="sync-modal-title">💾 Backup, Sync & Export Progress</span>
        <button type="button" class="modal-close" id="close-sync-btn" aria-label="Close">×</button>
      </div>

      <div class="modal-section">
        <h4>📱 Quick Transfer Code (PC ↔ Android)</h4>
        <p>Copy this compact code to send your progress via message/notes, or paste a code from another device and tap Load.</p>
        <textarea id="sync-code-textarea" class="sync-code-box" placeholder="Paste sync code here..."></textarea>
        <div class="modal-btn-row">
          <button type="button" class="btn btn-gold" id="copy-code-btn">📋 Copy Current Code</button>
          <button type="button" class="btn" id="load-code-btn">📥 Load Code</button>
        </div>
      </div>

      <div class="modal-section">
        <h4>📂 File Backup & Spreadsheet Export</h4>
        <p>Download a JSON backup file to restore later, or export a full CSV spreadsheet compatible with Excel and Google Sheets.</p>
        <div class="modal-btn-row">
          <button type="button" class="btn btn-gold" id="export-json-btn">⬇️ Export .JSON</button>
          <label class="btn" style="cursor: pointer;">
            ⬆️ Import .JSON
            <input type="file" id="import-json-input" accept=".json,application/json" style="display: none;" />
          </label>
          <button type="button" class="btn" id="export-csv-btn">📊 Export Excel .CSV</button>
        </div>
      </div>

      <div class="modal-section">
        <h4>⚠️ Reset Options</h4>
        <p>Restore the initial 91 found items from your original HTML file, or clear all progress to 0%.</p>
        <div class="modal-btn-row">
          <button type="button" class="btn" id="restore-initial-btn">🔄 Restore Initial (91 Found)</button>
          <button type="button" class="btn btn-danger" id="reset-zero-btn">🗑️ Reset All to 0%</button>
        </div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    const CHECKLIST_DATA = __CHECKLIST_JSON__;
    const STORAGE_KEY = 'gow_ragnarok_found_ids_v1';
    const VIEW_MODE_KEY = 'gow_ragnarok_view_mode_v1';

    // State
    let foundSet = new Set();
    let filterSearch = '';
    let filterRealm = '';
    let filterCategory = '';
    let filterStatus = 'all'; // 'all' | 'unfound' | 'found'
    let sortMode = 'order-asc';
    let viewMode = localStorage.getItem(VIEW_MODE_KEY) || 'auto'; // 'auto' | 'cards' | 'table'

    // Load initial or saved progress
    function loadProgress() {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed)) {
            foundSet = new Set(parsed.map(String));
            return;
          }
        } catch (e) {
          console.error('Failed to parse saved progress:', e);
        }
      }
      // Default to the 91 items marked found in the user's source HTML
      foundSet = new Set(
        CHECKLIST_DATA.filter((item) => item.initialFound).map((item) => String(item.id))
      );
      saveProgress();
    }

    function saveProgress() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(foundSet)));
      } catch (e) {
        console.error('Failed to save progress:', e);
      }
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(showToast._timer);
      showToast._timer = setTimeout(() => t.classList.remove('show'), 2400);
    }

    // Compact base64 bitfield for effortless PC <-> Android copy/paste sync
    function encodeSyncCode() {
      const bytes = new Uint8Array(Math.ceil(CHECKLIST_DATA.length / 8));
      CHECKLIST_DATA.forEach((item, idx) => {
        if (foundSet.has(String(item.id))) {
          bytes[idx >> 3] |= 1 << (idx & 7);
        }
      });
      let binary = '';
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      return 'GOWR1:' + btoa(binary);
    }

    function decodeSyncCode(code) {
      const clean = code.trim();
      if (!clean.startsWith('GOWR1:')) {
        throw new Error('Invalid sync code prefix');
      }
      const binary = atob(clean.slice(6));
      const newSet = new Set();
      CHECKLIST_DATA.forEach((item, idx) => {
        const byteIndex = idx >> 3;
        if (byteIndex < binary.length) {
          const byte = binary.charCodeAt(byteIndex);
          if (byte & (1 << (idx & 7))) {
            newSet.add(String(item.id));
          }
        }
      });
      return newSet;
    }

    // Populate Realm & Category filter dropdowns
    function initSelectOptions() {
      const realmCounts = {};
      const catCounts = {};
      CHECKLIST_DATA.forEach((item) => {
        realmCounts[item.realm] = (realmCounts[item.realm] || 0) + 1;
        catCounts[item.category] = (catCounts[item.category] || 0) + 1;
      });

      const realmSelect = document.getElementById('realm-select');
      Object.keys(realmCounts)
        .sort()
        .forEach((realm) => {
          const opt = document.createElement('option');
          opt.value = realm;
          opt.textContent = `${realm} (${realmCounts[realm]})`;
          realmSelect.appendChild(opt);
        });

      const catSelect = document.getElementById('category-select');
      Object.keys(catCounts)
        .sort()
        .forEach((cat) => {
          const opt = document.createElement('option');
          opt.value = cat;
          opt.textContent = `${cat} (${catCounts[cat]})`;
          catSelect.appendChild(opt);
        });
    }

    // Update overall bar + Realm & Category dashboard cards
    function renderDashboard() {
      const total = CHECKLIST_DATA.length;
      const found = foundSet.size;
      const remaining = total - found;
      const pct = total > 0 ? ((found / total) * 100).toFixed(1) : '0.0';

      document.getElementById('overall-percent-text').textContent = `${pct}% Complete`;
      document.getElementById('overall-found-count').textContent = found;
      document.getElementById('overall-total-count').textContent = total;
      document.getElementById('overall-remaining-count').textContent = remaining;
      document.getElementById('overall-progress-fill').style.width = `${pct}%`;

      // Group by realm and category
      const realms = {};
      const categories = {};

      CHECKLIST_DATA.forEach((item) => {
        const isFound = foundSet.has(String(item.id));
        if (!realms[item.realm]) realms[item.realm] = { total: 0, found: 0 };
        realms[item.realm].total++;
        if (isFound) realms[item.realm].found++;

        if (!categories[item.category]) categories[item.category] = { total: 0, found: 0 };
        categories[item.category].total++;
        if (isFound) categories[item.category].found++;
      });

      const realmsGrid = document.getElementById('realms-grid');
      realmsGrid.innerHTML = Object.keys(realms)
        .sort()
        .map((r) => {
          const st = realms[r];
          const rPct = Math.round((st.found / st.total) * 100);
          const isSelected = filterRealm === r;
          const isCompleted = st.found === st.total;
          return `
            <div class="stat-card ${isSelected ? 'selected' : ''} ${isCompleted ? 'completed' : ''}"
                 data-filter-realm="${escapeAttr(r)}" title="Tap to filter by ${escapeAttr(r)}">
              <div class="stat-card-top">
                <span class="stat-name">${escapeHtml(r)}</span>
                <span class="stat-fraction">${st.found}/${st.total}</span>
              </div>
              <div class="mini-track">
                <div class="mini-fill" style="width: ${rPct}%"></div>
              </div>
            </div>
          `;
        })
        .join('');

      const categoriesGrid = document.getElementById('categories-grid');
      categoriesGrid.innerHTML = Object.keys(categories)
        .sort()
        .map((c) => {
          const st = categories[c];
          const cPct = Math.round((st.found / st.total) * 100);
          const isSelected = filterCategory === c;
          const isCompleted = st.found === st.total;
          return `
            <div class="stat-card ${isSelected ? 'selected' : ''} ${isCompleted ? 'completed' : ''}"
                 data-filter-category="${escapeAttr(c)}" title="Tap to filter by ${escapeAttr(c)}">
              <div class="stat-card-top">
                <span class="stat-name">${escapeHtml(c)}</span>
                <span class="stat-fraction">${st.found}/${st.total}</span>
              </div>
              <div class="mini-track">
                <div class="mini-fill" style="width: ${cPct}%"></div>
              </div>
            </div>
          `;
        })
        .join('');
    }

    function escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    function escapeAttr(str) {
      return escapeHtml(str).replace(/'/g, '&#39;');
    }

    function getFilteredAndSortedItems() {
      const q = filterSearch.trim().toLowerCase();

      const filtered = CHECKLIST_DATA.filter((item) => {
        const isFound = foundSet.has(String(item.id));
        if (filterStatus === 'unfound' && isFound) return false;
        if (filterStatus === 'found' && !isFound) return false;
        if (filterRealm && item.realm !== filterRealm) return false;
        if (filterCategory && item.category !== filterCategory) return false;
        if (q) {
          const hay = `${item.name} ${item.category} ${item.realm} ${item.infoText}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      });

      filtered.sort((a, b) => {
        const aFound = foundSet.has(String(a.id)) ? 1 : 0;
        const bFound = foundSet.has(String(b.id)) ? 1 : 0;

        switch (sortMode) {
          case 'status-unfound':
            if (aFound !== bFound) return aFound - bFound;
            return a.order - b.order;
          case 'status-found':
            if (aFound !== bFound) return bFound - aFound;
            return a.order - b.order;
          case 'name-asc':
            return a.name.localeCompare(b.name);
          case 'name-desc':
            return b.name.localeCompare(a.name);
          case 'realm-asc':
            return a.realm.localeCompare(b.realm) || a.order - b.order;
          case 'category-asc':
            return a.category.localeCompare(b.category) || a.order - b.order;
          case 'order-asc':
          default:
            return a.order - b.order;
        }
      });

      return filtered;
    }

    function isDesktopTableActive() {
      if (viewMode === 'cards') return false;
      if (viewMode === 'table') return true;
      return window.innerWidth >= 900;
    }

    function renderChecklist() {
      const items = getFilteredAndSortedItems();
      const container = document.getElementById('checklist-output');

      document.getElementById('showing-count-text').textContent =
        `Showing ${items.length} of ${CHECKLIST_DATA.length} items`;

      const hasActiveFilters =
        filterSearch.trim() !== '' ||
        filterRealm !== '' ||
        filterCategory !== '' ||
        filterStatus !== 'all';
      document.getElementById('reset-filters-btn').style.display = hasActiveFilters
        ? 'inline-block'
        : 'none';

      if (items.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <p>No checklist items match your current filters.</p>
          </div>
        `;
        return;
      }

      if (isDesktopTableActive()) {
        container.innerHTML = `
          <div class="table-container">
            <table class="items-table">
              <thead>
                <tr>
                  <th class="sortable" data-sort-col="status" style="width: 72px;">Found</th>
                  <th style="width: 84px;">Map Pin</th>
                  <th class="sortable" data-sort-col="name">Name</th>
                  <th class="sortable" data-sort-col="category">Category</th>
                  <th class="sortable" data-sort-col="realm">Realm</th>
                  <th>Info / Unlock Requirements</th>
                </tr>
              </thead>
              <tbody>
                ${items
                  .map((item) => {
                    const isFound = foundSet.has(String(item.id));
                    return `
                      <tr class="${isFound ? 'found' : ''}" data-item-id="${item.id}">
                        <td>
                          <div class="custom-check">${isFound ? '✓' : ''}</div>
                        </td>
                        <td>
                          ${
                            item.mapUrl
                              ? `<a href="${escapeAttr(item.mapUrl)}" target="_blank" rel="noopener noreferrer" class="pin-btn" title="Open on MapGenie">📍 Map</a>`
                              : ''
                          }
                        </td>
                        <td class="td-name">${escapeHtml(item.name)}</td>
                        <td><span class="badge badge-category">${escapeHtml(item.category)}</span></td>
                        <td><span class="badge badge-realm">${escapeHtml(item.realm)}</span></td>
                        <td class="td-info">${item.infoHtml || '<span style="color:var(--text-dim)">—</span>'}</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="cards-container">
            ${items
              .map((item) => {
                const isFound = foundSet.has(String(item.id));
                return `
                  <article class="item-card ${isFound ? 'found' : ''}" data-item-id="${item.id}">
                    <div class="check-wrapper">
                      <div class="custom-check">${isFound ? '✓' : ''}</div>
                    </div>
                    <div class="card-body">
                      <div class="card-header-row">
                        <div class="item-title">${escapeHtml(item.name)}</div>
                        ${
                          item.mapUrl
                            ? `<a href="${escapeAttr(item.mapUrl)}" target="_blank" rel="noopener noreferrer" class="pin-btn" title="Open pin on MapGenie">📍 Map</a>`
                            : ''
                        }
                      </div>
                      <div class="badges-row">
                        <span class="badge badge-realm">🌍 ${escapeHtml(item.realm)}</span>
                        <span class="badge badge-category">🛡️ ${escapeHtml(item.category)}</span>
                      </div>
                      ${item.infoHtml ? `<div class="item-info">${item.infoHtml}</div>` : ''}
                    </div>
                  </article>
                `;
              })
              .join('')}
          </div>
        `;
      }
    }

    function toggleItemFound(id) {
      const key = String(id);
      if (foundSet.has(key)) {
        foundSet.delete(key);
      } else {
        foundSet.add(key);
      }
      saveProgress();
      renderDashboard();
      renderChecklist();
    }

    function updateViewModeButton() {
      const label = document.getElementById('view-mode-label');
      if (viewMode === 'auto') label.textContent = '🗂️ View: Auto';
      else if (viewMode === 'cards') label.textContent = '📱 View: Cards';
      else label.textContent = '💻 View: Table';
    }

    // Event Listeners
    document.addEventListener('DOMContentLoaded', () => {
      loadProgress();
      initSelectOptions();
      updateViewModeButton();
      renderDashboard();
      renderChecklist();

      // Register Service Worker for PWA offline capability when served over HTTP/HTTPS
      if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
        navigator.serviceWorker.register('./sw.js').catch(() => {});
      }

      // Toggle item found via event delegation
      document.getElementById('checklist-output').addEventListener('click', (e) => {
        // Do not toggle checkbox if the user clicked a link
        if (e.target.closest('a')) return;

        // Sortable table headers
        const th = e.target.closest('th.sortable');
        if (th) {
          const col = th.getAttribute('data-sort-col');
          if (col === 'status') {
            sortMode = sortMode === 'status-unfound' ? 'status-found' : 'status-unfound';
          } else if (col === 'name') {
            sortMode = sortMode === 'name-asc' ? 'name-desc' : 'name-asc';
          } else if (col === 'realm') {
            sortMode = 'realm-asc';
          } else if (col === 'category') {
            sortMode = 'category-asc';
          }
          document.getElementById('sort-select').value = sortMode;
          renderChecklist();
          return;
        }

        const rowOrCard = e.target.closest('[data-item-id]');
        if (rowOrCard) {
          toggleItemFound(rowOrCard.getAttribute('data-item-id'));
        }
      });

      // Dashboard tabs
      document.querySelectorAll('.dash-tab').forEach((tab) => {
        tab.addEventListener('click', () => {
          document.querySelectorAll('.dash-tab').forEach((t) => t.classList.remove('active'));
          document.querySelectorAll('.dash-content').forEach((c) => c.classList.remove('active'));
          tab.classList.add('active');
          document.getElementById('tab-' + tab.getAttribute('data-tab')).classList.add('active');
        });
      });

      // Dashboard card click -> filter by realm or category
      document.getElementById('dashboard-panel').addEventListener('click', (e) => {
        const realmCard = e.target.closest('[data-filter-realm]');
        if (realmCard) {
          const r = realmCard.getAttribute('data-filter-realm');
          filterRealm = filterRealm === r ? '' : r;
          document.getElementById('realm-select').value = filterRealm;
          renderDashboard();
          renderChecklist();
          return;
        }
        const catCard = e.target.closest('[data-filter-category]');
        if (catCard) {
          const c = catCard.getAttribute('data-filter-category');
          filterCategory = filterCategory === c ? '' : c;
          document.getElementById('category-select').value = filterCategory;
          renderDashboard();
          renderChecklist();
        }
      });

      // Toggle Dashboard visibility
      document.getElementById('toggle-dashboard-btn').addEventListener('click', () => {
        const panel = document.getElementById('dashboard-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      });

      // Toggle View Mode (Auto -> Cards -> Table)
      document.getElementById('toggle-view-btn').addEventListener('click', () => {
        if (viewMode === 'auto') viewMode = 'cards';
        else if (viewMode === 'cards') viewMode = 'table';
        else viewMode = 'auto';
        localStorage.setItem(VIEW_MODE_KEY, viewMode);
        updateViewModeButton();
        renderChecklist();
      });

      // Search input
      const searchInput = document.getElementById('search-input');
      const clearSearchBtn = document.getElementById('clear-search-btn');
      searchInput.addEventListener('input', () => {
        filterSearch = searchInput.value;
        clearSearchBtn.style.display = filterSearch ? 'block' : 'none';
        renderChecklist();
      });
      clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterSearch = '';
        clearSearchBtn.style.display = 'none';
        renderChecklist();
      });

      // Dropdowns
      document.getElementById('realm-select').addEventListener('change', (e) => {
        filterRealm = e.target.value;
        renderDashboard();
        renderChecklist();
      });

      document.getElementById('category-select').addEventListener('change', (e) => {
        filterCategory = e.target.value;
        renderDashboard();
        renderChecklist();
      });

      document.getElementById('sort-select').addEventListener('change', (e) => {
        sortMode = e.target.value;
        renderChecklist();
      });

      // Status pills
      document.querySelectorAll('.status-pill').forEach((pill) => {
        pill.addEventListener('click', () => {
          document.querySelectorAll('.status-pill').forEach((p) => p.classList.remove('active'));
          pill.classList.add('active');
          filterStatus = pill.getAttribute('data-status');
          renderChecklist();
        });
      });

      // Clear all filters
      document.getElementById('reset-filters-btn').addEventListener('click', () => {
        filterSearch = '';
        filterRealm = '';
        filterCategory = '';
        filterStatus = 'all';
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        document.getElementById('realm-select').value = '';
        document.getElementById('category-select').value = '';
        document.querySelectorAll('.status-pill').forEach((p) => {
          p.classList.toggle('active', p.getAttribute('data-status') === 'all');
        });
        renderDashboard();
        renderChecklist();
      });

      // Sync Modal
      const syncModal = document.getElementById('sync-modal');
      const syncTextarea = document.getElementById('sync-code-textarea');

      document.getElementById('open-sync-btn').addEventListener('click', () => {
        syncTextarea.value = encodeSyncCode();
        syncModal.classList.add('open');
      });

      document.getElementById('close-sync-btn').addEventListener('click', () => {
        syncModal.classList.remove('open');
      });

      syncModal.addEventListener('click', (e) => {
        if (e.target === syncModal) syncModal.classList.remove('open');
      });

      document.getElementById('copy-code-btn').addEventListener('click', () => {
        syncTextarea.value = encodeSyncCode();
        syncTextarea.select();
        navigator.clipboard?.writeText(syncTextarea.value);
        showToast('Sync code copied to clipboard!');
      });

      document.getElementById('load-code-btn').addEventListener('click', () => {
        try {
          const newSet = decodeSyncCode(syncTextarea.value);
          foundSet = newSet;
          saveProgress();
          renderDashboard();
          renderChecklist();
          showToast(`Loaded progress (${foundSet.size} / ${CHECKLIST_DATA.length} found)!`);
          syncModal.classList.remove('open');
        } catch (err) {
          alert('Invalid sync code. Make sure you copied the full code starting with GOWR1:');
        }
      });

      // Export JSON
      document.getElementById('export-json-btn').addEventListener('click', () => {
        const payload = {
          app: 'gow-ragnarok-100-checklist',
          exportedAt: new Date().toISOString(),
          foundCount: foundSet.size,
          totalCount: CHECKLIST_DATA.length,
          foundIds: Array.from(foundSet),
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gow-ragnarok-progress-${foundSet.size}of${CHECKLIST_DATA.length}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Progress JSON exported!');
      });

      // Import JSON
      document.getElementById('import-json-input').addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const data = JSON.parse(reader.result);
            const list = Array.isArray(data) ? data : data.foundIds;
            if (!Array.isArray(list)) throw new Error('Invalid JSON structure');
            foundSet = new Set(list.map(String));
            saveProgress();
            renderDashboard();
            renderChecklist();
            syncTextarea.value = encodeSyncCode();
            showToast(`Imported ${foundSet.size} found items!`);
            syncModal.classList.remove('open');
          } catch (err) {
            alert('Could not read JSON backup file.');
          }
        };
        reader.readAsText(file);
        e.target.value = '';
      });

      // Export CSV
      document.getElementById('export-csv-btn').addEventListener('click', () => {
        const headers = ['Found', 'ID', 'Name', 'Category', 'Realm', 'Info', 'MapGenie URL'];
        const rows = CHECKLIST_DATA.map((item) => {
          const isFound = foundSet.has(String(item.id)) ? 'TRUE' : 'FALSE';
          return [
            isFound,
            item.id,
            item.name,
            item.category,
            item.realm,
            item.infoText,
            item.mapUrl,
          ]
            .map((val) => `"${String(val || '').replace(/"/g, '""')}"`)
            .join(',');
        });
        const csvContent = '\\uFEFF' + [headers.join(','), ...rows].join('\\r\\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'GoW_Ragnarok_100Percent_Checklist.csv';
        a.click();
        URL.revokeObjectURL(url);
        showToast('CSV exported for Excel / Sheets!');
      });

      // Restore initial 91 found items
      document.getElementById('restore-initial-btn').addEventListener('click', () => {
        if (!confirm('Restore progress to the initial 91 found items from your original HTML file?')) return;
        foundSet = new Set(
          CHECKLIST_DATA.filter((item) => item.initialFound).map((item) => String(item.id))
        );
        saveProgress();
        renderDashboard();
        renderChecklist();
        syncTextarea.value = encodeSyncCode();
        showToast('Restored to initial 91 found items.');
      });

      // Reset to 0%
      document.getElementById('reset-zero-btn').addEventListener('click', () => {
        if (!confirm('Are you sure you want to uncheck all 496 items (0% progress)?')) return;
        foundSet = new Set();
        saveProgress();
        renderDashboard();
        renderChecklist();
        syncTextarea.value = encodeSyncCode();
        showToast('All items unchecked (0%).');
      });

      // Re-render if window crosses mobile/desktop threshold in Auto mode
      let lastIsTable = isDesktopTableActive();
      window.addEventListener('resize', () => {
        if (viewMode === 'auto') {
          const nowIsTable = isDesktopTableActive();
          if (nowIsTable !== lastIsTable) {
            lastIsTable = nowIsTable;
            renderChecklist();
          }
        }
      });
    });
  </script>
</body>
</html>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    items = parse_checklist(SOURCE_HTML)
    found_count = sum(1 for x in items if x["initialFound"])
    realms = sorted({x["realm"] for x in items})
    categories = sorted({x["category"] for x in items})

    print(f"Extracted {len(items)} items ({found_count} marked found).")
    print(f"Realms ({len(realms)}): {realms}")
    print(f"Categories ({len(categories)}): {categories}")

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    compact_json = json.dumps(items, ensure_ascii=False)
    html_out = HTML_TEMPLATE.replace("__CHECKLIST_JSON__", compact_json)

    with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Successfully generated:\n  - {DATA_JSON_PATH}\n  - {INDEX_HTML_PATH}")


if __name__ == "__main__":
    main()

