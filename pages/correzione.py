import streamlit as st

st.title("Pagina di Correzione")

col1, col2 = st.columns(2)

# Mostra i Codici Studenti
with col1:
    st.header("Codici Studenti")
    if "codici_studenti" in st.session_state and st.session_state["codici_studenti"] is not None:
        st.write("Anteprima del file caricato:")
        st.download_button("Scarica Codici Studenti", st.session_state["codici_studenti"].getvalue(),
                           file_name="codici_studenti.pdf", mime="application/pdf")
    else:
        st.warning("Nessun file caricato per i codici studenti.")

# Mostra i Criteri di Correzione
with col2:
    st.header("Criteri di Correzione")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"] is not None:
        st.write("Anteprima del file caricato:")
        st.download_button("Scarica Criteri di Correzione", st.session_state["criteri_correzione"].getvalue(),
                           file_name="criteri_correzione.pdf", mime="application/pdf")
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Pulsante per tornare alla prima pagina
if st.button("Torna al Caricamento"):
    st.switch_page("prova.py")
