import streamlit as st
import os

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")  

# Titolo principale della pagina
st.title("Caricamento dei Materiali")  

# Inizializza lo stato della sessione per i file, se non esiste già
if "testo_esame" not in st.session_state:
    st.session_state["testo_esame"] = None
if "criteri_correzione" not in st.session_state:
    st.session_state["criteri_correzione"] = None
if "cartella_codici" not in st.session_state:
    st.session_state["cartella_codici"] = None

# Funzione per caricare un file e salvarlo nello stato della sessione
def carica_file(file, key):
    if file is not None:
        st.session_state[key] = file
        st.success(f"File '{file.name}' caricato con successo!")

# Funzione per caricare una cartella e salvarne il percorso nello stato della sessione
def carica_cartella(cartella):
    if cartella:
        st.session_state["cartella_codici"] = cartella
        st.success(f"Cartella '{cartella}' caricata con successo!")

# Creazione di tre colonne per il caricamento dei file
col1, col2, col3 = st.columns(3)

# Upload del Testo d'Esame
with col1:
    st.subheader("Testo d'Esame")
    file = st.file_uploader("Carica il PDF", type=["pdf"], key="upload_testo_esame")
    if file:
        carica_file(file, "testo_esame")
    if st.session_state["testo_esame"]:
        st.write(f"📄 **File caricato:** {st.session_state['testo_esame'].name}")
        st.download_button("Scarica", st.session_state["testo_esame"].getvalue(), file_name=st.session_state["testo_esame"].name, mime="application/pdf")

# Upload dei Criteri di Correzione (file .txt)
with col2:
    st.subheader("Criteri di Correzione (.txt)")
    file = st.file_uploader("Carica il file .txt", type=["txt"], key="upload_criteri_correzione")
    if file:
        carica_file(file, "criteri_correzione")
    if st.session_state["criteri_correzione"]:
        st.write(f"📄 **File caricato:** {st.session_state['criteri_correzione'].name}")
        st.download_button("Scarica", st.session_state["criteri_correzione"].getvalue(), file_name=st.session_state["criteri_correzione"].name, mime="text/plain")

# Upload della Cartella dei Codici Studenti
with col3:
    st.subheader("Codici Studenti (Cartella)")
    cartella = st.text_input("Inserisci il percorso della cartella dei codici studenti:")
    if st.button("Carica Cartella"):
        if os.path.isdir(cartella):
            carica_cartella(cartella)
        else:
            st.error("Percorso non valido. Inserisci una cartella esistente.")
    if st.session_state["cartella_codici"]:
        st.write(f"📁 **Cartella caricata:** {st.session_state['cartella_codici']}")

# Pulsante per accedere alla pagina di correzione
if st.button("Vai alla Pagina di Correzione"):
    st.switch_page("pages/correzione.py")
