import os
import sys
import json
import time
from src.pipeline import run_greenwashing_pipeline
from generate_dashboard import generate_html_dashboard

# Mapping of PDF files to company names
DATASETS = [
    {"pdf": "data/2023AR_VN.pdf", "company": "Sabeco", "top_chunks": 8},
    {"pdf": "data/2025AR_VN_v1.pdf", "company": "Sabeco", "top_chunks": 8},
    {"pdf": "data/BHN_Baocaothuongnien_2024.pdf", "company": "Habeco", "top_chunks": 6},
    {"pdf": "data/DBC_Baocaothuongnien_2023.pdf", "company": "Dabaco", "top_chunks": 6},
    {"pdf": "data/DBC_Baocaothuongnien_2024.pdf", "company": "Dabaco", "top_chunks": 6},
    {"pdf": "data/KDC_Baocaothuongnien_2024.pdf", "company": "Kido", "top_chunks": 6},
    {"pdf": "data/KDC_Baocaothuongnien_2025.pdf", "company": "Kido", "top_chunks": 6},
    {"pdf": "data/Masan2025.pdf", "company": "Masan", "top_chunks": 6},
    {"pdf": "data/masan2026.pdf", "company": "Masan", "top_chunks": 6},
    {"pdf": "data/VCF_Baocaothuongnien_2024.pdf", "company": "Vinacafé", "top_chunks": 6},
    {"pdf": "data/VCF_Baocaothuongnien_2025.pdf", "company": "Vinacafé", "top_chunks": 6},
    {"pdf": "data/VSN2023VI.pdf", "company": "Vissan", "top_chunks": 6},
    {"pdf": "data/VSN2025.pdf", "company": "Vissan", "top_chunks": 6},
    # Vinamilk — 2 báo cáo bị thiếu
    {"pdf": "data/VNMSR_2024_VN_3e1e0590bd.pdf", "company": "Vinamilk", "top_chunks": 8},
    {"pdf": "data/VNMSR_Full_VN_Smart_PDF_0807_compressed_614c2277d9.pdf", "company": "Vinamilk", "top_chunks": 8},
]

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs("output_results", exist_ok=True)
    
    print("=" * 70)
    print(f"🚀 BẮT ĐẦU CHẠY PIPELINE THỰC TẾ 100% CHO {len(DATASETS)} BÁO CÁO ESG")
    print("=" * 70)
    
    start_time = time.time()
    success_count = 0
    
    for idx, item in enumerate(DATASETS, 1):
        pdf_path = item["pdf"]
        company = item["company"]
        top_k = item["top_chunks"]
        out_name = os.path.splitext(os.path.basename(pdf_path))[0] + "_result.json"
        out_json = os.path.join("output_results", out_name)
        
        print(f"\n[{idx}/{len(DATASETS)}] 👉 Đang xử lý: {pdf_path} ({company})...")
        try:
            run_greenwashing_pipeline(
                pdf_path=pdf_path,
                company_name=company,
                top_chunks=top_k,
                output_json_path=out_json
            )
            success_count += 1
            print(f"✅ Hoàn thành {company} ({pdf_path}) -> {out_json}")
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {pdf_path}: {e}")
            
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN THÀNH {success_count}/{len(DATASETS)} BÁO CÁO! (Thời gian: {time.time() - start_time:.1f}s)")
    print("📊 Đang tổng hợp Dashboard HTML...")
    
    generate_html_dashboard()
    print("✅ Đã xuất bản Dashboard: output_results.html & dashboard.html")

if __name__ == "__main__":
    main()
