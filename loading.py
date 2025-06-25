import streamlit as st
import os
import zipfile
import io

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

# Funzione per processare il file .zip
def process_zip_file(uploaded_file):
    student_files = {}
    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                # Cerca file .c in sottocartelle, ignorando i metadati di macOS
                if file_info.filename.endswith('.c') and not file_info.filename.startswith('__MACOSX'):
                    parts = file_info.filename.split('/')
                    if len(parts) > 1:
                        student_name = parts[0]
                        file_content = io.BytesIO(zip_ref.read(file_info.filename))
                        file_content.name = os.path.basename(file_info.filename)
                        student_files[student_name] = file_content
    except zipfile.BadZipFile:
        st.error("The uploaded file is not a valid .zip file.")
        return None
    except Exception as e:
        st.error(f"An error occurred while processing the zip file: {e}")
        return None
    return student_files

# Funzione per eliminare file
def elimina_file(file_key):
    if file_key in st.session_state:
        del st.session_state[file_key]

    if file_key == "testo_esame":
        st.toast("✅ Exam Text successfully deleted!", icon="🗑️")
        st.session_state["reset_testo"] = True
    elif file_key == "criteri_correzione":
        st.toast("✅ Correction Criteria successfully deleted!", icon="🗑️")
        st.session_state["reset_criteri"] = True
    elif file_key == "cartella_codici":
        st.toast("✅ Student Codes successfully deleted!", icon="🗑️")
        if "zip_file_object" in st.session_state:
            del st.session_state["zip_file_object"]
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

# Cartella codici studenti
with col3:
    st.subheader("Student Codes")
    
    zip_file = st.file_uploader(
        "Upload a .zip file with student subfolders",
        type=["zip"],
        key="upload_student_codes_zip"
    )

    if zip_file and st.session_state.get("cartella_codici") is None:
        student_codes_dict = process_zip_file(zip_file)
        if student_codes_dict:
            st.session_state["cartella_codici"] = student_codes_dict
            st.session_state["zip_file_object"] = zip_file
            st.success(f"File '{zip_file.name}' processed. Found code for {len(student_codes_dict)} students.")
            st.rerun()

    # Visualizza lo zip caricato
    if st.session_state.get("cartella_codici"):
        if isinstance(st.session_state["cartella_codici"], dict):
            zip_obj = st.session_state.get("zip_file_object")
            if zip_obj:
                st.write(f"📄 **File uploaded:** {zip_obj.name}")
                st.write(f"👥 **Students found:** {len(st.session_state['cartella_codici'])}")
                
                st.download_button("💾 Download ZIP", zip_obj.getvalue(), file_name=zip_obj.name, mime="application/zip")
                if st.button("🗑️ Delete Student Codes"):
                    elimina_file("cartella_codici")
    

# Spaziatura
st.write("\n" * 10)

# Pulsante per cambiare pagina
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("Go to the Correction Page", use_container_width=True):
        st.switch_page("pages/correction.py")
