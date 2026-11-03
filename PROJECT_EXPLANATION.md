# ClauseGuard: Project Explanation

## Base Research Paper
**"Legal lay summarization: exploring methods and data generation with large language models"** (Moro et al., *Artificial Intelligence Review*, 2026. DOI: 10.1007/s10462-025-11392-7).

**Important Differentiation:** The base paper relies heavily on Large Language Models (LLMs) to summarize and explain legal text. Our project takes a radically different, simpler, and more transparent approach. We explicitly explore a **NON-LLM** pipeline to achieve readability improvements while ensuring **automatic verification of semantic preservation**.

## Problem Statement
Legal contracts are written in complex legalese. The core research problem is: *"How can a legal document be simplified for easier understanding while automatically checking whether important legal meaning has been preserved?"*

## Proposed System: ClauseGuard
ClauseGuard is an educational NLP tool. It features:
1. **Document Parsing:** Accepts PDF and TXT files.
2. **Education-Level Simplification:** Adjusts the aggressiveness of simplification based on user level (Beginner, Intermediate, Advanced).
3. **Non-LLM Summarization:** Uses TF-IDF for extractive summarization.
4. **Legal Term Dictionary:** Automatically detects and explains difficult legal terminology.
5. **Preservation Checker:** Extracts critical entities (Modality, Actions, Dates, Amounts) to verify meaning is preserved.
6. **Automatic Correction Loop:** If a change alters the core legal meaning, the system automatically reverts to a safer simplification level.

## Algorithms
We strictly avoid LLMs and use traditional, explainable NLP algorithms:

1. **TF-IDF (Term Frequency-Inverse Document Frequency):** Used for clause classification and extractive summarization.
2. **Logistic Regression:** Used for clause classification.
3. **Cosine Similarity:** Used to compare the semantic similarity of the original and simplified text.
4. **Rule-Based Regex & spaCy (Dependency Parsing):** Used for extracting specific legal entities.

## User Experience (Step-by-Step)
1. User uploads a contract (PDF/TXT).
2. User selects an Understanding Level.
3. The system generates a Simple Summary and highlights Legal Terms.
4. The Preservation Checker evaluates the simplification.
5. If meaning is preserved, it shows a ✓ Success message.
6. If meaning is changed (⚠ High Risk), the system triggers an automatic review loop to revise the summary.
7. User can download the Final Simplified Document and the JSON Preservation Report.

## Safety / Disclaimer
*ClauseGuard is an educational and informational NLP tool. It does not provide legal advice and does not replace a qualified legal professional. Preservation results are automated indicators and should not be treated as a guarantee of legal correctness.*
