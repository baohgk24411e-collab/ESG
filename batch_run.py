import os
import json
import glob
from typing import List
from src.pipeline import run_greenwashing_pipeline

DATA_DIR = r"d:\ESG\data"
OUTPUT_DIR = r"d:\ESG\output_results"


def extract_company_name(filename: str) -> str:
    fn_upper = filename.upper()
    if "VNM" in fn_upper or "VINAMILK" in fn_upper:
        return "Vinamilk"
    elif "MASAN" in fn_upper or "MSN" in fn_upper:
        return "Masan"
    elif "2023AR" in fn_upper or "2025AR" in fn_upper or "SABECO" in fn_upper or "SAB" in fn_upper:
        return "Sabeco"
    elif "BHN" in fn_upper or "HABECO" in fn_upper:
        return "Habeco"
    elif "DBC" in fn_upper or "DABACO" in fn_upper:
        return "Dabaco"
    elif "KDC" in fn_upper or "KIDO" in fn_upper:
        return "Kido"
    elif "VCF" in fn_upper or "VINACAFE" in fn_upper:
        return "Vinacafé"
    elif "VSN" in fn_upper or "VISSAN" in fn_upper:
        return "Vissan"
    else:
        return filename.split("_")[0].replace(".pdf", "").title()


def run_batch_processing(top_chunks: int = 20):
    """
    Automatically discover all PDF files in data/ directory and process each company report.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))

    if not pdf_files:
        print(f"⚠️ No PDF files found in {DATA_DIR}!")
        return

    print(f"=======================================================")
    print(f"📦 FOUND {len(pdf_files)} ESG PDF REPORTS TO PROCESS IN BATCH")
    print(f"=======================================================\n")

    summary_list = []

    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        company_name = extract_company_name(filename)
        base_name = os.path.splitext(filename)[0]

        print(f"\n▶️ [{idx}/{len(pdf_files)}] Processing Company: {company_name} ({filename})...")

        out_json_path = os.path.join(OUTPUT_DIR, f"{base_name}_result.json")

        try:
            result = run_greenwashing_pipeline(
                pdf_path=pdf_path,
                company_name=company_name,
                top_chunks=top_chunks,
                output_json_path=out_json_path
            )

            summary_list.append({
                "company_name": company_name,
                "pdf_file": filename,
                "total_claims": len(result.claims_detected),
                "precision": result.metrics.precision,
                "recall": result.metrics.recall,
                "f1_score": result.metrics.f1_score,
                "accuracy": result.metrics.accuracy,
                "result_file": out_json_path
            })
        except Exception as e:
            print(f"❌ Error processing {company_name}: {e}")

    # Save summary report across all companies
    summary_path = os.path.join(OUTPUT_DIR, "batch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_list, f, ensure_ascii=False, indent=2)

    print(f"\n=======================================================")
    print(f"🎉 BATCH PROCESSING COMPLETED!")
    print(f"📊 Summary report saved to: {summary_path}")
    print(f"=======================================================\n")

    # Generate unified multi-company HTML dashboard
    try:
        from generate_dashboard import generate_html_dashboard
        generate_html_dashboard(json_path=os.path.join(OUTPUT_DIR, "batch_summary.json"), output_html_path="dashboard.html")
    except Exception as e:
        print(f"⚠️ Could not auto-generate batch HTML dashboard: {e}")


if __name__ == "__main__":
    run_batch_processing(top_chunks=20)

