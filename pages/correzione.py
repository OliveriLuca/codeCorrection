import streamlit as st

st.title("Pagina di Correzione")

col1, col2 = st.columns(2)

# Funzione per eliminare un file dallo stato della sessione
def elimina_file(file_key):
    if file_key in st.session_state:
        del st.session_state[file_key]
        st.success(f"File '{file_key.replace('_', ' ')}' eliminato con successo!")
        st.rerun()

# Mostra i Codici Studenti
with col1:
    st.header("Codici Studenti")
    if "codici_studenti" in st.session_state and st.session_state["codici_studenti"]:
        st.write(f"📄 **File caricato:** {st.session_state['codici_studenti'].name}")
        st.download_button("Scarica Codici Studenti", st.session_state["codici_studenti"].getvalue(),
                           file_name=st.session_state["codici_studenti"].name, mime="application/pdf")
        if st.button("Elimina Codici Studenti"):
            elimina_file("codici_studenti")
    else:
        st.warning("Nessun file caricato per i codici studenti.")

# Mostra i Criteri di Correzione
with col2:
    st.header("Criteri di Correzione")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        st.write(f"📄 **File caricato:** {st.session_state['criteri_correzione'].name}")
        st.download_button("Scarica Criteri di Correzione", st.session_state["criteri_correzione"].getvalue(),
                           file_name=st.session_state["criteri_correzione"].name, mime="application/pdf")
        if st.button("Elimina Criteri di Correzione"):
            elimina_file("criteri_correzione")
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Pulsante per tornare alla pagina di caricamento
if st.button("Torna al Caricamento"):
    st.switch_page("caricamento.py")
