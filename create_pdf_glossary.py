import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def build_glossary_pdf(output_pdf_path="SYSTEM_GLOSSARY_AND_METHODOLOGY.pdf"):
    # Register Vietnamese Unicode fonts from Windows Fonts
    font_path = "C:/Windows/Fonts/arial.ttf"
    font_bold_path = "C:/Windows/Fonts/arialbd.ttf"
    font_italic_path = "C:/Windows/Fonts/ariali.ttf"

    pdfmetrics.registerFont(TTFont("ArialVN", font_path))
    pdfmetrics.registerFont(TTFont("ArialVN-Bold", font_bold_path))
    pdfmetrics.registerFont(TTFont("ArialVN-Italic", font_italic_path))

    # A4 dimensions: 595.27 x 841.89 pt. Printable width = 595.27 - 72 = 523.27 pt
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Vietnamese Paragraph Styles (TA_JUSTIFY for clean text alignment)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='ArialVN-Bold',
        fontSize=15,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='ArialVN-Italic',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='ArialVN-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='ArialVN',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_JUSTIFY,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='ArialVN',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        alignment=TA_JUSTIFY,
        leftIndent=12,
        spaceAfter=4
    )

    bold_prefix_style = ParagraphStyle(
        'BoldPrefix',
        parent=styles['Normal'],
        fontName='ArialVN-Bold',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=6,
        spaceAfter=3
    )

    cell_style = ParagraphStyle(
        'Cell_Style',
        parent=styles['Normal'],
        fontName='ArialVN',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_LEFT
    )

    cell_header_style = ParagraphStyle(
        'Cell_Header_Style',
        parent=styles['Normal'],
        fontName='ArialVN-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=TA_LEFT
    )

    story = []

    # Document Header
    story.append(Paragraph("HƯỚNG DẪN & GIẢI THÍCH THUẬT NGỮ HỆ THỐNG GIÁM SÁT ESG GREENWASHING", title_style))
    story.append(Paragraph("Tài liệu giải thích thuật ngữ, thang đo rủi ro và phương pháp luận dành cho Chuyên gia Thẩm định & Hội đồng Đánh giá", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3b82f6'), spaceAfter=10))

    # Section 1
    story.append(Paragraph("1. TỔNG QUAN HỆ THỐNG 3 AGENT (3-AGENT SYSTEM ARCHITECTURE)", h1_style))
    story.append(Paragraph("Hệ thống ứng dụng kiến trúc 3 Agent AI độc lập phối hợp nhằm phát hiện và giám sát rủi ro <b>Greenwashing</b> (Tẩy xanh) trong Báo cáo Phát triển Bền vững (ESG) của doanh nghiệp FMCG:", body_style))
    
    story.append(Paragraph("• <b>Agent 1 (ESG Claim Analyzer):</b> Quét toàn bộ văn bản báo cáo ESG, phát hiện các phát biểu môi trường nghi vấn Greenwashing và phân loại theo 4 nhóm Indicator.", bullet_style))
    story.append(Paragraph("• <b>Agent 2 (Devil's Advocate):</b> Phản biện độc lập tranh luận với Agent 1 để bảo đảm không bị ảo giác (hallucination) hoặc cảnh báo quá mức. Hai Agent lặp lại cuộc tranh luận cho đến khi đạt đồng thuận.", bullet_style))
    story.append(Paragraph("• <b>Agent 3 (Incident Matcher & Search API Validation):</b> Sử dụng Google Custom Search API / Live Web Search API cào dữ liệu báo chí và thông báo xử phạt thực tế để đối chiếu phán đoán AI với thực tế đời thực.", bullet_style))

    # Section 2
    story.append(Paragraph("2. GIẢI THÍCH CHI TIẾT CÁC THUẬT NGỮ CHÍNH (GLOSSARY)", h1_style))
    
    story.append(Paragraph("4 ESG Indicators (4 Nhóm Chỉ số Rủi ro Greenwashing):", bold_prefix_style))
    story.append(Paragraph("1. <b>Selective Disclosure (Giấu thông tin xấu / Vắng mặt dữ liệu ngành chính):</b> Nhấn mạnh điểm xanh nhỏ nhưng che giấu tác hại/vi phạm môi trường tiêu cực hoặc cố tình né tránh, không công bố các chỉ số trọng yếu bắt buộc theo ngành kinh doanh cốt lõi.", bullet_style))
    story.append(Paragraph("2. <b>Hollow Promise (Cam kết rỗng):</b> Đưa ra cam kết lớn (Net Zero, 100% giảm nhựa...) nhưng không có tiến triển, không lộ trình, không mốc thời gian rõ ràng.", bullet_style))
    story.append(Paragraph("3. <b>Potential Data Mispresentation (Nguy cơ trình bày sai lệch dữ liệu):</b> Các tuyên bố về môi trường (dưới dạng số liệu hoặc thông tin thực tế) thiếu nhất quán nội bộ, thiếu cơ sở chứng minh đầy đủ hoặc mâu thuẫn với các bằng chứng đáng tin cậy.", bullet_style))
    story.append(Paragraph("4. <b>Misleading Presentation (Ngôn ngữ mập mờ):</b> Dùng nhãn 'xanh 100%', 'thân thiện môi trường', 'thuần tự nhiên' mà không có chứng nhận hợp lệ.", bullet_style))

    story.append(Paragraph("Phân biệt Sự vắng mặt thông tin ngành chính vs Tuyên bố xanh ngoài lề (Sector Materiality Calibration):", bold_prefix_style))
    story.append(Paragraph("• <b>Sự vắng mặt thông tin ngành chính (Core Sector Materiality Absence):</b> Doanh nghiệp không công bố hoặc giấu nhẹm số liệu môi trường trọng yếu của ngành kinh doanh cốt lõi (vd: bia/nước giải khát không công bố nước thải; chăn nuôi/thịt không công bố Scope 1-3 & chất thải) ➔ Xếp vào <b>Selective Disclosure mức Rủi ro High / Medium</b>.", bullet_style))
    story.append(Paragraph("• <b>Tuyên bố xanh ngoài lề (Generic Green Claims):</b> Các hoạt động phong trào như trồng cây, dọn rác, văn phòng xanh nếu thiếu số liệu chỉ xếp vào <b>Hollow Promise mức Low / Medium</b>, không đánh đồng với sai lệch dữ liệu ngành chính.", bullet_style))

    story.append(Paragraph("Trạng thái Chứng cứ Biện luận của Agent 1 (Evidence Status):", bold_prefix_style))
    story.append(Paragraph("• <b>Sufficient (Đầy đủ chứng cứ):</b> Trích dẫn đầy đủ số liệu định lượng, mốc thời gian và ngữ cảnh văn bản đối chiếu rõ ràng.", bullet_style))
    story.append(Paragraph("• <b>Partial (Một phần chứng cứ):</b> Có câu trích dẫn hoặc số liệu nhưng chưa hoàn chỉnh ngữ cảnh đối chiếu.", bullet_style))
    story.append(Paragraph("• <b>Insufficient (Thiếu chứng cứ):</b> Trích dẫn chung chung, thiếu căn cứ xác minh để biện luận.", bullet_style))

    story.append(Paragraph("Risk Levels & Calibration (Các mức độ Rủi ro):", bold_prefix_style))
    story.append(Paragraph("• <b>[High Risk] (Rủi ro Cao):</b> Tuyên bố mâu thuẫn số liệu nghiêm trọng hoặc che giấu tác động môi trường của ngành cốt lõi; cam kết rất lớn mà hoàn toàn không có lộ trình.", bullet_style))
    story.append(Paragraph("• <b>[Medium Risk] (Rủi ro Trung bình):</b> Cam kết môi trường cụ thể nhưng thiếu số liệu xác minh độc lập, hoặc thông tin ngôn ngữ mập mờ.", bullet_style))
    story.append(Paragraph("• <b>[Low Risk / None] (Rủi ro Thấp / Không rủi ro):</b> Thông điệp truyền thông chung, sứ mệnh doanh nghiệp, hoặc thành tựu đã được chứng nhận rõ ràng.", bullet_style))

    # Section 3: Cohen Kappa Table
    story.append(Paragraph("3. CHỈ SỐ ĐỒNG THUẬN COHEN'S KAPPA (κ - INTER-RATER AGREEMENT)", h1_style))
    story.append(Paragraph("Công thức toán học chuẩn: <b>κ = (p_o - p_e) / (1 - p_e)</b>", body_style))
    story.append(Paragraph("Bảng xếp hạng mức độ đồng thuận theo chuẩn Landis & Koch (1977):", body_style))

    kappa_raw_data = [
        ["Giá trị Cohen's Kappa (κ)", "Mức độ Đồng thuận", "Ý nghĩa thực tế trong Hệ thống"],
        ["1.00", "Perfect agreement", "Đồng thuận tuyệt đối giữa Agent 1 & Agent 2"],
        ["0.81 - 0.99", "Near perfect agreement", "Gần như hoàn hảo (Độ tin cậy rất cao)"],
        ["0.61 - 0.80", "Substantial agreement", "Đồng thuận đáng kể (Kết quả phản biện vững chắc)"],
        ["0.41 - 0.60", "Moderate agreement", "Đồng thuận vừa phải (Cần xem xét luận điểm)"],
        ["0.21 - 0.40", "Fair agreement", "Đồng thuận trung bình (Có sự khác biệt rủi ro)"],
        ["0.10 - 0.20", "Slight agreement", "Đồng thuận nhẹ (Bất đồng quan điểm nhẹ)"],
        ["0.00", "No agreement", "Bất đồng hoàn toàn (Cần con người can thiệp - HITL)"]
    ]

    kappa_table_data = []
    for r_idx, row in enumerate(kappa_raw_data):
        row_cells = []
        for cell_text in row:
            st = cell_header_style if r_idx == 0 else cell_style
            row_cells.append(Paragraph(cell_text, st))
        kappa_table_data.append(row_cells)

    # Printable width: 523pt total
    t_kappa = Table(kappa_table_data, colWidths=[115, 140, 268])
    t_kappa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eff6ff')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_kappa)

    # Section 4: Confusion Matrix Table
    story.append(Paragraph("4. MA TRẬN ĐỐI CHIẾU BÁO CHÍ & ĐỘ CHÍNH XÁC (CONFUSION MATRIX & METRICS)", h1_style))
    
    cm_raw_data = [
        ["Trạng thái phân loại", "Ký hiệu toán học", "Ý nghĩa đánh giá thực tế"],
        ["Confirmed Risk", "True Positive (TP)", "AI báo rủi ro và Google Search API tìm thấy báo chí xác nhận đúng."],
        ["Unverified Risk", "False Positive (FP)", "AI báo rủi ro nhưng thực tế chưa có báo chí xác nhận hoặc bị bác bỏ."],
        ["Confirmed Clean", "True Negative (TN)", "AI báo an toàn/rủi ro thấp và thực tế không có bài báo vi phạm."],
        ["Missed Risk", "False Negative (FN)", "AI báo an toàn nhưng thực tế báo chí có tin xử phạt vi phạm."]
    ]

    cm_table_data = []
    for r_idx, row in enumerate(cm_raw_data):
        row_cells = []
        for cell_text in row:
            st = cell_header_style if r_idx == 0 else cell_style
            row_cells.append(Paragraph(cell_text, st))
        cm_table_data.append(row_cells)

    # Printable width: 523pt total
    t_cm = Table(cm_table_data, colWidths=[115, 135, 273])
    t_cm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0fdf4')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_cm)

    story.append(Paragraph("<br/><b>Công thức chỉ số hiệu năng tổng thể:</b>", bold_prefix_style))
    story.append(Paragraph("• <b>Precision (Độ chính xác):</b> Precision = TP / (TP + FP)", bullet_style))
    story.append(Paragraph("• <b>Recall (Độ bao phủ):</b> Recall = TP / (TP + FN)", bullet_style))
    story.append(Paragraph("• <b>F1-Score:</b> F1 = 2 * (Precision * Recall) / (Precision + Recall)", bullet_style))
    story.append(Paragraph("• <b>Accuracy (Độ chính xác toàn cục):</b> Accuracy = (TP + TN) / (TP + FP + TN + FN)", bullet_style))

    doc.build(story)
    print(f"📄 Successfully generated polished Glossary PDF at: {output_pdf_path}")

if __name__ == "__main__":
    build_glossary_pdf()
