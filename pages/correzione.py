import streamlit as st
import fitz  # PyMuPDF per leggere i PDF

st.title("Pagina di Correzione")

# Funzione per leggere il testo di un PDF
def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
        return text
    return "Nessun file caricato."

# Colonne per la visualizzazione
col1, col2 = st.columns(2)

# Colonna per i codici degli studenti
with col1:
    st.header("Codici Studenti")
    if "codici_studenti" in st.session_state and st.session_state["codici_studenti"] is not None:
        codici_text = extract_text_from_pdf(st.session_state["codici_studenti"])
        st.text_area("Anteprima Codici", codici_text, height=300)
    else:
        st.warning("Nessun file caricato per i codici studenti.")

# Colonna per i criteri di correzione
with col2:
    st.header("Criteri di Correzione")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"] is not None:
        criteri_text = extract_text_from_pdf(st.session_state["criteri_correzione"])
        st.text_area("Anteprima Criteri", criteri_text, height=300)
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Pulsante per tornare indietro
if st.button("Torna al Caricamento"):
    st.switch_page("prova.py")
