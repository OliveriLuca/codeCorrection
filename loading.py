import streamlit as st
import os

# Configura la pagina
st.set_page_config(layout="wide")
st.title("Loading Materials")

# Inizializza lo stato della sessione
for key in ["testo_esame", "criteri_correzione", "cartella_codici", "reset_testo", "reset_criteri"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Funzione per caricare un file
def carica_file(file, key):
    if file is not None:
        st.session_state[key] = file
        st.success(f"File '{file.name}' successfully uploaded!")

# Funzione per caricare una cartella
def carica_cartella(cartella):
    if cartella:
        st.session_state["cartella_codici"] = cartella
        st.success(f"Folder '{cartella}' successfully uploaded!")

# Funzione per eliminare file
def elimina_file(file_key):
    if file_key in st.session_state:
        st.session_state[file_key] = None

    if file_key == "testo_esame":
        st.session_state["reset_testo"] = True
        st.session_state["messaggio_eliminazione_testo"] = "Exam Text successfully deleted!"
    elif file_key == "criteri_correzione":
        st.session_state["reset_criteri"] = True
        st.session_state["messaggio_eliminazione_criteri"] = "Correction Criteria successfully deleted!"
    elif file_key == "cartella_codici":
        st.session_state["messaggio_eliminazione_cartella"] = "Student Codes Folder successfully deleted!"
    st.rerun()


# Tre colonne
col1, col2, col3 = st.columns(3)

# Testo d'esame
with col1:
    st.subheader("Exam Text")
    if st.session_state["reset_testo"]:
        testo_file = st.file_uploader("Upload PDF or .txt file", type=["pdf", "txt"], key="upload_testo_esame_" + str(os.urandom(4)))
        st.session_state["reset_testo"] = False
    else:
        testo_file = st.file_uploader("Upload PDF or .txt file", type=["pdf", "txt"], key="upload_testo_esame")

    if testo_file and st.session_state["testo_esame"] is None:
        carica_file(testo_file, "testo_esame")

    if st.session_state["testo_esame"]:
        st.write(f"📄 **File uploaded:** {st.session_state['testo_esame'].name}")
        st.download_button("💾 Download",
                           st.session_state["testo_esame"].getvalue(),
                           file_name=st.session_state["testo_esame"].name,
                           mime="application/pdf" if st.session_state["testo_esame"].name.endswith(".pdf") else "text/plain",
                           key="download_testo_esame")
        if st.button("🗑️ Delete Exam Text"):
            elimina_file("testo_esame")
    # Mostra messaggio di eliminazione dopo il rerun
    if "messaggio_eliminazione_testo" in st.session_state:
     st.success(st.session_state["messaggio_eliminazione_testo"])
     del st.session_state["messaggio_eliminazione_testo"]



# Criteri di correzione
with col2:
    st.subheader("Correction Criteria")
    if st.session_state["reset_criteri"]:
        criteri_file = st.file_uploader("Upload the .txt file", type=["txt"], key="upload_criteri_correzione_" + str(os.urandom(4)))
        st.session_state["reset_criteri"] = False
    else:
        criteri_file = st.file_uploader("Upload the .txt file", type=["txt"], key="upload_criteri_correzione")

    if criteri_file and st.session_state["criteri_correzione"] is None:
        carica_file(criteri_file, "criteri_correzione")

    if st.session_state["criteri_correzione"]:
        st.write(f"📄 **File uploaded:** {st.session_state['criteri_correzione'].name}")
        st.download_button("💾 Download",
                           st.session_state["criteri_correzione"].getvalue(),
                           file_name=st.session_state["criteri_correzione"].name,
                           mime="text/plain",
                           key="download_criteri_correzione")
        if st.button("🗑️ Delete Correction Criteria"):
            elimina_file("criteri_correzione")
    # Mostra messaggio di eliminazione dopo il rerun       
    if "messaggio_eliminazione_criteri" in st.session_state:
     st.success(st.session_state["messaggio_eliminazione_criteri"])
     del st.session_state["messaggio_eliminazione_criteri"]


# Cartella codici studenti
with col3:
    st.subheader("Student Codes")

    folder_path_input_key = "folder_path_input_key"
    folder_path = st.text_input(
        "Enter the path to the main folder containing student subfolders:",
        key=folder_path_input_key
    )

    if st.button("Load Student Codes Folder"):
        if folder_path:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                carica_cartella(folder_path) # Salva il percorso nella session_state
                # Resetta il campo di input dopo il caricamento, se desiderato
                # st.session_state[folder_path_input_key] = "" # Questo causerebbe un rerun immediato
            else:
                st.error("The provided path is not a valid folder. Please check the path and try again.")
        else:
            st.warning("Please enter a folder path.")

    # Visualizza la cartella caricata
    if st.session_state.get("cartella_codici"):
        # Ora ci aspettiamo sempre una stringa (percorso) qui
        if isinstance(st.session_state["cartella_codici"], str):
            st.write(f"📁 **Folder loaded:** {st.session_state['cartella_codici']}")
        # La logica per il dizionario di file è stata rimossa poiché ora carichiamo una cartella.

        if st.button("🗑️ Delete Student Codes"):
            elimina_file("cartella_codici")
    
    # Mostra messaggio di eliminazione
    if "messaggio_eliminazione_cartella" in st.session_state:
        st.success(st.session_state["messaggio_eliminazione_cartella"])
        del st.session_state["messaggio_eliminazione_cartella"]


# Spaziatura
st.write("\n" * 10)

# Pulsante per cambiare pagina
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("Go to the Correction Page", use_container_width=True):
        st.switch_page("pages/correction.py")
