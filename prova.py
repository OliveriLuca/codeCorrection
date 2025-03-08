import streamlit as st

st.title("Caricamento dei Materiali")

# Inizializza lo stato della sessione per i file caricati
if "testo_esame" not in st.session_state:
    st.session_state["testo_esame"] = None
if "criteri_correzione" not in st.session_state:
    st.session_state["criteri_correzione"] = None
if "codici_studenti" not in st.session_state:
    st.session_state["codici_studenti"] = None

col1, col2, col3 = st.columns(3)

with col1:
    st.header("Testo d'Esame")
    testo_esame = st.file_uploader("Carica il PDF del testo d'esame", type=["pdf"])
    if testo_esame is not None:
        st.session_state["testo_esame"] = testo_esame
        st.success("File caricato con successo!")

with col2:
    st.header("Criteri di Correzione")
    criteri_correzione = st.file_uploader("Carica il PDF con i criteri di correzione", type=["pdf"])
    if criteri_correzione is not None:
        st.session_state["criteri_correzione"] = criteri_correzione
        st.success("File caricato con successo!")

with col3:
    st.header("Codici Studenti")
    codici_studenti = st.file_uploader("Carica il PDF con i codici degli studenti", type=["pdf"])
    if codici_studenti is not None:
        st.session_state["codici_studenti"] = codici_studenti
        st.success("File caricato con successo!")

# Pulsante per accedere alla pagina di correzione
if st.button("Vai alla Correzione"):
    st.switch_page("pages/correzione.py")
