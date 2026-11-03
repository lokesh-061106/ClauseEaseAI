import PyPDF2

def parse_document(uploaded_file):
    """
    Input: Streamlit uploaded file object
    Processing: Checks extension. If PDF, uses PyPDF2 to extract text from all pages. If TXT, decodes to string.
    Output: A string containing the extracted raw text.
    Purpose: Provides a unified interface to read different file formats into raw text.
    """
    if uploaded_file is None:
        return ""
        
    extracted_text = ""
    if uploaded_file.name.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text_pages = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
            extracted_text = "\n".join(text_pages)
        except Exception as e:
            return f"Error reading PDF: {e}"
    elif uploaded_file.name.endswith(".txt"):
        extracted_text = uploaded_file.getvalue().decode("utf-8")
        
    return extracted_text
