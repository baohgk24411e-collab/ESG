import sys
import argparse
from src.pipeline import run_greenwashing_pipeline

def main():
    parser = argparse.ArgumentParser(description="Greenwashing Detection 3-Agent Pipeline for Vietnamese Corporate ESG Reports")
    parser.add_argument("--pdf", type=str, default=r"d:\ESG\data\VNMSR_Full_VN_Smart_PDF_0807_compressed_614c2277d9.pdf", help="Path to ESG PDF report")
    parser.add_argument("--company", type=str, default="Vinamilk", help="Company name")
    parser.add_argument("--top_chunks", type=int, default=30, help="Number of top ESG chunks to process (default: 30 best ESG chunks)")
    parser.add_argument("--out", type=str, default="output_results.json", help="Output JSON path")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    run_greenwashing_pipeline(
        pdf_path=args.pdf,
        company_name=args.company,
        top_chunks=args.top_chunks,
        output_json_path=args.out
    )

if __name__ == "__main__":
    main()
