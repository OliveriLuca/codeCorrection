import streamlit as st
import pdfplumber  # Per leggere il testo dei PDF
import base64      # Per visualizzare il PDF nel browser

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")   

# Titolo principale della pagina
st.title("Pagina di Correzione")   

# Creazione di due colonne di uguale dimensione per visualizzare i file PDF
col1, col2 = st.columns(2)

# Funzione per eliminare un file dallo stato della sessione
def elimina_file(file_key):
    if file_key in st.session_state:  # Verifica se il file è stato caricato nella sessione
        del st.session_state[file_key]  # Rimuove il file dalla sessione
        st.success(f"File '{file_key.replace('_', ' ')}' eliminato con successo!")  # Messaggio di conferma
        st.rerun()  # Ricarica la pagina per aggiornare la UI

# Funzione per mostrare un'anteprima del PDF
def mostra_pdf(file):
    if file is not None:
        # Converte il file PDF in base64 per visualizzarlo all'interno di un iframe
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    st.header("Codici Studenti")
    # Verifica se il file è presente nella sessione
    if "codici_studenti" in st.session_state and st.session_state["codici_studenti"]:
        with st.expander("Visualizza Codici Studenti", expanded=False):
            st.write(f"📄 **File caricato:** {st.session_state['codici_studenti'].name}")
            # Pulsante per scaricare il file caricato
            st.download_button("Scarica Codici Studenti", st.session_state["codici_studenti"].getvalue(),
                               file_name=st.session_state["codici_studenti"].name, mime="application/pdf")
            # Mostra un'anteprima del PDF
            mostra_pdf(st.session_state["codici_studenti"])
            # Pulsante per eliminare il file
            if st.button("Elimina Codici Studenti"):
                elimina_file("codici_studenti")
    else:
        st.warning("Nessun file caricato per i codici studenti.")

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Criteri di Correzione")
    # Verifica se il file è presente nella sessione
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        with st.expander("Visualizza Criteri di Correzione", expanded=False):
            st.write(f"📄 **File caricato:** {st.session_state['criteri_correzione'].name}")
            # Pulsante per scaricare il file caricato
            st.download_button("Scarica Criteri di Correzione", st.session_state["criteri_correzione"].getvalue(),
                               file_name=st.session_state["criteri_correzione"].name, mime="application/pdf")
            # Mostra un'anteprima del PDF
            mostra_pdf(st.session_state["criteri_correzione"])
            # Pulsante per eliminare il file
            if st.button("Elimina Criteri di Correzione"):
                elimina_file("criteri_correzione")
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Linea di separazione tra le sezioni
st.divider()

# Creazione di una colonna centrale per il Testo d'Esame
spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

# Sezione per la visualizzazione del Testo d'Esame
with col3:
    st.header("Testo d'Esame")
    # Verifica se il file è presente nella sessione
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        with st.expander("Visualizza Testo d'Esame"):
            file = st.session_state["testo_esame"]
            st.write(f"📄 **File caricato:** {file.name}")
            
            # Se il file è un PDF, viene mostrato nell'iframe
            if file.name.endswith(".pdf"):
                mostra_pdf(file)
            else:
                # Se il file non è un PDF, viene mostrato come testo semplice
                testo = file.getvalue().decode("utf-8")
                st.text_area("Contenuto del Testo d'Esame", testo, height=300)
            
            # Pulsante per eliminare il file
            if st.button("Elimina Testo d'Esame"):
                elimina_file("testo_esame")
    else:
        st.warning("Nessun file caricato per il testo d'esame.")

# Pulsante per tornare alla pagina di caricamento
if st.button("Torna al Caricamento"):
    st.switch_page("caricamento.py")
