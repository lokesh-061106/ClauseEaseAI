import streamlit as st
import textstat
import sys
import os
import json
import pandas as pd

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing import preprocess_contract
from src.simplifier import simplify_clause
from src.summarizer import summarize_text_extractive
from src.preservation_checker import check_preservation
from src.legal_terms import detect_legal_terms

st.set_page_config(page_title="Contract Simplifier", layout="wide")

st.title("📝 Contract Language Simplifier")

user_input = st.text_area("Enter Contract Text", height=250)

if st.button("Simplify"):
    if not user_input.strip():
        st.warning("Enter text first")
    else:
        with st.spinner("Processing..."):
            clauses = preprocess_contract(user_input)
            if not clauses:
                clauses = [user_input]
                
            final_simplified_clauses = []
            preservation_reports = []
            
            for original_clause in clauses:
                simplified_clause = simplify_clause(original_clause, level="Beginner")
                report = check_preservation(original_clause, simplified_clause)
                
                # Auto Correction Loop (Max 3)
                if report['risk_level'] == "HIGH":
                    simplified_clause = simplify_clause(original_clause, level="Advanced")
                    report = check_preservation(original_clause, simplified_clause)
                    if report['risk_level'] == "HIGH":
                        simplified_clause = original_clause
                        report = check_preservation(original_clause, simplified_clause)

                final_simplified_clauses.append(simplified_clause)
                preservation_reports.append((original_clause, simplified_clause, report))
                
            simplified_full = " ".join(final_simplified_clauses)
            summary = summarize_text_extractive(user_input, num_sentences=3)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Original")
                st.write(user_input)

            with col2:
                st.subheader("Simplified")
                st.write(simplified_full)

            st.subheader("Summary")
            st.info(summary)

            score = textstat.flesch_reading_ease(simplified_full)
            st.subheader("Readability Score")
            st.write(score)
            
            # --- NEW PRESERVATION CHECKER SECTION ---
            st.markdown("---")
            st.subheader("🛡️ Preservation Checker")
            
            high_risks = 0
            table_data = []
            for orig, simp, rep in preservation_reports:
                if rep['risk_level'] == "HIGH": high_risks += 1
                table_data.append({
                    "Original": orig,
                    "Simplified": simp,
                    "Status": "Preserved" if rep['risk_level'] in ["LOW", "PRESERVED"] else "Changed",
                    "Risk": rep['risk_level']
                })
                
            overall_sim_score = sum([r[2]['similarity'] for r in preservation_reports]) / len(preservation_reports) if preservation_reports else 0
            
            if high_risks == 0:
                st.success(f"✓ Meaning Preserved (Score: {int(overall_sim_score * 100)}%)")
            else:
                st.error(f"⚠ Meaning Change Detected (Score: {int(overall_sim_score * 100)}%)")
                
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
            
            if high_risks > 0:
                st.write("**Detected Changes:**")
                for orig, simp, rep in preservation_reports:
                    if rep['risk_level'] in ["HIGH", "MEDIUM"]:
                        st.write(f"- {', '.join(rep['changed'])}: {rep['reason']}")
                        
            st.markdown("---")
            st.subheader("📖 Legal Terms")
            terms = detect_legal_terms(user_input)
            if terms:
                for term in terms:
                    st.write(f"**{term['term'].capitalize()}**: {term['explanation']}")
            else:
                st.write("No complex legal terms detected.")
