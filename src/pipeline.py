import os
import json
from src.models import FullPipelineOutput
from src.ingestor import extract_pdf_chunks
from src.phobert_embedder import filter_esg_relevant_chunks
from src.agents.agent1_analyzer import analyze_chunk_for_claims
from src.agents.agent2_debater import run_debate_loop
from src.incident_crawler import search_environmental_incidents
from src.agents.agent3_matcher import match_claim_with_incidents
from src.metrics import calculate_evaluation_metrics


def run_greenwashing_pipeline(
    pdf_path: str, 
    company_name: str = "Vinamilk",
    top_chunks: int = 15,
    output_json_path: str = "output_results.json"
) -> FullPipelineOutput:
    """
    Run full 3-Agent Greenwashing Detection Pipeline.
    """
    print(f"\n=======================================================")
    print(f"🚀 STARTING GREENWASHING PIPELINE FOR: {company_name}")
    print(f"=======================================================\n")

    # Step 1: Ingestion
    chunks = extract_pdf_chunks(pdf_path, company_name=company_name)
    
    # Step 2: PhoBERT / Vietnamese NLP relevance filter
    relevant_chunks = filter_esg_relevant_chunks(chunks, min_score=0.05, top_k=top_chunks)

    # Step 3 & 4: Agent 1 Analysis & Agent 2 Debate Loop
    claims_detected = []
    print("\n🤖 Running Agent 1 (Analyzer) & Agent 2 (Devil's Advocate Debate Loop)...")
    for idx, chunk in enumerate(relevant_chunks, 1):
        print(f"  -> [{idx}/{len(relevant_chunks)}] Analyzing Page {chunk.page_number}...")
        extracted_claims = analyze_chunk_for_claims(chunk)
        for claim in extracted_claims:
            print(f"     🔍 Claim Found: [{claim.indicator_type}] {claim.claim_text[:60]}...")
            debate_result = run_debate_loop(claim, chunk)
            print(f"     ⚖️ Debate Final Risk: {debate_result.final_risk_level} (Consensus: {debate_result.consensus_reached})")
            claims_detected.append(debate_result)

    # Step 5: Incident Scraping
    print(f"\n📰 Scraping real-world news incidents for: {company_name}...")
    scraped_incidents = search_environmental_incidents(company_name, max_results=5)

    # Step 6: Agent 3 Incident Matching
    print("\n🔍 Running Agent 3 (Incident Matcher & Validation)...")
    incident_matches = []
    for debate_res in claims_detected:
        match_res = match_claim_with_incidents(debate_res, scraped_incidents)
        print(f"  -> Claim [{match_res.claim_id}] Match Status: {match_res.match_status}")
        incident_matches.append(match_res)

    # Step 7: Calculate System Evaluation Metrics
    metrics = calculate_evaluation_metrics(incident_matches)
    print(f"\n📊 SYSTEM EVALUATION METRICS (Confusion Matrix):")
    print(f"   -----------------------------------------------")
    print(f"   True Positives  (TP - Confirmed Risk):   {metrics.true_positives}")
    print(f"   False Positives (FP - Unverified Risk):  {metrics.false_positives}")
    print(f"   True Negatives  (TN - Confirmed Clean):  {metrics.true_negatives}")
    print(f"   False Negatives (FN - Missed Risk):     {metrics.false_negatives}")
    print(f"   -----------------------------------------------")
    print(f"   Precision: {metrics.precision * 100:.1f}%")
    print(f"   Recall:    {metrics.recall * 100:.1f}%")
    print(f"   F1-Score:  {metrics.f1_score * 100:.1f}%")
    print(f"   Accuracy:  {metrics.accuracy * 100:.1f}%")

    output = FullPipelineOutput(
        company_name=company_name,
        source_file=os.path.basename(pdf_path),
        total_chunks_processed=len(chunks),
        relevant_chunks_count=len(relevant_chunks),
        claims_detected=claims_detected,
        scraped_incidents=scraped_incidents,
        incident_matches=incident_matches,
        metrics=metrics
    )

    # Save to JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(output.dict(), f, ensure_ascii=False, indent=2)
    print(f"\n💾 Full results saved to: {output_json_path}")

    # Generate HTML Dashboard
    try:
        from generate_dashboard import generate_html_dashboard
        html_out = output_json_path.replace(".json", ".html")
        generate_html_dashboard(output_json_path, html_out)
        generate_html_dashboard(output_json_path, "dashboard.html")
    except Exception as e:
        print(f"⚠️ Could not auto-generate HTML dashboard: {e}")

    return output
