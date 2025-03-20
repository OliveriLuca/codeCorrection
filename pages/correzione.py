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

# Funzione per eliminare la cartella caricata
def elimina_cartella():
    if "cartella_codici" in st.session_state:
        del st.session_state["cartella_codici"]
        st.success("Cartella dei codici studenti eliminata con successo!")
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

        # Recupera tutte le sottocartelle
        sottocartelle = [d for d in os.listdir(cartella) if os.path.isdir(os.path.join(cartella, d))]
        
        if sottocartelle:
            # Selettore per scegliere una sottocartella
            sottocartella_scelta = st.selectbox("Seleziona uno studente:", sottocartelle)
            percorso_cartella_scelta = os.path.join(cartella, sottocartella_scelta)
            
            # Cerca il file .c nella sottocartella scelta
            file_c = None
            for file in os.listdir(percorso_cartella_scelta):
                if file.endswith(".c"):
                    file_c = file
                    break
            
            if file_c:
                percorso_file = os.path.join(percorso_cartella_scelta, file_c)
                with open(percorso_file, "r") as codice_file:
                    codice = codice_file.read()
                st.text_area(f"Contenuto di {file_c}", codice, height=200)
            else:
                st.warning("Nessun file .c trovato nella cartella selezionata.")
        else:
            st.warning("Nessuna sottocartella trovata nella cartella principale.")
    else:
        st.warning("Nessuna cartella caricata per i codici studenti.")
    
    # Bottone per eliminare la cartella caricata
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        if st.button("Elimina Cartella Codici Studenti"):
            elimina_cartella()

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Criteri di Correzione (.txt)")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        st.write(f"📄 **File caricato:** {file.name}")

        # Visualizza il contenuto del file .txt
        testo = file.getvalue().decode("utf-8")
        st.text_area("Contenuto dei Criteri di Correzione", testo, height=300)

        # Pulsanti per scaricare ed eliminare il file
        st.download_button("Salva Criteri di Correzione", file.getvalue(), file_name=file.name, mime="text/plain")
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
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        file = st.session_state["testo_esame"]
        st.write(f"📄 **File caricato:** {file.name}")

        # Visualizza il contenuto del file in base al tipo
        if file.name.endswith(".pdf"):
            mostra_pdf(file)
        else:
            testo = file.getvalue().decode("utf-8")
            st.text_area("Contenuto del Testo d'Esame", testo, height=300)

        # Pulsanti per scaricare ed eliminare il file
        if file.name.endswith(".pdf"):
            st.download_button("Salva Testo d'Esame", file.getvalue(), file_name=file.name, mime="application/pdf")
        else:
            st.download_button("Salva Testo d'Esame", file.getvalue(), file_name=file.name, mime="text/plain")
        if st.button("Elimina Testo d'Esame"):
            elimina_file("testo_esame")
    else:
        st.warning("Nessun file caricato per il testo d'esame.")

# Pulsante per tornare alla pagina di caricamento
if st.button("Torna al Caricamento"):
    st.switch_page("caricamento.py")
