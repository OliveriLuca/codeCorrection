import streamlit as st
import os
import base64
import openai
import anthropic
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import textwrap
import json

# Configurazione delle chiavi API usando Streamlit secrets
# Le chiavi vengono lette dai secrets di Streamlit per motivi di sicurezza
try:
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
except Exception:
    openai_api_key = None

try:
    anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY")
except Exception:
    anthropic_api_key = None

try:
    gemini_api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    gemini_api_key = None

# Inizializzazione dei client LLM
client = None
if openai_api_key:
    try:
        client = openai.OpenAI(api_key=openai_api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
else:
    st.warning("OpenAI API key not found. OpenAI features will be unavailable.", icon="⚠️")

anthropic_client = None
if anthropic_api_key:
    try:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    except Exception as e:
        st.error(f"Failed to initialize Anthropic client: {e}")
else:
    st.warning("Anthropic API key not found. Anthropic features will be unavailable.", icon="⚠️")

gemini_model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel(
            model_name='gemini-1.5-pro-latest',
            system_instruction="Sei un esperto di programmazione in C."
        )
    except Exception as e:
        st.error(f"Failed to configure or initialize Gemini API/Model: {e}")
        gemini_model = None # Ensure it's None on failure
else:
    st.warning("Gemini API key not found. Gemini features will be unavailable.", icon="⚠️")

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")

# Titolo principale della pagina
st.title("Correction Page")

# Creazione di due colonne di uguale dimensione per visualizzare i file PDF e i codici studenti
col1, col2 = st.columns(2)

# Funzione per eliminare un file dallo stato della sessione
def elimina_file(file_key):
    if file_key in st.session_state:
        del st.session_state[file_key]
        st.success(f"File '{file_key.replace('_', ' ')}' successfully deleted!")
        st.rerun()

# Funzione per eliminare la cartella caricata
def elimina_cartella():
    if "cartella_codici" in st.session_state:
        del st.session_state["cartella_codici"]
        st.success("Student Codes Folder Deleted Successfully!")
        st.rerun()

# Funzione per mostrare un'anteprima del PDF
def mostra_pdf(file):
    if file is not None:
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# Funzione per correzione automatica del codice C di uno studente tramite modelli LLM.
def correggi_codice(codice_studente, criteri, testo_esame, modello_scelto):
    # Crea il prompt da inviare al modello, includendo il testo dell'esame, i criteri di correzione e il codice dello studente.
    # Il modello deve rispondere ESCLUSIVAMENTE con un array JSON di oggetti errore.
    prompt = f"""
    Testo dell'esercizio (se presente):
    {textwrap.dedent(testo_esame) if testo_esame else "N/D"}

    Criteri di correzione:
    {textwrap.dedent(criteri)}
    
    Codice dello studente:
    ```c
    {codice_studente}
    ```
     Analizza il codice dello studente basandoti sui criteri di correzione e sul testo dell'esercizio.
    Restituisci ESCLUSIVAMENTE un array JSON contenente oggetti per ogni errore identificato. Ogni oggetto deve avere la seguente struttura:
    {{
      "line": "string",  // Il numero della riga (1-based) in cui si trova l'errore. Es: "4"
      "criteria": "string",  // La descrizione del criterio di correzione violato o dell'errore. Es: "NEVER ENTERS THE LOOP!"
      "point_deduction": number,  // La deduzione di punti per questo errore (es. -5).
      "inline_comment": "string"  // Un commento da inserire accanto alla riga di codice, formattato come "//******** CRITERIA_TEXT -POINTS_DEDUCTED". Es: "//******** NEVER ENTERS THE LOOP! -5"
    }}

    Esempio di output JSON (DEVE essere un array valido):
    [
      {{
        "line": "4",
        "criteria": "NEVER ENTERS THE LOOP!",
        "point_deduction": -5,
        "inline_comment": "//******** NEVER ENTERS THE LOOP! -5"
      }},
      {{
        "line": "12",
        "criteria": "Variabile non inizializzata",
        "point_deduction": -3,
        "inline_comment": "//******** Variabile non inizializzata -3"
      }}
    ]
    Se non ci sono errori, restituisci un array JSON vuoto: [].
    Non includere NESSUN testo al di fuori dell'array JSON nella tua risposta.
    """

    try:
        # Caso: utilizzo del modello GPT-4o di OpenAI
        if modello_scelto == "gpt-4o":
            if not client:
                return None, "Error: OpenAI client not initialized. Check API key."
            risposta = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sei un esperto di programmazione in C."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.2 # Puoi aggiungere o modificare la temperatura qui se necessario
            )
            # Restituisce il contenuto JSON e None per l'errore
            return risposta.choices[0].message.content, None

        # Caso: utilizzo del modello Claude 3.5 Sonnet di Anthropic
        elif modello_scelto == "claude-3.5-sonnet":
            if not anthropic_client:
                return None, "Error: Anthropic client not initialized. Check API key."
            risposta = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                temperature=0.2, # Già presente, corretto
                system="Sei un esperto di programmazione in C.",
                messages=[{"role": "user", "content": prompt}]
            )
            # Restituisce il contenuto JSON e None per l'errore
            return risposta.content[0].text, None

        # Caso: utilizzo del modello Gemini 1.5 Pro di Google
        elif modello_scelto == "gemini-1.5-pro-latest":
            if not gemini_model:
                return None, "Error: Gemini model not initialized. Check API key and configuration."
            try:
                response = gemini_model.generate_content( # Use the global gemini_model
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                return response.text, None
            except google_exceptions.ResourceExhausted as e:
                return None, "Error: You have exhausted your Gemini API quota. Check your Google Cloud project and billing details, or wait for the quota to reset."
            except google_exceptions.GoogleAPIError as e: 
                return None, f"Error API Gemini: {e}"
    # Gestione errori API OpenAI (es. fine quota)
    except openai.APIError as e:
        if "insufficient_quota" in str(e).lower():
            return None, "Error: You have exhausted your OpenAI quota. Check your plan or wait for monthly renewal."
        return None, f"Error API OpenAI: {e}"

    # Gestione errori API Anthropic (es. fine quota)
    except anthropic.APIStatusError as e:
        if "credit balance is too low" in str(e).lower(): # Modificato per riconoscere il messaggio di credito esaurito
            return None, "Error: You have exhausted your Anthropic quota. Check your plan or wait for monthly renewal."
        return None, f"Error API Claude: {e}"

    # Gestione di altri errori imprevisti
    except Exception as e:
        return None, f"Unexpected Error: {e}"

def evidenzia_errori_json(codice_studente, correzioni_json):
    righe_codice = codice_studente.split("\n")
    codice_modificato = ""

    # Organizza le correzioni per riga
    correzioni_per_riga = {}
    totale_deduzioni = 0

    try:
        correzioni = json.loads(correzioni_json)
        for cor in correzioni:
            linea = int(cor.get("line", -1))
            commento = cor.get("inline_comment", "")
            punti = cor.get("point_deduction", 0)
            totale_deduzioni += punti
            if 0 <= linea - 1 < len(righe_codice): # Correct for 1-based line number
                correzioni_per_riga[linea - 1] = commento
    except Exception as e:
        return codice_studente, 0, f"Errore parsing JSON: {e}"

    # Aggiunge i commenti alle righe corrette
    for i, riga in enumerate(righe_codice):
        commento = correzioni_per_riga.get(i, "")
        if commento:
            codice_modificato += f"{riga}    {commento}\n"
        else:
            codice_modificato += f"{riga}\n"

    return codice_modificato, totale_deduzioni, None

# --- Sezione Interfaccia Utente ---

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    st.header("Student codes")
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        cartella = st.session_state["cartella_codici"]
        st.write(f"\U0001F4C1 **Folder loaded:** {cartella}")

        if not os.path.exists(cartella) or not os.listdir(cartella):
            st.warning("The uploaded folder does not contain valid files.")
        else:
            sottocartelle = [d for d in os.listdir(cartella) if os.path.isdir(os.path.join(cartella, d))]

            if sottocartelle:
                sottocartella_scelta = st.selectbox("Select a student:", sottocartelle)
                percorso_cartella_scelta = os.path.join(cartella, sottocartella_scelta)
                
                # Trova il file .c e salvalo nello stato della sessione se non già presente per questo studente
                if "selected_student_folder" not in st.session_state or st.session_state["selected_student_folder"] != percorso_cartella_scelta:
                    st.session_state["selected_student_folder"] = percorso_cartella_scelta
                    st.session_state["selected_c_file_path"] = None
                    st.session_state["codice_studente_originale"] = ""
                    st.session_state["codice_studente_modificato"] = "" # Usiamo questo per l'area di testo editabile
                    st.session_state["correzioni_json"] = None # Resetta le correzioni quando cambia studente

                    file_c_name = None
                    for file in os.listdir(percorso_cartella_scelta):
                        if file.endswith(".c"):
                            file_c_name = file
                            break

                    if file_c_name:
                        percorso_file = os.path.join(percorso_cartella_scelta, file_c_name)
                        st.session_state["selected_c_file_path"] = percorso_file
                        with open(percorso_file, "r", encoding="utf-8") as codice_file:
                            codice = codice_file.read()
                        st.session_state["codice_studente_originale"] = codice
                        st.session_state["codice_studente_modificato"] = codice # Inizializza l'area di testo con l'originale
                    else:
                         st.warning("No .c files found in the selected folder.")
                         st.session_state["selected_c_file_path"] = None # Assicurati che sia None se non trovato

                # Visualizza l'area di testo editabile solo se un file .c è stato trovato e caricato
                if st.session_state.get("selected_c_file_path"):

                    # Riquadro editabile
                    current_c_file_name = os.path.basename(st.session_state["selected_c_file_path"])
                    codice_modificato = st.text_area(
                        f"Content of {current_c_file_name}",
                        st.session_state["codice_studente_modificato"],
                        height=200
                    )

                    # Aggiorna lo stato della sessione con il contenuto modificato dall'utente
                    st.session_state["codice_studente_modificato"] = codice_modificato

                    # Pulsante di download per il codice modificato
                    cognome_nome = sottocartella_scelta.replace(" ", "_") # Assicurati che sottocartella_scelta sia ancora disponibile qui
                    # Suggested change for clearer filename:
                    # nome_file_salvato = f"{cognome_nome}_{os.path.splitext(current_c_file_name)[0]}_corrected.c"
                    # Using a simpler version for now, but consider the above for more specificity.
                    nome_file_salvato_corrected = f"{cognome_nome}_corrected.c"
                    st.download_button("💾 Save code", codice_modificato, file_name=nome_file_salvato_corrected, mime="text/plain")
                else:
                    st.warning("No .c files found in the selected folder.")
            else:
                st.warning("No subfolders found in the parent folder.")
    else:
        st.warning("No folder loaded for student codes.")

    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        if st.button("🗑️ Delete Student Codes Folder"):
            elimina_cartella()

    # Sezione per la correzione con LLM
    # Prepara una variabile di default per i criteri
    criteri = ""
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
     file = st.session_state["criteri_correzione"]
     # Carica il contenuto solo se non è già nello stato o se il file è cambiato
     if "criteri_modificati" not in st.session_state or st.session_state.get("criteri_file_name") != file.name:
         st.session_state["criteri_modificati"] = file.getvalue().decode("utf-8") # Assuming UTF-8 for criteria
         st.session_state["criteri_file_name"] = file.name

     criteri = st.session_state["criteri_modificati"] # Usa il contenuto dallo stato

    # Abilita la sezione di correzione solo se ci sono codici studente caricati, criteri e uno studente/file selezionato
    if st.session_state.get("cartella_codici") and st.session_state.get("criteri_modificati") and st.session_state.get("selected_c_file_path"):

            modello_scelto = st.radio(
                "Select the template to use for correction:",
                ["gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro-latest"],
                horizontal=True
            )

            # Visualizzazione del codice e degli errori
            if st.button("🤖 Correct"):
                st.session_state["correzioni_json"] = None # Resetta correzioni precedenti
                st.session_state["api_error_message"] = None # Resetta errori API precedenti

                criteri = st.session_state.get("criteri_modificati", "")
                testo_esame = st.session_state.get("testo_modificato", "")
                codice = st.session_state.get("codice_studente_modificato", "") # Usa il codice dall'area di testo editabile
                llm_response_content, api_or_model_error = correggi_codice(codice, criteri, testo_esame, modello_scelto)

                if api_or_model_error:
                    st.session_state["api_error_message"] = api_or_model_error
                elif llm_response_content:
                    st.session_state["correzioni_json"] = llm_response_content
                else:
                    # Caso in cui non ci sono né errore né contenuto, dovrebbe essere raro
                    st.session_state["api_error_message"] = "Received an empty response from the model."

                # st.rerun() # This is likely redundant as Streamlit reruns after button press

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Correction Criteria")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        st.write(f"**File uploaded:** {file.name}")

        # Visualizza il contenuto del file .txt
        # Carica il contenuto solo se non è già nello stato o se il file è cambiato
        if "criteri_modificati" not in st.session_state or st.session_state.get("criteri_file_name") != file.name:
            testo = file.getvalue().decode("utf-8")
            st.session_state["criteri_modificati"] = testo

        criteri_editabili = st.text_area("Content of the Correction Criteria", st.session_state["criteri_modificati"], height=300)

        # Aggiorna lo stato della sessione con il contenuto modificato
        st.session_state["criteri_modificati"] = criteri_editabili

        # Pulsanti per scaricare ed eliminare il file
        if st.download_button("💾 Save Correction Criteria", st.session_state["criteri_modificati"], file_name=file.name, mime="text/plain"):
            st.success("File downloaded successfully with changes made!")

        if st.button("🗑️ Delete Correction Criteria"):
            elimina_file("criteri_correzione")
            # Pulisci anche lo stato associato
            if "criteri_modificati" in st.session_state:
                del st.session_state["criteri_modificati"]
            if "criteri_file_name" in st.session_state:
                del st.session_state["criteri_file_name"]
            # Resetta le correzioni se i criteri vengono eliminati
            st.session_state["correzioni_json"] = None
            st.session_state["api_error_message"] = None

    else:
        st.warning("No files uploaded for correction criteria.")

# Linea di separazione tra le sezioni
st.divider()

# Creazione di una colonna centrale per il Testo d'Esame
spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

#Sezione per visualizzazione testo d'esame
with col3:
    st.header("Exam Text")
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        file = st.session_state["testo_esame"]
        st.write(f"**File uploaded:** {file.name}")

        # Verifica se il file è un PDF
        if file.name.endswith(".pdf"):
            mostra_pdf(file)

            # Modifica il tipo MIME per i PDF
            # Non ha senso "salvare con modifiche" un PDF visualizzato così, il download è dell'originale
            st.download_button("💾 Download Exam Text", file.getvalue(), file_name=file.name, mime="application/pdf")


        # Se il file è un file di testo (modificabile)
        elif file.name.endswith(".txt"):
            testo = file.getvalue().decode("utf-8") # Assuming UTF-8 for exam text
            if "testo_modificato" not in st.session_state:
                st.session_state["testo_modificato"] = testo

            testo_modificato = st.text_area("Content of the Exam Text", st.session_state["testo_modificato"], height=300)

            # Aggiorna lo stato della sessione con il contenuto modificato
            st.session_state["testo_modificato"] = testo_modificato

            # Pulsante per il download del testo
            if st.download_button("💾 Save Exam Text ", testo_modificato, file_name=file.name, mime="text/plain"):
                st.success("Text file downloaded successfully!")

        # Pulsante per eliminare il file
        if st.button("🗑️ Delete Exam Text"):
            elimina_file("testo_esame")
            if "testo_modificato" in st.session_state:
                # Pulisci anche lo stato associato
                del st.session_state["testo_modificato"]
            if "testo_file_name" in st.session_state:
                del st.session_state["testo_file_name"]
    else:
        st.warning("No file uploaded for the exam text.")

# Sezione per visualizzare i risultati della correzione (sotto le aree di input)
api_error_msg = st.session_state.get("api_error_message")
correzioni_json_str = st.session_state.get("correzioni_json")

if api_error_msg:
    st.divider()
    st.header("Correction Attempt Failed")
    st.error(api_error_msg)
elif correzioni_json_str:
    st.divider()
    st.header("Correction Results")
    codice_originale_o_modificato = st.session_state.get("codice_studente_modificato", "") 

    codice_evidenziato, totale_deduzioni, parsing_error = evidenzia_errori_json(codice_originale_o_modificato, correzioni_json_str)

    if parsing_error:
        st.error(f"Could not process LLM response: {parsing_error}")
        st.write("Raw LLM output that caused the parsing error:")
        st.code(correzioni_json_str) 
    else:
        st.write(f"### 🔍 Total Point Deduction: `{totale_deduzioni}`")
        st.code(codice_evidenziato, language="c")
        try:
            st.json(json.loads(correzioni_json_str)) 
        except json.JSONDecodeError:
            st.warning("Could not display raw JSON output as it's not valid, despite successful initial parsing.")
            st.code(correzioni_json_str)

# Aggiunge più spazio vuoto per spingere il bottone verso il basso
for _ in range(10):
    st.write("")

# Creazione di colonne per centrare il pulsante
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Return to the material upload page", use_container_width=True):
        st.switch_page("loading.py")

# Aggiunge ancora più spazio sotto il pulsante
for _ in range(5):
    st.write("")
