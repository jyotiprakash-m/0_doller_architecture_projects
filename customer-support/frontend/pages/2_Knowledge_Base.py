"""
Knowledge Base Page — Upload company docs, manage knowledge bases.
"""
import streamlit as st
from utils.styles import inject_custom_css

inject_custom_css()

if not st.session_state.get("token"):
    st.warning("Please login first.")
    st.stop()

api = st.session_state.api
st.markdown("# 📚 Knowledge Base Manager")
st.caption("Upload your company's documents to power realistic training scenarios.")

# Create new KB
with st.expander("➕ Create New Knowledge Base", expanded=False):
    with st.form("create_kb"):
        name = st.text_input("Name", placeholder="e.g., Acme Corp Support Docs")
        desc = st.text_area("Description", placeholder="Company FAQs, product manuals, policies...", height=80)
        if st.form_submit_button("Create", type="primary", use_container_width=True):
            if name:
                result = api.create_kb(name, desc)
                if result:
                    st.success(f"✅ Knowledge base '{name}' created!")
                    st.rerun()
            else:
                st.warning("Please enter a name.")

st.markdown("---")

# List knowledge bases
kbs = api.list_kbs()
if not kbs:
    st.info("No knowledge bases yet. Create one above to get started!")
    st.stop()

for kb in kbs:
    with st.container():
        col_info, col_actions = st.columns([3, 1])

        with col_info:
            st.markdown(f"""
            <div class="info-card">
                <h3 style="margin: 0;">📚 {kb['name']}</h3>
                <p style="color: #9ca3af; margin: 0.3rem 0;">{kb.get('description', '')}</p>
                <p style="color: #6b7280; font-size: 0.85rem;">
                    📄 {kb.get('doc_count', 0)} documents · Created: {kb['created_at'][:10]}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_actions:
            if st.button("🗑️ Delete", key=f"del_kb_{kb['id']}"):
                api.delete_kb(kb["id"])
                st.success("Deleted!")
                st.rerun()

        # Document upload and list (inside expandable section per KB)
        with st.expander(f"📄 Documents in {kb['name']}", expanded=False):
            # Upload
            uploaded = st.file_uploader(
                "Upload document",
                type=["pdf", "docx", "txt", "md"],
                key=f"upload_{kb['id']}",
            )
            if uploaded:
                if st.button("📤 Index Document", key=f"idx_{kb['id']}"):
                    with st.spinner("Extracting text and indexing via RAG..."):
                        result = api.upload_kb_document(kb["id"], uploaded)
                        if result:
                            st.success(f"✅ Indexed '{uploaded.name}' — {result.get('chunk_count', 0)} chunks")
                            st.rerun()

            # List docs
            docs = api.list_kb_documents(kb["id"])
            if docs:
                for doc in docs:
                    dcol1, dcol2, dcol3 = st.columns([3, 1, 1])
                    with dcol1:
                        status_icon = "✅" if doc["status"] == "indexed" else "⏳" if doc["status"] == "uploaded" else "❌"
                        st.write(f"{status_icon} **{doc['filename']}** — {doc.get('chunk_count', 0)} chunks")
                    with dcol2:
                        size_kb = doc.get("file_size", 0) / 1024
                        st.write(f"{size_kb:.1f} KB")
                    with dcol3:
                        if st.button("🗑️", key=f"del_doc_{doc['id']}"):
                            api.delete_kb_document(kb["id"], doc["id"])
                            st.rerun()
            else:
                st.info("No documents yet. Upload one above.")

        st.markdown("")  # spacer
