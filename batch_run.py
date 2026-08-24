import os
import json
import glob
from typing import List
from src.pipeline import run_greenwashing_pipeline

DATA_DIR = r"d:\ESG\data"
OUTPUT_DIR = r"d:\ESG\output_results"


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
        if "VNM" in filename.upper() or "VINAMILK" in filename.upper():
            company_name = "Vinamilk"
        elif "2023AR" in filename.upper() or "MASAN" in filename.upper():
            company_name = "Masan"
        else:
            company_name = filename.split("_")[0].replace(".pdf", "").title()

        print(f"\n▶️ [{idx}/{len(pdf_files)}] Processing Company: {company_name} ({filename})...")

        out_json_path = os.path.join(OUTPUT_DIR, f"{company_name.lower()}_result.json")

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


if __name__ == "__main__":
    run_batch_processing(top_chunks=20)
