import streamlit as st

# Titolo della pagina
st.title("Caricamento dei Materiali")

# Colonne per la disposizione dei riquadri
col1, col2, col3 = st.columns(3)

# Riquadro per il Testo d'Esame
with col1:
    st.header("Testo d'Esame")
    testo_esame = st.file_uploader("Carica il PDF del testo d'esame", type=["pdf"], key="testo_esame")
    if testo_esame is not None:
        st.success("File caricato con successo!")

# Riquadro per i Criteri di Correzione
with col2:
    st.header("Criteri di Correzione")
    criteri_correzione = st.file_uploader("Carica il PDF con i criteri di correzione", type=["pdf"], key="criteri_correzione")
    if criteri_correzione is not None:
        st.success("File caricato con successo!")

# Riquadro per i Codici Studenti
with col3:
    st.header("Codici Studenti")
    codici_studenti = st.file_uploader("Carica il PDF con i codici degli studenti", type=["pdf"], key="codici_studenti")
    if codici_studenti is not None:
        st.success("File caricato con successo!")

# Pulsante per accedere alla pagina di correzione
if st.button("Vai alla Correzione"):
    st.switch_page("pages/correzione.py")
