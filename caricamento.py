import streamlit as st

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")  

# Titolo principale della pagina
st.title("Caricamento dei Materiali")  

# Inizializza lo stato della sessione per i file, se non esiste già
if "testo_esame" not in st.session_state:
    st.session_state["testo_esame"] = None
if "criteri_correzione" not in st.session_state:
    st.session_state["criteri_correzione"] = None
if "codici_studenti" not in st.session_state:
    st.session_state["codici_studenti"] = None

# Funzione per caricare un file e salvarlo nello stato della sessione
def carica_file(file, key):
    if file is not None:
        st.session_state[key] = file  # Salva il file nello stato della sessione
        st.success(f"File '{file.name}' caricato con successo!")  # Mostra un messaggio di conferma

# Creazione di tre colonne per il caricamento dei file
col1, col2, col3 = st.columns(3)

# Upload del Testo d'Esame
with col1:
    st.subheader("Testo d'Esame")
    # Permette il caricamento di un file PDF
    file = st.file_uploader("Carica il PDF", type=["pdf"], key="upload_testo_esame")
    if file:
        carica_file(file, "testo_esame")  # Salva il file nello stato della sessione
    # Se il file è già stato caricato, mostra il nome e permette il download
    if st.session_state["testo_esame"]:
        st.write(f"📄 **File caricato:** {st.session_state['testo_esame'].name}")
        st.download_button("Scarica", st.session_state["testo_esame"].getvalue(), 
                           file_name=st.session_state["testo_esame"].name, mime="application/pdf")

# Upload dei Criteri di Correzione
with col2:
    st.subheader("Criteri di Correzione")
    # Permette il caricamento di un file PDF
    file = st.file_uploader("Carica il PDF", type=["pdf"], key="upload_criteri_correzione")
    if file:
        carica_file(file, "criteri_correzione")  # Salva il file nello stato della sessione
    # Se il file è già stato caricato, mostra il nome e permette il download
    if st.session_state["criteri_correzione"]:
        st.write(f"📄 **File caricato:** {st.session_state['criteri_correzione'].name}")
        st.download_button("Scarica", st.session_state["criteri_correzione"].getvalue(), 
                           file_name=st.session_state["criteri_correzione"].name, mime="application/pdf")

# Upload dei Codici Studenti
with col3:
    st.subheader("Codici Studenti")
    # Permette il caricamento di un file PDF
    file = st.file_uploader("Carica il PDF", type=["pdf"], key="upload_codici_studenti")
    if file:
        carica_file(file, "codici_studenti")  # Salva il file nello stato della sessione
    # Se il file è già stato caricato, mostra il nome e permette il download
    if st.session_state["codici_studenti"]:
        st.write(f"📄 **File caricato:** {st.session_state['codici_studenti'].name}")
        st.download_button("Scarica", st.session_state["codici_studenti"].getvalue(), 
                           file_name=st.session_state["codici_studenti"].name, mime="application/pdf")

# Pulsante per accedere alla pagina di correzione
if st.button("Vai alla Pagina di Correzione"):
    st.switch_page("pages/correzione.py")  # Reindirizza alla pagina di correzione
