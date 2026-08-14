import os
import json
import io
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="LexAI - Legal Document Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Apple Frosted Acrylic & Clean Light Aesthetics
st.html("""
<style>
    /* Global Font & Canvas */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #fed7aa 0%, #fbcfe8 35%, #e9d5ff 70%, #bfdbfe 100%);
        padding: 2.2rem;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.9);
    }
    
    .hero-title {
        color: #0f172a;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        letter-spacing: -0.03em;
    }
    
    .hero-subtitle {
        color: #475569;
        font-size: 1rem;
        margin-bottom: 0;
    }

    /* Glass Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
    }
    
    .metric-val {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .metric-lbl {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }

    /* Provision & Flag Cards */
    .flag-card-danger {
        background: #ffffff;
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    
    .flag-card-warning {
        background: #ffffff;
        border-left: 4px solid #f59e0b;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }

    .quote-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.88rem;
        color: #0284c7;
        margin: 0.6rem 0;
    }

    .remediation-box {
        background: #ecfdf5;
        border: 1px dashed #a7f3d0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.88rem;
        color: #065f46;
    }
</style>
""")

# ----------------- Helper Functions -----------------
def extract_text_from_file(uploaded_file):
    """Extract text from uploaded PDF, DOCX, or TXT file"""
    filename = uploaded_file.name.lower()
    if filename.endswith('.txt'):
        return uploaded_file.getvalue().decode('utf-8', errors='ignore')
    elif filename.endswith('.pdf'):
        try:
            import pypdf
            pdf_reader = pypdf.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""
    elif filename.endswith('.docx'):
        try:
            import docx
            doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
            return text.strip()
        except Exception as e:
            st.error(f"Error reading Word document: {e}")
            return ""
    return ""

def get_gemini_client(api_key):
    """Initialize Gemini client safely"""
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None

# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/scales.png", width=64)
    st.title("⚖️ LexAI Settings")
    
    # API Key Handling (Secrets -> .env -> User Input)
    default_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            default_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    if not default_key and os.environ.get("GEMINI_API_KEY"):
        default_key = os.environ.get("GEMINI_API_KEY")
        
    user_api_key = st.text_input(
        "Google Gemini API Key", 
        value=default_key, 
        type="password",
        help="Enter your Gemini API key. If left blank, the deterministic fallback rule engine is used."
    )
    
    st.divider()
    
    st.subheader("Analysis Parameters")
    summary_depth = st.selectbox(
        "Summary Depth", 
        ["medium", "short", "detailed"],
        format_func=lambda x: {"short": "Short Executive Brief (~100 words)", "medium": "Standard Coverage (~250 words)", "detailed": "Clause-by-Clause (~500 words)"}[x]
    )
    
    analysis_type = st.selectbox(
        "Analysis Scope",
        ["both", "summarize", "bias"],
        format_func=lambda x: {"both": "Full AI Suite (Summary + Bias + Entities)", "summarize": "Executive Summary Only", "bias": "Bias Audit Only"}[x]
    )
    
    enable_pii = st.toggle("Enable PII Masking", value=True, help="Masks SSNs, emails, phone numbers before sending to AI.")
    
    st.divider()
    st.caption("LexAI Legal Intelligence Platform • v2.5")

# ----------------- Main Hero Header -----------------
st.html("""
<div class="hero-banner">
    <div class="hero-title">⚖️ LexAI Legal Intelligence</div>
    <p class="hero-subtitle">Automated contract review, 5-category bias auditing, and interactive legal clause assistant.</p>
</div>
""")

# ----------------- Document Input Section -----------------
tab_upload, tab_paste, tab_sample = st.tabs(["📁 Upload Document", "✍️ Paste Text", "📄 Load Sample Agreement"])

doc_content = ""
doc_title = "Legal Document"

with tab_upload:
    uploaded_file = st.file_uploader("Upload Legal Contract (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded_file:
        doc_content = extract_text_from_file(uploaded_file)
        doc_title = uploaded_file.name

with tab_paste:
    pasted_title = st.text_input("Document Title", value="Commercial Service Agreement")
    pasted_text = st.text_area("Paste Legal Document Text", height=200, placeholder="Paste agreement text, NDA, or terms here...")
    if not doc_content and pasted_text:
        doc_content = pasted_text
        doc_title = pasted_title

with tab_sample:
    if st.button("Load Comprehensive Test Agreement (Bias & Risk Test)"):
        sample_path = os.path.join(os.path.dirname(__file__), "test_documents", "full_test_contract.txt")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                doc_content = f.read()
                doc_title = "Full Master Services Agreement (Test Contract)"
            st.success("Loaded Full Test Agreement!")

# ----------------- Run Analysis Action -----------------
if doc_content:
    st.markdown(f"**Selected Document:** `{doc_title}` &bull; *({len(doc_content.split())} words)*")
    
    if st.button("🚀 Run Full AI Analysis", type="primary", use_container_width=True):
        with st.spinner("Analyzing document clauses and running bias audits..."):
            from services.ai_service import run_gemini_analysis, run_fallback_analysis, mask_pii
            
            # Apply PII masking if requested
            processed_content = mask_pii(doc_content) if enable_pii else doc_content
            
            gemini_client = get_gemini_client(user_api_key)
            
            if gemini_client:
                analysis_res = run_gemini_analysis(processed_content, analysis_type=analysis_type, summary_length=summary_depth, client_override=gemini_client)
            else:
                analysis_res = run_fallback_analysis(processed_content, analysis_type=analysis_type, summary_length=summary_depth)
                
            st.session_state["analysis_results"] = analysis_res
            st.session_state["active_doc_content"] = doc_content
            st.session_state["active_doc_title"] = doc_title
            st.session_state["chat_history"] = []

# ----------------- Display Results -----------------
if "analysis_results" in st.session_state:
    res = st.session_state["analysis_results"]
    bias_score = res.get("bias_score", 0.0)
    bias_category = res.get("bias_category", "Neutral")
    
    st.divider()
    
    # Executive Metrics Strip
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color: {'#10b981' if bias_score < 0.2 else ('#f59e0b' if bias_score < 0.5 else '#ef4444')}">{int(bias_score * 100)}%</div>
            <div class="metric-lbl">Overall Bias Index</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        compliance = res.get("compliance_status", "Compliant" if bias_score < 0.3 else "Action Required")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color: {'#10b981' if compliance == 'Compliant' else '#f59e0b'}">{compliance}</div>
            <div class="metric-lbl">EEOC / Civil Rights</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{len(res.get('key_provisions', []))}</div>
            <div class="metric-lbl">Provisions Extracted</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        flags_count = len(res.get('flags', []))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val" style="color: {'#10b981' if flags_count == 0 else '#ef4444'}">{flags_count}</div>
            <div class="metric-lbl">Risk Clauses Flagged</div>
        </div>
        """, unsafe_allow_html=True)

    # Detailed Analysis Tabs
    res_tab_summary, res_tab_bias, res_tab_entities, res_tab_chat, res_tab_doc = st.tabs([
        "📝 Executive Summary & Provisions",
        "🛡️ Bias Audit & Remediation",
        "🏢 Entities & Terms",
        "💬 Ask LexAI Chatbot",
        "📄 Full Document Text"
    ])
    
    # Tab 1: Summary & Provisions
    with res_tab_summary:
        st.subheader("Executive Legal Summary")
        st.write(res.get("summary", "No summary generated."))
        
        provisions = res.get("key_provisions", [])
        if provisions:
            st.subheader("Key Contractual Provisions")
            p_cols = st.columns(2)
            for i, p in enumerate(provisions):
                with p_cols[i % 2]:
                    st.markdown(f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <h4 style="margin: 0 0 6px 0; color: #0284c7; font-size: 1rem;">📌 {p.get('topic', 'Provision')}</h4>
                        <p style="margin: 0; color: #475569; font-size: 0.9rem;">{p.get('clause_text', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Tab 2: Bias Audit
    with res_tab_bias:
        st.subheader("Protected Class Risk Breakdown")
        cats = res.get("categories", {})
        if cats:
            for cat_name, val in cats.items():
                if isinstance(val, (int, float)):
                    st.write(f"**{cat_name.title()} Bias**: `{int(val * 100)}%`")
                    st.progress(min(max(float(val), 0.0), 1.0))
        
        st.subheader("Remediation Recommendations")
        flags = res.get("flags", [])
        if flags:
            for f in flags:
                sev = f.get('severity', 'High').lower()
                card_class = 'flag-card-danger' if 'high' in sev else 'flag-card-warning'
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a; margin-bottom: 4px;">
                        ⚠️ {f.get('category', 'Risk Flag')} ({f.get('severity', 'Medium')} Severity)
                    </div>
                    <div class="quote-box">"{f.get('quote', '')}"</div>
                    <div class="remediation-box"><strong>Proposed Neutral Remediation:</strong> {f.get('remediation', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No discriminatory or high-risk clauses were detected in this document.")

    # Tab 3: Entities
    with res_tab_entities:
        st.subheader("Extracted Legal Entities")
        entities = res.get("entities", {})
        e_col1, e_col2, e_col3 = st.columns(3)
        with e_col1:
            st.markdown("#### 👥 People & Parties")
            for person in entities.get("people", []):
                st.markdown(f"- **{person.get('name', person)}**")
        with e_col2:
            st.markdown("#### 🏛️ Organizations")
            for org in entities.get("organizations", []):
                st.markdown(f"- **{org.get('name', org)}**")
        with e_col3:
            st.markdown("#### 💵 Monetary Values")
            for m in entities.get("monetary", []):
                st.markdown(f"- **{m.get('name', m)}**")

    # Tab 4: Ask LexAI Chatbot
    with res_tab_chat:
        st.subheader("💬 Ask LexAI About This Document")
        st.caption("Ask questions, query liability limits, or request neutral clause rewrites.")
        
        # Display chat history
        for msg in st.session_state.get("chat_history", []):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        # Chat input
        if prompt := st.chat_input("Ask a question about this document..."):
            st.session_state["chat_history"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("LexAI is reviewing clauses..."):
                    gemini_client = get_gemini_client(user_api_key)
                    if gemini_client:
                        try:
                            full_prompt = f"""You are LexAI, an intelligent legal assistant. Answer based on this document:
DOCUMENT TITLE: {st.session_state.get('active_doc_title', 'Document')}
DOCUMENT TEXT:
{st.session_state.get('active_doc_content', '')[:12000]}

User Question: {prompt}
Cite specific clauses when applicable."""
                            response = gemini_client.models.generate_content(
                                model="gemini-3.5-flash",
                                contents=full_prompt
                            )
                            answer = response.text
                        except Exception as e:
                            answer = f"AI query failed: {e}"
                    else:
                        answer = "Please provide a Google Gemini API key in the sidebar to enable conversational legal Q&A."
                        
                    st.write(answer)
                    st.session_state["chat_history"].append({"role": "assistant", "content": answer})

    # Tab 5: Full Text
    with res_tab_doc:
        st.subheader("Raw Document Content")
        st.text_area("Full Text Content", value=st.session_state.get("active_doc_content", ""), height=400, disabled=True)
        
        # Download buttons
        json_data = json.dumps(res, indent=2)
        st.download_button(
            "📥 Export Full Analysis (JSON)",
            data=json_data,
            file_name=f"{st.session_state.get('active_doc_title', 'analysis')}_audit.json",
            mime="application/json"
        )
