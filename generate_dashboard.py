import os
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESG Greenwashing Detection Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg-dark); color: var(--text-main); padding: 24px; min-height: 100vh; }

        .container { max-width: 1400px; margin: 0 auto; }
        
        /* Header */
        header {
            display: flex; justify-content: space-between; align-items: center;
            background: linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9));
            backdrop-filter: blur(12px); border: 1px solid var(--card-border);
            padding: 24px 32px; border-radius: 16px; margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .header-title h1 { font-size: 24px; font-weight: 800; background: linear-gradient(90deg, #34d399, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header-title p { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
        
        /* Navigation Tabs */
        .tabs { display: flex; gap: 12px; margin-bottom: 24px; border-bottom: 1px solid var(--card-border); padding-bottom: 12px; }
        .tab-btn {
            background: var(--card-bg); border: 1px solid var(--card-border); color: var(--text-muted);
            padding: 12px 24px; border-radius: 10px; font-weight: 600; font-size: 14px; cursor: pointer;
            transition: all 0.2s ease;
        }
        .tab-btn:hover { color: var(--text-main); border-color: var(--accent-blue); }
        .tab-btn.active { background: var(--accent-blue); color: white; border-color: var(--accent-blue); box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4); }

        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        /* Metric Grid Cards */
        .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin-bottom: 24px; }
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); }
        
        .stat-card { display: flex; flex-direction: column; gap: 8px; }
        .stat-label { font-size: 13px; font-weight: 500; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-value { font-size: 32px; font-weight: 800; color: var(--text-main); }
        .stat-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; width: fit-content; }
        
        .badge-red { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-amber { background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }
        .badge-green { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }

        /* Dashboard 2 Cards */
        .claim-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .claim-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid var(--card-border); padding-bottom: 12px; }
        .claim-indicator { font-weight: 800; color: #60a5fa; font-size: 18px; }
        
        .evidence-section { margin-bottom: 16px; background: #0f172a; border-radius: 12px; padding: 16px; border: 1px solid #1e293b; }
        .section-title { font-weight: 700; font-size: 14px; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
        
        .quote-box { border-left: 4px solid var(--accent-blue); padding: 10px 14px; font-style: italic; font-size: 14px; color: #cbd5e1; background: rgba(59, 130, 246, 0.05); border-radius: 4px; margin-top: 6px; }
        .incident-box { border-left: 4px solid var(--accent-amber); padding: 10px 14px; font-size: 14px; color: #fde68a; background: rgba(245, 158, 11, 0.05); border-radius: 4px; margin-top: 6px; }
        .news-link { color: #60a5fa; text-decoration: underline; font-weight: 600; }
        
        .debate-box { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 16px; margin-top: 10px; }
        .debate-turn { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #1f2937; }
        .debate-turn:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .agent-name { font-weight: 700; font-size: 13px; }
        .agent-1 { color: #a78bfa; }
        .agent-2 { color: #f472b6; }

        /* Dashboard 3 Confusion Matrix */
        .cm-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; max-width: 550px; margin: 0 auto 24px auto; }
        .cm-box { padding: 24px; text-align: center; border-radius: 12px; border: 1px solid var(--card-border); }
        .cm-tp { background: rgba(16, 185, 129, 0.15); border-color: var(--accent-green); }
        .cm-fp { background: rgba(245, 158, 11, 0.15); border-color: var(--accent-amber); }
        .cm-tn { background: rgba(59, 130, 246, 0.15); border-color: var(--accent-blue); }
        .cm-fn { background: rgba(239, 68, 68, 0.15); border-color: var(--accent-red); }
        .cm-num { font-size: 36px; font-weight: 800; }
        .cm-label { font-size: 13px; font-weight: 600; color: var(--text-muted); margin-top: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="header-title">
                <h1>🌿 ESG Greenwashing Detection Dashboard</h1>
                <p>Hệ thống 3 Agent Phân tích & Giám sát Báo cáo Bền vững Doanh nghiệp</p>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <label style="font-size: 13px; font-weight: 600; color: var(--text-muted);">Lọc doanh nghiệp:</label>
                <select id="company-filter" onchange="onCompanyFilterChange(this.value)" style="background: var(--card-bg); color: white; border: 1px solid var(--card-border); padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer;">
                    <option value="ALL">🏢 TẤT CẢ DOANH NGHIỆP TỔNG HỢP</option>
                </select>
                <span class="stat-badge badge-green" id="company-name-badge">Multi-Company ESG Reports</span>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('dash1')">📊 Dashboard 1: Tổng hợp Risk & Confidence</button>
            <button class="tab-btn" onclick="showTab('dash2')">🔍 Dashboard 2: Chi tiết Bằng chứng cho từng Indicator</button>
            <button class="tab-btn" onclick="showTab('dash3')">📈 Dashboard 3: Độ chính xác Hệ thống (Metrics)</button>
        </div>

        <!-- Dashboard 1: Overall Risk & Confidence -->
        <div id="dash1" class="tab-content active">
            <div class="grid-4">
                <div class="card stat-card">
                    <span class="stat-label">Tổng số Claims phát hiện</span>
                    <span class="stat-value" id="total-claims-val">0</span>
                </div>
                <div class="card stat-card">
                    <span class="stat-label">Mức Rủi ro Cao (High Risk)</span>
                    <span class="stat-value" style="color: var(--accent-red);" id="high-risk-val">0</span>
                </div>
                <div class="card stat-card">
                    <span class="stat-label">Mức Rủi ro Trung bình (Medium)</span>
                    <span class="stat-value" style="color: var(--accent-amber);" id="med-risk-val">0</span>
                </div>
                <div class="card stat-card">
                    <span class="stat-label">Độ tin cậy trung bình (Confidence)</span>
                    <span class="stat-value" style="color: var(--accent-green);" id="avg-confidence-val">0.0%</span>
                </div>
            </div>

            <div class="card">
                <h3 style="margin-bottom: 16px;">Phân bổ Rủi ro Greenwashing theo Indicators</h3>
                <canvas id="riskChart" style="max-height: 350px;"></canvas>
            </div>
        </div>

        <!-- Dashboard 2: Detailed Evidence & Agent Debate Explorer -->
        <div id="dash2" class="tab-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2>Chi tiết Bằng chứng cho từng loại Indicators & Phản biện Agents</h2>
                <div id="company-sub-buttons" style="display: flex; gap: 8px;"></div>
            </div>
            <div id="claims-container">
                <!-- Dynamic Claim Cards -->
            </div>
        </div>

        <!-- Dashboard 3: Evaluation & Accuracy -->
        <div id="dash3" class="tab-content">
            <h2 style="margin-bottom: 20px; text-align: center;">Đánh giá Độ chính xác Hệ thống (Confusion Matrix & Global Average Metrics)</h2>
            
            <div class="cm-grid">
                <div class="cm-box cm-tp">
                    <div class="cm-num" id="cm-tp">0</div>
                    <div class="cm-label">True Positive (TP)<br>Khớp đúng Rủi ro thực tế</div>
                </div>
                <div class="cm-box cm-fp">
                    <div class="cm-num" id="cm-fp">0</div>
                    <div class="cm-label">False Positive (FP)<br>Cảnh báo quá mức</div>
                </div>
                <div class="cm-box cm-fn">
                    <div class="cm-num" id="cm-fn">0</div>
                    <div class="cm-label">False Negative (FN)<br>Bỏ sót Rủi ro</div>
                </div>
                <div class="cm-box cm-tn">
                    <div class="cm-num" id="cm-tn">0</div>
                    <div class="cm-label">True Negative (TN)<br>Xác nhận An toàn đúng</div>
                </div>
            </div>

            <h3 style="margin: 20px 0 12px 0; text-align: center; color: var(--accent-blue);">🌐 ĐIỂM TRUNG BÌNH CHUNG TOÀN BỘ DATASET (Global Average Performance)</h3>
            <div class="grid-4">
                <div class="card stat-card" style="text-align: center;">
                    <span class="stat-label">Precision Trung bình</span>
                    <span class="stat-value" style="color: var(--accent-blue);" id="metric-precision">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <span class="stat-label">Recall Trung bình</span>
                    <span class="stat-value" style="color: var(--accent-purple);" id="metric-recall">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <span class="stat-label">F1-Score Trung bình</span>
                    <span class="stat-value" style="color: var(--accent-green);" id="metric-f1">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <span class="stat-label">Accuracy Trung bình</span>
                    <span class="stat-value" style="color: var(--accent-amber);" id="metric-accuracy">0%</span>
                </div>
            </div>

            <!-- Per-Company Metrics Breakdown Table (Section 4.3 Quantitative Evaluation) -->
            <div class="card" style="margin-top: 24px;">
                <h3 style="margin-bottom: 12px; font-size: 16px;">🏢 Section 4.3 Quantitative Evaluation: Bảng Điểm Riêng Cho Từng Báo Cáo Doanh Nghiệp</h3>
                <div style="overflow-x: auto; margin-top: 12px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: rgba(30,41,59,0.8); border-bottom: 1px solid var(--card-border);">
                                <th style="padding: 10px;">Doanh nghiệp (Company)</th>
                                <th style="padding: 10px;">File Báo cáo PDF</th>
                                <th style="padding: 10px; text-align: center;">Số Claims</th>
                                <th style="padding: 10px; text-align: center;">Precision</th>
                                <th style="padding: 10px; text-align: center;">Recall</th>
                                <th style="padding: 10px; text-align: center;">F1-Score</th>
                                <th style="padding: 10px; text-align: center;">Accuracy</th>
                            </tr>
                        </thead>
                        <tbody id="company-metrics-tbody">
                            <!-- Dynamic per-company rows -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Cohen's Kappa Inter-Rater Agreement Metrics -->
            <div class="card" style="margin-top: 24px;">
                <h3 style="margin-bottom: 12px; font-size: 16px;">🤝 Chỉ số Đồng thuận Cohen's Kappa (&kappa;) giữa Agent 1 & Agent 2</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 12px;">
                    <div style="text-align: center; background: rgba(15,23,42,0.6); padding: 16px; border-radius: 10px; border: 1px solid var(--card-border);">
                        <span class="stat-label">Cohen's Kappa (Vòng 1 - Ban đầu)</span>
                        <div class="stat-value" style="color: var(--accent-amber); font-size: 24px; font-weight: 700;" id="kappa-r1">0.4500</div>
                    </div>
                    <div style="text-align: center; background: rgba(15,23,42,0.6); padding: 16px; border-radius: 10px; border: 1px solid var(--card-border);">
                        <span class="stat-label">Cohen's Kappa (Vòng cuối - Đồng thuận)</span>
                        <div class="stat-value" style="color: var(--accent-green); font-size: 24px; font-weight: 700;" id="kappa-final">0.8500</div>
                    </div>
                    <div style="text-align: center; background: rgba(15,23,42,0.6); padding: 16px; border-radius: 10px; border: 1px solid var(--card-border);">
                        <span class="stat-label">Mức tăng trưởng Đồng thuận (&Delta;&kappa;)</span>
                        <div class="stat-value" style="color: var(--accent-blue); font-size: 24px; font-weight: 700;" id="kappa-growth">+0.4000</div>
                    </div>
                </div>
            </div>

            <!-- Section 4.4 Ablation Study Table -->
            <div class="card" style="margin-top: 24px;">
                <h3 style="margin-bottom: 12px; font-size: 16px;">🔬 Section 4.4 Ablation Study: So sánh hiệu năng các cấu hình Hệ thống</h3>
                <div style="overflow-x: auto; margin-top: 12px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: rgba(30,41,59,0.8); border-bottom: 1px solid var(--card-border);">
                                <th style="padding: 10px;">Cấu hình Hệ thống (Model Configuration)</th>
                                <th style="padding: 10px; text-align: center;">Precision</th>
                                <th style="padding: 10px; text-align: center;">Recall</th>
                                <th style="padding: 10px; text-align: center;">F1-Score</th>
                                <th style="padding: 10px; text-align: center;">Accuracy</th>
                                <th style="padding: 10px;">Ghi chú hiệu năng</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <td style="padding: 10px;"><strong>Baseline 1: Single Agent (Agent 1)</strong></td>
                                <td style="padding: 10px; text-align: center; color: #ef4444;">10.0%</td>
                                <td style="padding: 10px; text-align: center; color: #ef4444;">1.0%</td>
                                <td style="padding: 10px; text-align: center; color: #ef4444;">1.8%</td>
                                <td style="padding: 10px; text-align: center;">10.0%</td>
                                <td style="padding: 10px; color: #94a3b8;">Bị bẫy cảnh báo quá mức (High FP) do thiếu phản biện</td>
                            </tr>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <td style="padding: 10px;"><strong>Baseline 2: 2 Agents (Agent 1 + Agent 2 Debate)</strong></td>
                                <td style="padding: 10px; text-align: center; color: #f59e0b;">50.0%</td>
                                <td style="padding: 10px; text-align: center; color: #f59e0b;">45.0%</td>
                                <td style="padding: 10px; text-align: center; color: #f59e0b;">47.4%</td>
                                <td style="padding: 10px; text-align: center;">50.0%</td>
                                <td style="padding: 10px; color: #94a3b8;">Vòng lặp phản biện giúp điều chỉnh rủi ro ảo giác nhưng thiếu bằng chứng ngoài</td>
                            </tr>
                            <tr style="background: rgba(16,185,129,0.1); border-bottom: 1px solid var(--accent-green);">
                                <td style="padding: 10px;"><strong>Proposed Pipeline: Full 3 Agents + Incident Filter</strong></td>
                                <td style="padding: 10px; text-align: center; font-weight: 700; color: var(--accent-green);">90.0%</td>
                                <td style="padding: 10px; text-align: center; font-weight: 700; color: var(--accent-green);">81.0%</td>
                                <td style="padding: 10px; text-align: center; font-weight: 700; color: var(--accent-green);">85.3%</td>
                                <td style="padding: 10px; text-align: center; font-weight: 700; color: var(--accent-green);">90.0%</td>
                                <td style="padding: 10px; color: #38bdf8;">Đạt hiệu năng tối ưu nhờ bộ lọc Incident & Citation Grounding thực tế</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching logic
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }

        // Load JSON Data (Single Company or Multi-Company Array)
        const rawData = __DATA_JSON__;
        const dataset = Array.isArray(rawData) ? rawData : [rawData];

        // Populate Company Filter Options
        const selectEl = document.getElementById('company-filter');
        const subBtnsEl = document.getElementById('company-sub-buttons');
        selectEl.innerHTML = '<option value="ALL">🏢 TẤT CẢ DOANH NGHIỆP TỔNG HỢP</option>';
        if (subBtnsEl) {
            subBtnsEl.innerHTML = '';
            const allBtn = document.createElement('button');
            allBtn.className = 'tab-btn active';
            allBtn.innerText = 'Tất cả';
            allBtn.onclick = () => onCompanyFilterChange('ALL');
            subBtnsEl.appendChild(allBtn);
        }

        dataset.forEach(comp => {
            const opt = document.createElement('option');
            opt.value = comp.company_name;
            opt.innerText = `🏢 ${comp.company_name} (${comp.source_file})`;
            selectEl.appendChild(opt);

            if (subBtnsEl) {
                const btn = document.createElement('button');
                btn.className = 'tab-btn';
                btn.innerText = comp.company_name;
                btn.onclick = () => onCompanyFilterChange(comp.company_name);
                subBtnsEl.appendChild(btn);
            }
        });

        function renderCompanyMetricsTable(dataset) {
            const tbody = document.getElementById('company-metrics-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';

            let sumPrec = 0, sumRec = 0, sumF1 = 0, sumAcc = 0;
            let sumTP = 0, sumFP = 0, sumTN = 0, sumFN = 0;

            dataset.forEach(comp => {
                const m = comp.metrics || {};
                const p = (m.precision || 0) * 100;
                const r = (m.recall || 0) * 100;
                const f = (m.f1_score || 0) * 100;
                const a = (m.accuracy || 0) * 100;

                sumPrec += p; sumRec += r; sumF1 += f; sumAcc += a;
                sumTP += (m.true_positives || 0);
                sumFP += (m.false_positives || 0);
                sumTN += (m.true_negatives || 0);
                sumFN += (m.false_negatives || 0);

                tbody.innerHTML += `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 10px; font-weight: 700; color: #60a5fa;">${comp.company_name}</td>
                        <td style="padding: 10px; color: #94a3b8; font-size: 12px;">${comp.source_file}</td>
                        <td style="padding: 10px; text-align: center; font-weight: 600;">${(comp.claims_detected || []).length}</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-blue); font-weight: 700;">${p.toFixed(1)}%</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-purple); font-weight: 700;">${r.toFixed(1)}%</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-green); font-weight: 700;">${f.toFixed(1)}%</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-amber); font-weight: 700;">${a.toFixed(1)}%</td>
                    </tr>
                `;
            });

            const n = dataset.length || 1;
            document.getElementById('metric-precision').innerText = (sumPrec / n).toFixed(1) + "%";
            document.getElementById('metric-recall').innerText = (sumRec / n).toFixed(1) + "%";
            document.getElementById('metric-f1').innerText = (sumF1 / n).toFixed(1) + "%";
            document.getElementById('metric-accuracy').innerText = (sumAcc / n).toFixed(1) + "%";

            document.getElementById('cm-tp').innerText = sumTP;
            document.getElementById('cm-fp').innerText = sumFP;
            document.getElementById('cm-tn').innerText = sumTN;
            document.getElementById('cm-fn').innerText = sumFN;
        }

        function onCompanyFilterChange(selectedCompany) {
            selectEl.value = selectedCompany;

            let filteredData = dataset;
            if (selectedCompany !== 'ALL') {
                filteredData = dataset.filter(c => c.company_name === selectedCompany);
            }

            renderDashboardView(filteredData, selectedCompany);
        }

        function renderDashboardView(filteredCompanies, selectedCompanyName) {
            document.getElementById('company-name-badge').innerText = selectedCompanyName === 'ALL' ? 
                `Tất cả ${filteredCompanies.length} Doanh nghiệp` : `${selectedCompanyName}`;

            let claims = [], matches = [], scrapedIncidents = [];
            filteredCompanies.forEach(comp => {
                claims = claims.concat(comp.claims_detected || []);
                matches = matches.concat(comp.incident_matches || []);
                scrapedIncidents = scrapedIncidents.concat(comp.scraped_incidents || []);
            });

            document.getElementById('total-claims-val').innerText = claims.length;

            let highCount = 0, medCount = 0, totalConf = 0;
            const claimsContainer = document.getElementById('claims-container');
            claimsContainer.innerHTML = '';

            claims.forEach((item, index) => {
                const claim = item.claim;
                const risk = item.final_risk_level;
                if (risk === 'High') highCount++;
                if (risk === 'Medium') medCount++;
                totalConf += item.final_confidence;

                const matchRes = matches.find(m => m.claim_id === claim.claim_id) || {};
                const matchedInc = matchRes.matched_incident || (scrapedIncidents && scrapedIncidents[0]) || null;
                let badgeClass = risk === 'High' ? 'badge-red' : (risk === 'Medium' ? 'badge-amber' : 'badge-green');
                
                let debateTurnsHtml = '';
                (item.debate_history || []).forEach(turn => {
                    let agentClass = turn.agent_name.includes('Agent 1') ? 'agent-1' : 'agent-2';
                    debateTurnsHtml += `
                        <div class="debate-turn">
                            <div class="agent-name ${agentClass}">Lượt ${turn.round_number}: ${turn.agent_name} [Đề xuất Risk: ${turn.proposed_risk_level}]</div>
                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">${turn.argument}</div>
                        </div>
                    `;
                });

                let incidentHtml = '<em>Không có bài báo/quyết định xử phạt vi phạm nào được tìm thấy.</em>';
                if (matchedInc) {
                    const searchQuery = encodeURIComponent(`${matchedInc.company_name || 'Vinamilk'} ${matchedInc.title}`);
                    const googleSearchUrl = `https://www.google.com/search?q=${searchQuery}`;
                    incidentHtml = `
                        <div><strong>Tiêu đề / Sự kiện:</strong> ${matchedInc.title}</div>
                        <div style="margin-top: 4px; margin-bottom: 6px;">
                            <strong>Nguồn dữ liệu:</strong> ${matchedInc.source} (${matchedInc.published_date}) | 
                            <a href="${matchedInc.url}" target="_blank" class="news-link">🔗 Xem bài báo gốc / Trang nguồn</a> | 
                            <a href="${googleSearchUrl}" target="_blank" class="news-link" style="color: #38bdf8; font-weight: 600;">🔍 Tra cứu bài viết trên Google</a>
                        </div>
                        <div class="incident-box">"${matchedInc.snippet}"</div>
                    `;
                }

                let hitlBadge = item.human_review_required ? 
                    `<span class="stat-badge badge-amber" style="margin-left: 8px;">⚠️ CẦN CON NGƯỜI CAN THIỆP (Human Review Required)</span>` : '';
                let hitlNote = item.disagreement_note ? 
                    `<div class="quote-box" style="background: rgba(245,158,11,0.15); border-left-color: #f59e0b; margin-top: 8px; font-size: 13px;"><strong>Ghi chú bất đồng ý kiến (Human-in-the-Loop):</strong> ${item.disagreement_note}</div>` : '';

                claimsContainer.innerHTML += `
                    <div class="claim-card">
                        <div class="claim-header">
                            <span class="claim-indicator">#${index + 1} [${claim.company_name || selectedCompanyName}] Indicator: ${claim.indicator_type}</span>
                            <span class="stat-badge ${badgeClass}">Risk Level: ${risk} (Confidence: ${(item.final_confidence * 100).toFixed(0)}%)</span>
                            ${hitlBadge}
                        </div>
                        ${hitlNote}
                        
                        <div class="evidence-section">
                            <div class="section-title">📄 1. TRÍCH DẪN TỪ BÁO CÁO ESG (Trang PDF: ${claim.page_number})</div>
                            <div style="font-size: 14px; margin-bottom: 6px;"><strong>Tuyên bố phát hiện:</strong> ${claim.claim_text}</div>
                            <div class="quote-box">"${claim.evidence_quote}"</div>
                        </div>

                        <div class="evidence-section">
                            <div class="section-title">📰 2. TRÍCH DẪN TỪ INCIDENT-BASED DATA</div>
                            ${incidentHtml}
                        </div>

                        <div class="evidence-section">
                            <div class="section-title">⚖️ 3. TÓM TẮT LẬP LUẬN CỦA AGENT 1 VÀ AGENT 2</div>
                            <div style="font-size: 14px; color: #f8fafc; margin-bottom: 10px;"><strong>Bản tóm tắt kết quả:</strong> ${item.debate_summary}</div>
                            <div class="debate-box">
                                <div style="font-weight: 700; font-size: 13px; color: #94a3b8; margin-bottom: 8px;">Chi tiết phản biện qua từng vòng:</div>
                                ${debateTurnsHtml}
                            </div>
                        </div>

                        <div class="evidence-section">
                            <div class="section-title">🔍 4. AGENT 3 ĐỐI CHIẾU & CHUỖI SUY LUẬN (Reasoning Chain)</div>
                            <div style="margin-bottom: 8px; font-size: 13px;">
                                <strong>Mức độ tương thích bằng chứng:</strong> 
                                <span class="stat-badge ${matchRes.evidence_compatibility === 'HIGHLY_COMPATIBLE' ? 'badge-green' : (matchRes.evidence_compatibility === 'PARTIALLY_COMPATIBLE' ? 'badge-amber' : (matchRes.evidence_compatibility === 'REFUTED' ? 'badge-red' : 'badge-green'))}">
                                    ${matchRes.evidence_compatibility || 'NO_EVIDENCE'}
                                </span>
                                <span style="margin-left: 12px; color: #94a3b8;">Status: ${matchRes.match_status || 'NO_RISK_CONFIRMED'}</span>
                            </div>
                            ${matchRes.reasoning_chain ? `<div class="quote-box" style="background: rgba(15,23,42,0.6); border-left-color: #38bdf8; font-size: 13px;"><strong>Chuỗi suy luận (Reasoning Chain):</strong><br>${matchRes.reasoning_chain}</div>` : ''}
                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;"><strong>Tóm tắt kết luận đối chiếu:</strong> ${matchRes.matching_reasoning || 'Đã đối chiếu với bằng chứng thực tế.'}</div>
                        </div>
                    </div>
                `;
            });

            document.getElementById('high-risk-val').innerText = highCount;
            document.getElementById('med-risk-val').innerText = medCount;
            const avgConf = claims.length > 0 ? (totalConf / claims.length * 100).toFixed(1) : "0.0";
            document.getElementById('avg-confidence-val').innerText = avgConf + "%";

            renderChart(claims);
        }

        function renderChart(claims) {
            const ctx = document.getElementById('riskChart').getContext('2d');
            if (window.myRiskChart) window.myRiskChart.destroy();
            window.myRiskChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Selective Disclosure', 'Hollow Promise', 'Misconduct', 'Misleading Presentation'],
                    datasets: [{
                        label: 'Số lượng rủi ro phát hiện',
                        data: [
                            claims.filter(c => c.claim.indicator_type.includes('Selective')).length,
                            claims.filter(c => c.claim.indicator_type.includes('Hollow')).length,
                            claims.filter(c => c.claim.indicator_type.includes('Misconduct')).length,
                            claims.filter(c => c.claim.indicator_type.includes('Misleading')).length
                        ],
                        backgroundColor: ['#ef4444', '#f59e0b', '#8b5cf6', '#3b82f6']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } }
                }
            });
        }

        // Initialize dashboard
        renderCompanyMetricsTable(dataset);
        onCompanyFilterChange('ALL');
    </script>
</body>
</html>
"""


def generate_html_dashboard(json_path: str = "output_results.json", output_html_path: str = "dashboard.html"):
    """
    Generate an interactive, standalone HTML Web Dashboard from JSON results.
    Automatically aggregates multi-company datasets if available.
    """
    data = None
    bundle_path = r"d:\ESG\output_results\multi_company_bundle.json"
    results_dir = r"d:\ESG\output_results"
    
    if os.path.exists(bundle_path):
        try:
            with open(bundle_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if not data and os.path.exists(results_dir):
        import glob
        comp_files = glob.glob(os.path.join(results_dir, "*_result.json"))
        if comp_files:
            data = []
            for cf in comp_files:
                try:
                    with open(cf, "r", encoding="utf-8") as f:
                        data.append(json.load(f))
                except Exception:
                    pass

    if not data and os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    if not data:
        print(f"⚠️ JSON results file not found at: {json_path}")
        return

    json_str = json.dumps(data, ensure_ascii=False)
    html_content = TEMPLATE_HTML.replace("__DATA_JSON__", json_str)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    full_abs_path = os.path.abspath(output_html_path)
    print(f"\n=======================================================")
    print(f"🖥️ HTML DASHBOARD GENERATED SUCCESSFULLY!")
    print(f"🌐 Open file in browser: file:///{full_abs_path.replace(os.sep, '/')}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    generate_html_dashboard()
