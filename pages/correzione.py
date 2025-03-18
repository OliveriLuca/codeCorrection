import streamlit as st
import os
import base64

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")   

# Titolo principale della pagina
st.title("Pagina di Correzione")   

# Creazione di due colonne di uguale dimensione per visualizzare i file PDF e i codici studenti
col1, col2 = st.columns(2)

# Funzione per eliminare un file dallo stato della sessione
def elimina_file(file_key):
    if file_key in st.session_state:
        del st.session_state[file_key]
        st.success(f"File '{file_key.replace('_', ' ')}' eliminato con successo!")
        st.rerun()

# Funzione per mostrare un'anteprima del PDF
def mostra_pdf(file):
    if file is not None:
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    st.header("Codici Studenti")
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        cartella = st.session_state["cartella_codici"]
        st.write(f"📁 **Cartella caricata:** {cartella}")

        # Mostra le sottocartelle e i file .c presenti nella cartella
        for root, dirs, files in os.walk(cartella):
            for nome_dir in dirs:
                st.subheader(f"📂 {nome_dir}")
                percorso_dir = os.path.join(root, nome_dir)
                for file in os.listdir(percorso_dir):
                    if file.endswith(".c"):
                        percorso_file = os.path.join(percorso_dir, file)
                        with open(percorso_file, "r") as codice_file:
                            codice = codice_file.read()
                        st.text_area(f"Contenuto di {file}", codice, height=200)
    else:
        st.warning("Nessuna cartella caricata per i codici studenti.")

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Criteri di Correzione (.txt)")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        st.write(f"📄 **File caricato:** {file.name}")

        # Visualizza il contenuto del file .txt
        testo = file.getvalue().decode("utf-8")
        st.text_area("Contenuto dei Criteri di Correzione", testo, height=300)
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Linea di separazione tra le sezioni
st.divider()

# Creazione di una colonna centrale per il Testo d'Esame
spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

# Sezione per la visualizzazione del Testo d'Esame
with col3:
    st.header("Testo d'Esame")
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        file = st.session_state["testo_esame"]
        st.write(f"📄 **File caricato:** {file.name}")
        mostra_pdf(file)
    else:
        st.warning("Nessun file caricato per il testo d'esame.")

# Pulsante per tornare alla pagina di caricamento
if st.button("Torna al Caricamento"):
    st.switch_page("caricamento.py")
