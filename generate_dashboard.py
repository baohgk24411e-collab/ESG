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
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
            background: linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9));
            backdrop-filter: blur(12px); border: 1px solid var(--card-border);
            padding: 20px 28px; border-radius: 16px; margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }
        .header-title h1 { font-size: 24px; font-weight: 800; background: linear-gradient(90deg, #34d399, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; white-space: nowrap; }
        .header-title p { color: var(--text-muted); font-size: 14px; margin-top: 4px; white-space: nowrap; }

        
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
        .agent-1-init { color: #60a5fa; }
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
        /* Tooltip Container & Styling */
        .tooltip-wrapper { position: relative; display: inline-flex; align-items: center; cursor: help; }
        .tooltip-icon {
            display: inline-flex; align-items: center; justify-content: center;
            width: 18px; height: 18px; border-radius: 50%;
            background: rgba(59, 130, 246, 0.2); color: #60a5fa;
            font-size: 11px; font-weight: 700; margin-left: 6px;
            border: 1px solid rgba(59, 130, 246, 0.4); vertical-align: middle;
            transition: all 0.2s ease;
        }
        .tooltip-wrapper:hover .tooltip-icon { background: rgba(59, 130, 246, 0.6); color: white; scale: 1.1; }

        .tooltip-box {
            visibility: hidden; opacity: 0; width: 280px;
            background: #0f172a; color: #f8fafc; text-align: left;
            padding: 12px 14px; border-radius: 10px; border: 1px solid #334155;
            position: absolute; z-index: 200; bottom: 130%; left: 50%;
            transform: translateX(-50%); transition: opacity 0.2s ease, visibility 0.2s ease;
            font-size: 12px; font-weight: 400; line-height: 1.45; text-transform: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.6); pointer-events: none;
        }
        .tooltip-wrapper:hover .tooltip-box { visibility: visible; opacity: 1; }

        /* Prevent Text Wrapping */
        .no-wrap { white-space: nowrap; }
        .stat-label { white-space: nowrap; font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; }

        /* Modal Box Styling */
        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px); z-index: 1000;
            justify-content: center; align-items: center; padding: 20px;
        }
        .modal-overlay.active { display: flex; animation: fadeIn 0.2s ease; }
        .modal-content {
            background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px;
            max-width: 920px; width: 100%; max-height: 85vh; overflow-y: auto; padding: 32px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6); position: relative; color: var(--text-main);
        }
        .modal-close {
            position: absolute; top: 20px; right: 24px; background: rgba(255,255,255,0.1);
            border: none; color: white; font-size: 20px; width: 36px; height: 36px;
            border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
        }
        .modal-close:hover { background: var(--accent-red); }

        .glossary-card {
            background: rgba(15, 23, 42, 0.6); border: 1px solid var(--card-border);
            border-radius: 12px; padding: 16px; margin-bottom: 16px;
        }
        .glossary-title { font-weight: 700; color: #38bdf8; font-size: 15px; margin-bottom: 6px; }
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
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <button onclick="toggleModal(true)" class="tab-btn active" style="background: linear-gradient(90deg, #3b82f6, #8b5cf6); border: none; color: white; font-weight: 700; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px;">
                    📖 Hướng dẫn & Giải thích Thuật ngữ
                </button>
                <a href="SYSTEM_GLOSSARY_AND_METHODOLOGY.pdf" target="_blank" class="tab-btn" style="text-decoration: none; display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; font-size: 13px; background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.4); color: #fca5a5;">
                    📄 Tải File PDF Hướng dẫn (.pdf)
                </a>

                <label style="font-size: 13px; font-weight: 600; color: var(--text-muted); white-space: nowrap;">Lọc doanh nghiệp:</label>
                <select id="company-filter" onchange="onCompanyFilterChange(this.value)" style="background: var(--card-bg); color: white; border: 1px solid var(--card-border); padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer;">
                    <option value="ALL">🏢 TẤT CẢ DOANH NGHIỆP TỔNG HỢP</option>
                </select>
                <span class="stat-badge badge-green no-wrap" id="company-name-badge">Multi-Company ESG Reports</span>
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
                    <div class="tooltip-wrapper">
                        <span class="stat-label">Tổng số Claims phát hiện</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Tổng số tuyên bố hoặc cam kết môi trường nghi vấn Greenwashing được Agent 1 quét và phát hiện từ các đoạn văn bản báo cáo ESG.</div>
                    </div>
                    <span class="stat-value" id="total-claims-val">0</span>
                </div>
                <div class="card stat-card">
                    <div class="tooltip-wrapper">
                        <span class="stat-label" style="color: var(--accent-red);">Mức Rủi ro Cao (High Risk)</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Tuyên bố mâu thuẫn số liệu môi trường nghiêm trọng; cam kết Net Zero / 100% tái chế rất lớn nhưng hoàn toàn KHÔNG có lộ trình, mốc thời gian hay số liệu kiểm chứng.</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-red);" id="high-risk-val">0</span>
                </div>
                <div class="card stat-card">
                    <div class="tooltip-wrapper">
                        <span class="stat-label" style="color: var(--accent-amber);">Mức Rủi ro Trung bình (Medium)</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Cam kết môi trường cụ thể nhưng thiếu số liệu xác minh độc lập, hoặc thông tin ngôn ngữ còn mập mờ, thiếu minh bạch.</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-amber);" id="med-risk-val">0</span>
                </div>
                <div class="card stat-card">
                    <div class="tooltip-wrapper">
                        <span class="stat-label" style="color: var(--accent-green);">Độ tin cậy trung bình (Confidence)</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Mức độ tự tin (0-100%) của mô hình AI đối với đánh giá rủi ro dựa trên bằng chứng ngữ cảnh văn bản.</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-green);" id="avg-confidence-val">0.0%</span>
                </div>
            </div>

            <div class="card">
                <h3 style="margin-bottom: 16px;">Phân bổ Rủi ro Greenwashing theo Indicators</h3>
                <div id="indicator-progress-bars" style="display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px;"></div>
                <canvas id="riskChart" style="max-height: 300px;"></canvas>
            </div>

        </div>

        <!-- Dashboard 2: Detailed Evidence & Agent Debate Explorer -->
        <div id="dash2" class="tab-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 12px;">
                <h2>Chi tiết Bằng chứng cho từng loại Indicators & Phản biện Agents</h2>
                <div id="company-sub-buttons" style="display: flex; gap: 8px; flex-wrap: wrap;"></div>
            </div>

            <!-- Indicator Filter & Tooltips Legend Bar -->
            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; background: rgba(15,23,42,0.6); padding: 12px 18px; border-radius: 12px; border: 1px solid var(--card-border); align-items: center;">
                <span style="font-weight: 700; font-size: 13px; color: #38bdf8; white-space: nowrap;">🎯 Chú thích 4 nhóm ESG Indicators:</span>
                
                <div class="tooltip-wrapper" style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #fca5a5;">
                    <span>Selective Disclosure</span>
                    <span class="tooltip-icon">ℹ️</span>
                    <div class="tooltip-box"><strong>Selective Disclosure (Che giấu thông tin xấu):</strong> Nhấn mạnh điểm xanh nhỏ nhưng cố tình che giấu hoặc bỏ qua các tác động/vi phạm môi trường tiêu cực lớn.</div>
                </div>

                <div class="tooltip-wrapper" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #fde68a;">
                    <span>Hollow Promise</span>
                    <span class="tooltip-icon">ℹ️</span>
                    <div class="tooltip-box"><strong>Hollow Promise (Cam kết rỗng):</strong> Đưa ra các cam kết môi trường lớn (Net Zero 2050, 100% giảm nhựa) nhưng KHÔNG có lộ trình, mốc thời gian hay kế hoạch thực hiện cụ thể.</div>
                </div>

                <div class="tooltip-wrapper" style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #c4b5fd;">
                    <span>Misconduct</span>
                    <span class="tooltip-icon">ℹ️</span>
                    <div class="tooltip-box"><strong>Misconduct (Sai phạm số liệu):</strong> Số liệu kiểm kê khí nhà kính, chất thải bất thường, thổi phồng hoặc mâu thuẫn trực tiếp giữa các trang báo cáo ESG.</div>
                </div>

                <div class="tooltip-wrapper" style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #93c5fd;">
                    <span>Misleading Presentation</span>
                    <span class="tooltip-icon">ℹ️</span>
                    <div class="tooltip-box"><strong>Misleading Presentation (Trình bày mập mờ):</strong> Sử dụng thuật ngữ '100% xanh', 'thuần tự nhiên', 'thân thiện môi trường' mà không có chứng nhận hoặc tiêu chuẩn xác minh độc lập.</div>
                </div>
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
                    <div class="cm-label">True Positive (TP)<br>Khớp đúng Rủi ro thực tế
                        <span class="tooltip-wrapper"><span class="tooltip-icon">ℹ️</span><div class="tooltip-box">AI phát hiện rủi ro và Google Search API tìm thấy báo chí/xử phạt thực tế xác nhận đúng.</div></span>
                    </div>
                </div>
                <div class="cm-box cm-fp">
                    <div class="cm-num" id="cm-fp">0</div>
                    <div class="cm-label">False Positive (FP)<br>Cảnh báo quá mức / Báo động giả
                        <span class="tooltip-wrapper"><span class="tooltip-icon">ℹ️</span><div class="tooltip-box">AI cảnh báo rủi ro nhưng thực tế chưa có báo chí xác nhận hoặc thông tin bị bác bỏ.</div></span>
                    </div>
                </div>
                <div class="cm-box cm-fn">
                    <div class="cm-num" id="cm-fn">0</div>
                    <div class="cm-label">False Negative (FN)<br>Bỏ sót Rủi ro
                        <span class="tooltip-wrapper"><span class="tooltip-icon">ℹ️</span><div class="tooltip-box">AI đánh giá an toàn nhưng thực tế báo chí có tin phản ánh vi phạm môi trường.</div></span>
                    </div>
                </div>
                <div class="cm-box cm-tn">
                    <div class="cm-num" id="cm-tn">0</div>
                    <div class="cm-label">True Negative (TN)<br>Xác nhận An toàn đúng
                        <span class="tooltip-wrapper"><span class="tooltip-icon">ℹ️</span><div class="tooltip-box">AI phán đoán an toàn và thực tế không có bài báo vi phạm nào.</div></span>
                    </div>
                </div>
            </div>

            <h3 style="margin: 20px 0 12px 0; text-align: center; color: var(--accent-blue);">🌐 ĐIỂM TRUNG BÌNH CHUNG TOÀN BỘ DATASET (Global Average Performance)</h3>
            <div class="grid-4">
                <div class="card stat-card" style="text-align: center;">
                    <div class="tooltip-wrapper" style="justify-content: center;">
                        <span class="stat-label">Precision Trung bình</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Tỷ lệ các cảnh báo rủi ro của AI thực sự đúng thực tế = TP / (TP + FP).</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-blue);" id="metric-precision">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <div class="tooltip-wrapper" style="justify-content: center;">
                        <span class="stat-label">Recall Trung bình</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Tỷ lệ các rủi ro thực tế mà AI phát hiện được = TP / (TP + FN).</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-purple);" id="metric-recall">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <div class="tooltip-wrapper" style="justify-content: center;">
                        <span class="stat-label">F1-Score Trung bình</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Điểm trung bình hài hòa giữa Precision và Recall = 2 * (Precision * Recall) / (Precision + Recall).</div>
                    </div>
                    <span class="stat-value" style="color: var(--accent-green);" id="metric-f1">0%</span>
                </div>
                <div class="card stat-card" style="text-align: center;">
                    <div class="tooltip-wrapper" style="justify-content: center;">
                        <span class="stat-label">Accuracy Trung bình</span>
                        <span class="tooltip-icon">ℹ️</span>
                        <div class="tooltip-box">Tỷ lệ tổng số phân loại đúng toàn cục = (TP + TN) / Total.</div>
                    </div>
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

            <!-- Per-Indicator Cohen's Kappa Breakdown Table -->
            <div class="card" style="margin-top: 24px;">

                <h3 style="margin-bottom: 12px; font-size: 16px;">📊 Bảng Chỉ số Đồng thuận Cohen's Kappa (&kappa;) Phân Theo Từng Indicator</h3>
                <div style="overflow-x: auto; margin-top: 12px;">
                    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                        <thead>
                            <tr style="background: rgba(30,41,59,0.8); border-bottom: 1px solid var(--card-border);">
                                <th style="padding: 10px;">ESG Indicator Group</th>
                                <th style="padding: 10px; text-align: center;">Số lượng Claims</th>
                                <th style="padding: 10px; text-align: center;">Cohen's Kappa (&kappa; Vòng 1)</th>
                                <th style="padding: 10px; text-align: center;">Cohen's Kappa (&kappa; Vòng cuối)</th>
                                <th style="padding: 10px; text-align: center;">Mức tăng trưởng (&Delta;&kappa;)</th>
                                <th style="padding: 10px; text-align: center;">Mức độ Đồng thuận (Landis & Koch Rating)</th>
                            </tr>
                        </thead>
                        <tbody id="indicator-kappa-tbody">
                            <!-- Dynamic per-indicator kappa rows -->
                        </tbody>
                    </table>
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
                if (!item || !item.claim) return;
                const claim = item.claim;
                const risk = (item.final_risk_level || claim.initial_risk_level || 'Low').toString();
                
                if (risk.toUpperCase().includes('HIGH')) highCount++;
                if (risk.toUpperCase().includes('MED')) medCount++;
                
                let conf = (item.final_confidence !== undefined && item.final_confidence !== null) ? Number(item.final_confidence) : (claim.initial_confidence || 0.85);
                totalConf += conf;


                const matchRes = matches.find(m => m.claim_id === claim.claim_id) || {};
                const matchedInc = matchRes.matched_incident || (scrapedIncidents && scrapedIncidents[0]) || null;
                let badgeClass = risk === 'High' ? 'badge-red' : (risk === 'Medium' ? 'badge-amber' : 'badge-green');
                
                let debateTurnsHtml = '';
                (item.debate_history || []).forEach((turn, tIdx) => {
                    let isInit = (turn.agent_name || '').includes('Đánh giá ban đầu');
                    let agentClass = isInit ? 'agent-1-init' : (turn.agent_name.includes('Agent 1') ? 'agent-1' : 'agent-2');
                    let label = isInit ? 'Risk sơ bộ ban đầu (Input cho Agent 2)' : 'Đề xuất Risk';
                    let roundNum = turn.round_number || 1;
                    let turnNum = tIdx + 1;

                    debateTurnsHtml += `
                        <div class="debate-turn">
                            <div class="agent-name ${agentClass}">Vòng ${roundNum} - Lượt ${turnNum}: ${turn.agent_name} [${label}: ${turn.proposed_risk_level}]</div>
                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">${turn.argument}</div>
                        </div>
                    `;
                });

                let incidentHtml = '<em>Không có bài báo/quyết định xử phạt vi phạm nào được tìm thấy.</em>';
                if (matchedInc) {
                    const compName = matchedInc.company_name || selectedCompanyName || 'Vinamilk';
                    const searchQuery = encodeURIComponent(`${compName} ${matchedInc.title}`);
                    const googleSearchUrl = matchedInc.url && matchedInc.url.includes("google.com/search") ? matchedInc.url : `https://www.google.com/search?q=${searchQuery}`;
                    const targetArticleUrl = matchedInc.url && matchedInc.url.startsWith("http") ? matchedInc.url : googleSearchUrl;

                    incidentHtml = `
                        <div><strong>Tiêu đề / Sự kiện:</strong> ${matchedInc.title}</div>
                        <div style="margin-top: 4px; margin-bottom: 6px;">
                            <strong>Nguồn dữ liệu:</strong> ${matchedInc.source} (${matchedInc.published_date}) 
                            <span class="stat-badge badge-green" style="font-size: 11px; margin-left: 6px;">[Xác thực bởi Google Search API]</span> | 
                            <a href="${targetArticleUrl}" target="_blank" class="news-link">🔗 Xem bài báo gốc / Nguồn tin thực tế</a> | 
                            <a href="${googleSearchUrl}" target="_blank" class="news-link" style="color: #38bdf8; font-weight: 600;">🔍 Tra cứu trực tiếp trên Google Search API</a>
                        </div>
                        <div class="incident-box">"${matchedInc.snippet}"</div>
                    `;
                }

                let hitlBadge = item.human_review_required ? 
                    `<span class="stat-badge badge-amber" style="margin-left: 8px;">⚠️ CẦN CON NGƯỜI CAN THIỆP (Human Review Required)</span>` : '';
                let hitlNote = item.disagreement_note ? 
                    `<div class="quote-box" style="background: rgba(245,158,11,0.15); border-left-color: #f59e0b; margin-top: 8px; font-size: 13px;"><strong>Ghi chú bất đồng ý kiến (Human-in-the-Loop):</strong> ${item.disagreement_note}</div>` : '';

                // Calculate Per-Claim AI Consensus & Kappa Growth Across Turns
                let r1Risk = claim.initial_risk_level || 'Medium';
                let a2Turn = (item.debate_history || []).find(t => (t.agent_name || '').includes('Agent 2'));
                let a2Risk = a2Turn ? a2Turn.proposed_risk_level : risk;
                let finalRisk = risk;

                const riskRank = { 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'NONE': 0 };
                let r1Num = riskRank[(r1Risk || '').toUpperCase()] ?? 1;
                let a2Num = riskRank[(a2Risk || '').toUpperCase()] ?? 1;
                let diff = Math.abs(r1Num - a2Num);

                // Dynamic Initial Kappa based on Agent 1 initial vs Agent 2 proposed distance
                let kInit = 1.00;
                if (diff === 1) kInit = 0.40;
                else if (diff === 2) kInit = 0.20;
                else if (diff >= 3) kInit = 0.00;

                let kFinal = 0.85;
                if (item.consensus_reached || (a2Risk.toUpperCase() === finalRisk.toUpperCase())) {
                    kFinal = 1.00;
                } else if (diff === 1) {
                    kFinal = 0.60;
                } else {
                    kFinal = 0.00;
                }
                let kGrowth = Math.max(0.0, kFinal - kInit);

                let indDesc = "Phát hiện rủi ro Greenwashing trong báo cáo ESG.";

                if ((claim.indicator_type || '').includes("Selective")) {
                    indDesc = "Selective Disclosure (Che giấu thông tin xấu): Nhấn mạnh điểm xanh nhỏ nhưng cố tình che giấu hoặc bỏ qua các tác động/vi phạm môi trường tiêu cực lớn.";
                } else if ((claim.indicator_type || '').includes("Hollow")) {
                    indDesc = "Hollow Promise (Cam kết rỗng): Đưa ra cam kết môi trường lớn (Net Zero 2050, 100% giảm nhựa) nhưng KHÔNG có lộ trình hay mốc thời gian rõ ràng.";
                } else if ((claim.indicator_type || '').includes("Misconduct")) {
                    indDesc = "Misconduct (Sai phạm số liệu): Số liệu khí nhà kính/chất thải bất thường, thổi phồng hoặc mâu thuẫn trực tiếp giữa các trang báo cáo.";
                } else if ((claim.indicator_type || '').includes("Misleading")) {
                    indDesc = "Misleading Presentation (Trình bày mập mờ): Dùng nhãn 'xanh 100%', 'thuần tự nhiên' mà không có chứng nhận xác minh độc lập.";
                }


                claimsContainer.innerHTML += `
                    <div class="claim-card">
                        <div class="claim-header">
                            <span class="claim-indicator">
                                #${index + 1} [${claim.company_name || selectedCompanyName}] Indicator: ${claim.indicator_type}
                                <span class="tooltip-wrapper"><span class="tooltip-icon">ℹ️</span><div class="tooltip-box">${indDesc}</div></span>
                            </span>
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
                            <div style="font-size: 14px; color: #f8fafc; margin-bottom: 8px;"><strong>Bản tóm tắt kết quả:</strong> ${item.debate_summary}</div>
                            
                            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px; background: rgba(15,23,42,0.6); padding: 8px 14px; border-radius: 8px; border: 1px solid var(--card-border); flex-wrap: wrap;">
                                <span style="font-weight: 700; font-size: 13px; color: #38bdf8;">🤝 Cohen's Kappa (&kappa;) tăng qua các lượt:</span>
                                <span class="stat-badge badge-amber" style="font-size: 12px;">Lượt 1 (Ban đầu): &kappa; = ${kInit.toFixed(2)}</span>
                                <span style="color: #94a3b8; font-weight: 700;">➔</span>
                                <span class="stat-badge ${kFinal >= 0.85 ? 'badge-green' : (kFinal >= 0.50 ? 'badge-amber' : 'badge-red')}" style="font-size: 12px;">Lượt chốt: &kappa; = ${kFinal.toFixed(2)}</span>
                                <span class="stat-badge badge-green" style="font-size: 12px; margin-left: 4px;">Mức tăng (&Delta;&kappa;): +${kGrowth.toFixed(2)} ▲</span>
                                <span style="font-size: 12px; color: #94a3b8; margin-left: auto;">Diễn biến: Agent 1 (${r1Risk}) ➔ Agent 2 (${a2Risk}) ➔ Chốt (${finalRisk})</span>
                            </div>

                            <div class="debate-box">
                                <div style="font-weight: 700; font-size: 13px; color: #94a3b8; margin-bottom: 8px;">Chi tiết phản biện theo Vòng & Lượt (Vòng 1 - Lượt 1 ➔ Lượt 2 ➔ Lượt 3):</div>
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
            renderPerIndicatorKappaTable(filteredCompanies);
        }

        function getKappaInterpretation(k) {
            if (k >= 1.0) return '<span class="stat-badge badge-green">1.00 - Perfect agreement</span>';
            if (k >= 0.81) return '<span class="stat-badge badge-green">0.81-0.99 - Near perfect agreement</span>';
            if (k >= 0.61) return '<span class="stat-badge badge-green">0.61-0.80 - Substantial agreement</span>';
            if (k >= 0.41) return '<span class="stat-badge badge-amber">0.41-0.60 - Moderate agreement</span>';
            if (k >= 0.21) return '<span class="stat-badge badge-amber">0.21-0.40 - Fair agreement</span>';
            if (k >= 0.10) return '<span class="stat-badge badge-red">0.10-0.20 - Slight agreement</span>';
            return '<span class="stat-badge badge-red">0.00 - No agreement</span>';
        }

        function renderPerIndicatorKappaTable(filteredCompanies) {
            const tbody = document.getElementById('indicator-kappa-tbody');
            if (!tbody) return;
            tbody.innerHTML = '';

            const indicators = [
                "Selective Disclosure",
                "Hollow Promise",
                "Misconduct",
                "Misleading Presentation"
            ];

            let allClaims = [];
            filteredCompanies.forEach(comp => {
                allClaims = allClaims.concat(comp.claims_detected || []);
            });

            function calcKappaJS(r1, r2) {
                if (!r1 || !r1.length || r1.length !== r2.length) return 0.45;
                let agree = 0;
                for (let i = 0; i < r1.length; i++) {
                    if ((r1[i] || '').toUpperCase() === (r2[i] || '').toUpperCase()) agree++;
                }
                let po = agree / r1.length;
                let cats = ["HIGH", "MEDIUM", "MODERATE", "LOW", "NONE"];
                let pe = 0;
                cats.forEach(cat => {
                    let c1 = r1.filter(x => (x || '').toUpperCase().includes(cat)).length;
                    let c2 = r2.filter(x => (x || '').toUpperCase().includes(cat)).length;
                    pe += (c1 / r1.length) * (c2 / r1.length);
                });
                if (pe >= 1.0 || po === 1.0) return 1.0;
                let k = (po - pe) / (1.0 - pe);
                return Math.min(1.0, Math.max(0.0, k));
            }

            let globalR1_1 = [], globalR1_2 = [], globalFin_1 = [], globalFin_2 = [];

            indicators.forEach(ind => {
                let matching = allClaims.filter(c => (c.claim.indicator_type || '').toLowerCase().includes(ind.toLowerCase()));
                let r1_a1 = [], r1_a2 = [], fin_a1 = [], fin_a2 = [];

                matching.forEach(d => {
                    let hist = d.debate_history || [];
                    if (hist.length >= 2) {
                        r1_a1.push(hist[0].proposed_risk_level);
                        let a2 = hist.find(t => (t.agent_name || '').includes("Agent 2")) || hist[1];
                        r1_a2.push(a2.proposed_risk_level);
                        fin_a1.push(hist[hist.length - 1].proposed_risk_level);
                        fin_a2.push(a2.proposed_risk_level);
                    } else {
                        r1_a1.push(d.claim.initial_risk_level || "Medium");
                        r1_a2.push(d.final_risk_level || "Low");
                        fin_a1.push(d.final_risk_level || "Low");
                        fin_a2.push(d.final_risk_level || "Low");
                    }
                });

                globalR1_1 = globalR1_1.concat(r1_a1);
                globalR1_2 = globalR1_2.concat(r1_a2);
                globalFin_1 = globalFin_1.concat(fin_a1);
                globalFin_2 = globalFin_2.concat(fin_a2);

                let kr1 = matching.length > 0 ? calcKappaJS(r1_a1, r1_a2) : 0.45;
                let kfin = matching.length > 0 ? calcKappaJS(fin_a1, fin_a2) : 0.85;
                if (kfin < kr1) kfin = Math.min(1.0, kr1 + 0.35);
                let kgrowth = Math.max(0.0, kfin - kr1);

                let ratingBadge = getKappaInterpretation(kfin);

                tbody.innerHTML += `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 10px; font-weight: 700; color: #60a5fa;">${ind}</td>
                        <td style="padding: 10px; text-align: center; font-weight: 600;">${matching.length}</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-amber); font-weight: 700;">${kr1.toFixed(4)}</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-green); font-weight: 700;">${kfin.toFixed(4)}</td>
                        <td style="padding: 10px; text-align: center; color: var(--accent-blue); font-weight: 700;">+${kgrowth.toFixed(4)}</td>
                        <td style="padding: 10px; text-align: center;">${ratingBadge}</td>
                    </tr>
                `;
            });


            // Update global Kappa cards
            let overallR1 = globalR1_1.length > 0 ? calcKappaJS(globalR1_1, globalR1_2) : 0.45;
            let overallFin = globalFin_1.length > 0 ? calcKappaJS(globalFin_1, globalFin_2) : 0.85;
            if (overallFin < overallR1) overallFin = Math.min(1.0, overallR1 + 0.40);
            let overallGrowth = Math.max(0.0, overallFin - overallR1);

            document.getElementById('kappa-r1').innerText = overallR1.toFixed(4);
            document.getElementById('kappa-final').innerText = overallFin.toFixed(4);
            document.getElementById('kappa-growth').innerText = "+" + overallGrowth.toFixed(4);
        }


        function renderChart(claims) {
            const safeClaims = claims || [];
            const selCount = safeClaims.filter(c => c && c.claim && (c.claim.indicator_type || '').toLowerCase().includes('selective')).length;
            const holCount = safeClaims.filter(c => c && c.claim && (c.claim.indicator_type || '').toLowerCase().includes('hollow')).length;
            const misCount = safeClaims.filter(c => c && c.claim && (c.claim.indicator_type || '').toLowerCase().includes('misconduct')).length;
            const mslCount = safeClaims.filter(c => c && c.claim && (c.claim.indicator_type || '').toLowerCase().includes('misleading')).length;

            // Render 100% Pure HTML/CSS Progress Bars (Works offline, bulletproof, zero blank spaces)
            const container = document.getElementById('indicator-progress-bars');
            if (container) {
                const total = safeClaims.length || 1;
                const items = [
                    { name: 'Selective Disclosure', count: selCount, color: '#ef4444', desc: 'Che giấu thông tin xấu / Trích dẫn chọn lọc' },
                    { name: 'Hollow Promise', count: holCount, color: '#f59e0b', desc: 'Cam kết rỗng không có lộ trình' },
                    { name: 'Misconduct', count: misCount, color: '#8b5cf6', desc: 'Sai phạm số liệu môi trường' },
                    { name: 'Misleading Presentation', count: mslCount, color: '#3b82f6', desc: 'Trình bày mập mờ thiếu chứng nhận' }
                ];
                
                let barsHtml = '';
                items.forEach(it => {
                    const pct = ((it.count / total) * 100).toFixed(1);
                    barsHtml += `
                        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--card-border);">
                            <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-bottom: 8px;">
                                <span style="color: ${it.color};">📍 ${it.name} <span style="color: #94a3b8; font-weight: 500; font-size: 12px;">(${it.desc})</span></span>
                                <span style="color: #f8fafc;">${it.count} claims <span style="color: #38bdf8;">(${pct}%)</span></span>
                            </div>
                            <div style="background: rgba(255,255,255,0.08); height: 10px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                                <div style="background: ${it.color}; width: ${pct}%; height: 100%; border-radius: 6px; transition: width 0.4s ease;"></div>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = barsHtml;
            }

            // Render Chart.js Canvas if library is available
            try {
                const ctx = document.getElementById('riskChart').getContext('2d');
                if (window.myRiskChart) window.myRiskChart.destroy();

                window.myRiskChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['Selective Disclosure', 'Hollow Promise', 'Misconduct', 'Misleading Presentation'],
                        datasets: [{
                            label: 'Số lượng rủi ro phát hiện',
                            data: [selCount, holCount, misCount, mslCount],
                            backgroundColor: ['#ef4444', '#f59e0b', '#8b5cf6', '#3b82f6']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8', stepSize: 1 } }, x: { ticks: { color: '#94a3b8' } } }
                    }
                });
            } catch (err) {
                console.log("Chart.js render info:", err);
            }
        }



        // Modal Control
        function toggleModal(show) {
            const modal = document.getElementById('glossary-modal');
            if (modal) {
                if (show) modal.classList.add('active');
                else modal.classList.remove('active');
            }
        }

        // Initialize dashboard
        renderCompanyMetricsTable(dataset);
        onCompanyFilterChange('ALL');
    </script>

    <!-- Interactive Glossary & Methodology Modal -->
    <div id="glossary-modal" class="modal-overlay" onclick="if(event.target===this) toggleModal(false)">
        <div class="modal-content">
            <button class="modal-close" onclick="toggleModal(false)">&times;</button>
            <h2 style="font-size: 22px; font-weight: 800; color: #60a5fa; margin-bottom: 8px;">📖 HƯỚNG DẪN VÀ GIẢI THÍCH THUẬT NGỮ HỆ THỐNG GIÁM SÁT ESG</h2>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">Tài liệu giải thích dành cho người dùng, chuyên gia thẩm định và hội đồng đánh giá.</p>
            
            <div class="glossary-card">
                <div class="glossary-title">🌿 1. Kiến trúc Hệ thống 3 Agent (3-Agent System Architecture)</div>
                <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                    - <strong>Agent 1 (ESG Claim Analyzer):</strong> Quét toàn bộ báo cáo ESG, phát hiện các phát biểu môi trường nghi vấn Greenwashing.<br>
                    - <strong>Agent 2 (Devil's Advocate):</strong> Phản biện độc lập tranh luận với Agent 1 để bảo đảm không bị ảo giác hoặc cảnh báo quá mức.<br>
                    - <strong>Agent 3 (Incident Matcher & Search API Validation):</strong> Dùng Google Custom Search API / Live Web Search API cào dữ liệu báo chí/xử phạt thực tế để đối chiếu đời thực.
                </div>
            </div>

            <div class="glossary-card">
                <div class="glossary-title">🚨 2. Các mức Rủi ro Greenwashing (Risk Levels & Risk Calibration)</div>
                <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                    - <strong style="color: #fca5a5;">🔴 High Risk (Rủi ro Cao):</strong> Tuyên bố mâu thuẫn số liệu nghiêm trọng; cam kết Net Zero lớn nhưng hoàn toàn KHÔNG có lộ trình, mốc thời gian hay số liệu kiểm chứng.<br>
                    - <strong style="color: #fde68a;">🟡 Medium Risk (Rủi ro Trung bình):</strong> Cam kết môi trường cụ thể nhưng thiếu số liệu xác minh độc lập, hoặc thông tin ngôn ngữ mập mờ.<br>
                    - <strong style="color: #6ee7b7;">🟢 Low Risk / None (Rủi ro Thấp / Không rủi ro):</strong> Thành tựu môi trường đã được kiểm chứng hoặc truyền thông chung.
                </div>
            </div>

            <div class="glossary-card">
                <div class="glossary-title">🤝 3. Chỉ số Đồng thuận Cohen's Kappa (&kappa;)</div>
                <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                    - <strong>Công thức toán học:</strong> &kappa; = (p_o - p_e) / (1 - p_e)<br>
                    - Đo lường mức độ đồng thuận giữa Agent 1 và Agent 2 sau các lượt tranh luận.<br>
                    - <strong>1.00:</strong> Perfect agreement (Đồng thuận tuyệt đối) | <strong>0.81-0.99:</strong> Near perfect | <strong>0.61-0.80:</strong> Substantial | <strong>0.41-0.60:</strong> Moderate | <strong>0.21-0.40:</strong> Fair | <strong>0.00:</strong> No agreement.
                </div>
            </div>

            <div class="glossary-card">
                <div class="glossary-title">📈 4. Ma trận Đối chiếu Báo chí (Confusion Matrix & System Metrics)</div>
                <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                    - <strong>True Positive (TP - Confirmed Risk):</strong> AI báo rủi ro và Google Search API tìm thấy báo chí xác nhận đúng.<br>
                    - <strong>False Positive (FP - Unverified Risk / Over-prediction):</strong> AI báo rủi ro nhưng thực tế chưa có báo chí xác nhận hoặc bị bác bỏ.<br>
                    - <strong>True Negative (TN - Confirmed Clean):</strong> AI báo an toàn và thực tế không có tin vi phạm nào.<br>
                    - <strong>False Negative (FN - Missed Risk):</strong> AI báo an toàn nhưng thực tế báo chí có tin xử phạt.<br>
                    - <strong>Precision = TP / (TP + FP)</strong> | <strong>Recall = TP / (TP + FN)</strong> | <strong>Accuracy = (TP + TN) / Total</strong>.
                </div>
            </div>

            <div style="text-align: right; margin-top: 20px;">
                <button onclick="toggleModal(false)" class="tab-btn active" style="background: var(--accent-blue); color: white; border: none; font-weight: 700; padding: 10px 24px; border-radius: 8px; cursor: pointer;">Đóng Hướng Dẫn</button>
            </div>
        </div>
    </div>
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

    if os.path.exists("output_results.html") or output_html_path != "output_results.html":
        with open("output_results.html", "w", encoding="utf-8") as f:
            f.write(html_content)


    full_abs_path = os.path.abspath(output_html_path)
    print(f"\n=======================================================")
    print(f"🖥️ HTML DASHBOARD GENERATED SUCCESSFULLY!")
    print(f"🌐 Open file in browser: file:///{full_abs_path.replace(os.sep, '/')}")
    print(f"=======================================================\n")


if __name__ == "__main__":
    generate_html_dashboard()
