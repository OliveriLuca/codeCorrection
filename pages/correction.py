import streamlit as st
import os
import base64
import openai
import textwrap
import re 
import json

# Configurazione della chiave API OpenRouter usando Streamlit secrets
# OpenRouter fornisce accesso unificato a più modelli LLM
try:
    openrouter_api_key = st.secrets.get("openrouter_api_key")
except Exception:
    print("OpenRouter API key not found.")

# Inizializzazione del client OpenRouter (usa l'API OpenAI-compatibile)
client = None
if openrouter_api_key:
    try:
        client = openai.OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    except Exception as e:
        st.error(f"Failed to initialize OpenRouter client: {e}")
else:
    st.warning("OpenRouter API key not found. LLM features will be unavailable.", icon="⚠️")

st.set_page_config(layout="wide")
st.title("Correction Page")
col1, col2 = st.columns(2)

# Funzione per resettare gli stati relativi alla visualizzazione della correzione
def reset_correction_display_states():
    keys_to_delete = [
        "correzioni_json_originale_llm", "api_error_message",
        "lista_oggetti_errore_iniziali", "codice_corretto_editabile",
        "punteggio_attuale", "json_attuale_da_visualizzare",
        "last_processed_llm_json"
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]


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
def correggi_codice(codice_studente, criteri, testo_esame, modello_scelto, client):
    # Crea il prompt da inviare al modello, includendo il testo dell'esame, i criteri di correzione e il codice dello studente.
    # Il modello deve rispondere ESCLUSIVAMENTE con un array JSON di oggetti errore.
    prompt = f"""
    Exam Text (if present):
    {textwrap.dedent(testo_esame) if testo_esame else "N/D"}

    Criteri di correzione:
    {textwrap.dedent(criteri)}
    
    Codice dello studente:
    ```c
    {codice_studente}
    ```
     ##1.Istruzioni e regole di valutazione:
     Rivedi i dettagli dell'assegnazione e la griglia di valutazione in modo approfondito. 
     Analizza la sottomissione del codice dello studente rispetto a ciascun criterio.
     Valuta SOLO in base ai criteri di correzione forniti.
     Aggiungi commenti in-line posizionandoli direttamente dopo la riga di codice pertinente. 
     Non modificare o correggere il codice dello studente. 
     Mantieni l'oggettività ed evita preferenze personali di codifica. 
     Non rimuovere punti per errori di battitura. Fornisci feedback specifico e attuabile.
     
     ##2. Formato dell'output:
     Restituisci ESCLUSIVAMENTE un array JSON contenente oggetti per ogni errore identificato.
     
     Ogni oggetto deve avere la seguente struttura:
    {{
      "line": "string",  // Il numero della riga (1-based) in cui si trova l'errore. Es: "4".
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
        # Utilizzo generico di qualsiasi modello tramite OpenRouter
        if not client:
            return None, "Error: OpenRouter client not initialized. Check API key."
        
        # Parametri per la generazione della risposta LLM
        max_tokens = 2048 # Massimo numero di token che il modello può generare nella risposta.
        temperature = 0.2 # Controlla la casualità della risposta: valori più bassi la rendono più focalizzata e deterministica.
        
            
        risposta = client.chat.completions.create(
            model=modello_scelto,
            messages=[
                {"role": "system", "content": "Sei un esperto di programmazione in C."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return risposta.choices[0].message.content, None

    # Gestione errori API OpenRouter
    except openai.APIError as e:
        if "insufficient_quota" in str(e).lower() or "credit" in str(e).lower():
            return None, "Error: You have exhausted your OpenRouter quota. Check your plan or wait for monthly renewal."
        elif "model not found" in str(e).lower():
            return None, f"Error: Model '{modello_scelto}' not found on OpenRouter. Please check the model name."
        return None, f"Error API OpenRouter: {e}"

    # Gestione di altri errori imprevisti
    except Exception as e:
        return None, f"Unexpected Error: {e}"

def evidenzia_errori_json(codice_c, correzioni_json_str):
    try:
        # Tenta di parsare la stringa JSON.
        # È cruciale che correzioni_json_str sia un JSON valido qui.
        dati_correzione = json.loads(correzioni_json_str)
        if not isinstance(dati_correzione, list): # LLM is instructed to return a list
            # Il prompt si aspetta un array JSON. Se non è una lista, trattalo come errore.
            raise json.JSONDecodeError("Expected a JSON array (list) from LLM.", correzioni_json_str, 0)
    
    except json.JSONDecodeError as e:
        # Se il parsing JSON fallisce, restituisci il codice originale con un commento di errore
        # e l'errore di parsing stesso.
        messaggio_errore_parsing = f"/* Error parsing LLM JSON response: {str(e)}. \n   Raw response was: \n{correzioni_json_str}\n*/"
        codice_con_errore_parsing = codice_c + "\n\n" + messaggio_errore_parsing
        return codice_con_errore_parsing, 0, str(e), None # Aggiunto None per i dati parsati

    codice_lines = codice_c.split('\n')
    totale_deduzioni = 0
    # Memorizza le annotazioni per riga. Una riga può avere più commenti.
    annotazioni_per_linea = {}  # Usa int come chiave (numero di riga 1-based)

    for item in dati_correzione:
        if not isinstance(item, dict):
            # Ogni elemento nell'array dovrebbe essere un oggetto (dict).
            # Salta elementi malformati o registra un avviso se necessario.
            continue

        line_str = item.get("line")
        point_deduction_val = item.get("point_deduction", 0)
        inline_comment = item.get("inline_comment") # Commento pre-formattato dall'LLM

        try:
            # Somma le deduzioni di punti (assicurati che point_deduction sia un numero)
            totale_deduzioni += float(point_deduction_val)
        except (ValueError, TypeError):
            # Gestisci i casi in cui point_deduction potrebbe non essere un numero valido
            # o registra questo come un problema con il formato di output dell'LLM.
            pass

        if line_str and inline_comment:
            try:
                line_num_int = int(line_str)  # Converte il numero di riga stringa in int
                if line_num_int <= 0:  # I numeri di riga sono tipicamente basati su 1
                    continue  # Salta numeri di riga non validi

                # Aggiunge il commento alla lista per questa riga
                annotazioni_per_linea.setdefault(line_num_int, []).append(inline_comment)
            except ValueError:
                # Gestisci i casi in cui line_str non è una stringa intera valida.
                pass # Salta questa annotazione di errore

    # Aggiungi commenti alle righe di codice
    codice_evidenziato_lines = []
    for i, line_content in enumerate(codice_lines, start=1):
        current_line_with_comments = line_content
        if i in annotazioni_per_linea:
            for comment in annotazioni_per_linea[i]:
                current_line_with_comments += f" {comment}" # Aggiunge spazio prima del commento
        codice_evidenziato_lines.append(current_line_with_comments)

    codice_evidenziato_final = "\n".join(codice_evidenziato_lines)
    return codice_evidenziato_final, totale_deduzioni, None, dati_correzione # Restituisci la lista parsata

def ricostruisci_errori_da_testo_commentato(testo_editato_con_commenti):
    """
    Analizza il testo del codice (che può contenere commenti di errore)
    per estrarre tutti gli errori formattati, ricalcolare il punteggio
    e generare una nuova lista di oggetti errore.
    Il formato del commento atteso è: //******** CRITERIA_TEXT -POINTS_DEDUCTED
    """
    # Pattern per catturare l'intero commento di errore formattato (ora flessibile sul numero di asterischi).
    pattern_full_comment_capture = r"(//\*+[^\r\n]*?-?\d+(?:\.\d+)?)"
    # Pattern per parsare i dettagli (criterio e punti) dall'intero commento catturato.
    # Gruppo 1: Testo del criterio (e.g., "NEVER ENTERS THE LOOP!")
    # Gruppo 2: Punti dedotti (e.g., "-5")
    pattern_dettagli_commento = r"//\*+\s*(.*?)\s*(-?\d+(?:\.\d+)?)(?:\s*\*+)?$"

    errori_ricostruiti = []
    punteggio_ricalcolato = 0

    if testo_editato_con_commenti:
        righe_codice = testo_editato_con_commenti.splitlines() # More robust for line endings
        for idx, riga_contenuto in enumerate(righe_codice, start=1):
            # Trova tutti i commenti di errore formattati sulla riga
            commenti_trovati_nella_riga = re.findall(pattern_full_comment_capture, riga_contenuto)

            for commento_intero_trovato in commenti_trovati_nella_riga:
                match_dettagli = re.search(pattern_dettagli_commento, commento_intero_trovato.strip())
                if match_dettagli:
                    criterio = match_dettagli.group(1).strip()
                    punti_str = match_dettagli.group(2)
                    try:
                        punti = float(punti_str)
                        errori_ricostruiti.append({
                            "line": str(idx),  # Numero di riga (1-based) dove il commento è stato trovato
                            "criteria": criterio,
                            "point_deduction": punti,
                            "inline_comment": commento_intero_trovato.strip() # Il commento completo come trovato
                        })
                        punteggio_ricalcolato += punti
                    except ValueError:
                        # Impossibile convertire i punti in numero, ignora questo commento per il calcolo.
                        # Potrebbe essere utile loggare questo caso se si verificasse frequentemente.
                        pass
    
    return punteggio_ricalcolato, errori_ricostruiti

# --- Funzioni Helper per l'analisi dei punteggi per funzione ---
def find_c_function_definitions(code_string):
    """
    Identifica le definizioni delle funzioni in una stringa di codice C.
    Restituisce una lista di dizionari, ognuno con "name", "start_line", "end_line".
    Limitazione: Semplice parser basato su regex; potrebbe non coprire tutti i casi C complessi.
    """
    lines = code_string.splitlines()
    functions = []
    # Regex per identificare una definizione di funzione (semplificata)
    # Cattura: tipo di ritorno (molto generico), nome funzione, parametri
    # Assume che la parentesi graffa aperta '{' sia sulla stessa riga della definizione.
    func_def_pattern = re.compile(
        r"^\s*([\w\s\*&]+(?:\[\s*\])?)\s+"  # Tipo di ritorno (parole, spazi, *, &, opzionale [])
        r"([a-zA-Z_]\w*)\s*"              # Nome funzione
        r"\(([^)]*)\)\s*(?:const)?\s*(?:(?:/\*.*?\*/)|(?://[^\r\n]*))*\s*\{"  # Parametri, commenti opzionali, e {
    )

    for i, line_content in enumerate(lines):
        match = func_def_pattern.match(line_content)
        if match:
            func_name = match.group(2)
            start_line_num = i + 1  # 1-based
            
            # Trova la fine della funzione contando le parentesi graffe
            brace_level = 1 # Per la { di apertura della funzione
            # Contenuto sulla stessa riga dopo la {
            content_after_opening_brace = line_content[match.end():]
            brace_level += content_after_opening_brace.count('{')
            brace_level -= content_after_opening_brace.count('}')

            end_line_num = -1
            if brace_level == 0: # Corpo della funzione terminato sulla stessa riga
                end_line_num = start_line_num
            else: # Corpo della funzione su più righe
                for j in range(i + 1, len(lines)): # Inizia dalla riga successiva
                    current_line_in_body = lines[j]
                    brace_level += current_line_in_body.count('{')
                    brace_level -= current_line_in_body.count('}')
                    if brace_level == 0:
                        end_line_num = j + 1 # 1-based
                        break
            
            if end_line_num != -1:
                functions.append({
                    "name": func_name,
                    "start_line": start_line_num,
                    "end_line": end_line_num
                })
    return functions

def parse_criteria_function_scores(criteria_text):
    """
    Estrae i punteggi base per funzione dal testo dei criteri.
    Formato atteso: "nome_funzione: punteggio" (es. "massimoPari: 5.0").
    Restituisce un dizionario {nome_funzione: punteggio_base}.
    """
    scores = {}
    pattern = re.compile(r"^\s*([a-zA-Z_]\w*)\s*:\s*(\d+(?:\.\d+)?)\s*(?:#.*)?$")
    for line in criteria_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            func_name = match.group(1)
            score = float(match.group(2))
            scores[func_name] = score
    return scores

def display_detailed_function_scores(student_code, criteria_text, error_list):
    """
    Calcola e visualizza i punteggi dettagliati per ogni funzione.
    """
    defined_functions = find_c_function_definitions(student_code)
    criteria_scores = parse_criteria_function_scores(criteria_text)

    if not defined_functions:
        st.info("No function definitions found in the student's code to analyze for detailed scores.")
        return

    st.markdown("---")
    st.subheader("Detailed Scores per Function:")

# --- Sezione Interfaccia Utente ---

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        student_data = st.session_state["cartella_codici"]
        # Controlla se è il nuovo formato (dizionario di file) o il vecchio formato (percorso cartella)
        if isinstance(student_data, dict):
            # Nuovo formato: dizionario di file studente
            st.write(f"\U0001F4C1 **Student files loaded:** {len(student_data)} students")
            
            if student_data:
                # Ottieni la lista dei nomi degli studenti
                student_names = list(student_data.keys())
                selected_student = st.selectbox("Select a student:", student_names)
                
                if selected_student:
                    # Ottieni il file per lo studente selezionato
                    selected_file = student_data[selected_student]
                    
                    # Resetta lo stato della sessione quando lo studente cambia
                    if "selected_student_name" not in st.session_state or st.session_state["selected_student_name"] != selected_student:
                        st.session_state["selected_student_name"] = selected_student
                        st.session_state["selected_c_file_path"] = selected_file.name
                        st.session_state["codice_studente_originale"] = selected_file.getvalue().decode("utf-8")
                        st.session_state["codice_studente_modificato"] = selected_file.getvalue().decode("utf-8")
                        reset_correction_display_states()


                    
                    # Visualizza l'area di testo editabile
                    codice_modificato = st.text_area(
                        f"Content of {selected_file.name}",
                        st.session_state["codice_studente_modificato"],
                        height=200
                    )
                    
                    # Aggiorna lo stato della sessione con il contenuto modificato
                    st.session_state["codice_studente_modificato"] = codice_modificato
                    
                    # Pulsante di download per il codice modificato

                    student_name_part = selected_student
                    original_file_base = os.path.splitext(selected_file.name)[0] # Original filename without extension

                    student_prefix_to_check = student_name_part + "_"
                    if original_file_base.startswith(student_prefix_to_check):
                        # L'originale era tipo "Mario_Rossi_Lab1.c". Vogliamo salvare come "Mario_Rossi_Lab1.c".
                        # In questo caso, original_file_base è "Mario_Rossi_Lab1".
                        nome_file_salvato = f"{original_file_base}.c"
                    else:
                        # L'originale era tipo "Lab1.c" (original_file_base è "Lab1")
                        # o "Mario_Rossi.c" (original_file_base è "Mario_Rossi").
                        # Vogliamo "Mario_Rossi_Lab1.c" o "Mario_Rossi_Mario_Rossi.c".
                        nome_file_salvato = f"{student_name_part}_{original_file_base}.c"
                    st.download_button("💾 Save code", codice_modificato, file_name=nome_file_salvato, mime="text/plain")
            else:
                st.warning("No student files found.")
                
        else:
            # Vecchio formato: percorso cartella (per compatibilità all'indietro)
            cartella = student_data
            st.write(f"\U0001F4C1 **Folder loaded:** {cartella}")

            if not os.path.exists(cartella) or not os.listdir(cartella):
                st.warning("The uploaded folder does not contain valid files.")
            else:
                sottocartelle = [d for d in os.listdir(cartella) if os.path.isdir(os.path.join(cartella, d))]

                if sottocartelle:
                    sottocartella_scelta = st.selectbox("Select a student:", sottocartelle)
                    percorso_cartella_scelta = os.path.join(cartella, sottocartella_scelta)
                    # Trova il file .c e salvalo nello stato della sessione se non è già presente per questo studente
                    if "selected_student_folder" not in st.session_state or st.session_state["selected_student_folder"] != percorso_cartella_scelta:
                        st.session_state["selected_student_folder"] = percorso_cartella_scelta
                        st.session_state["selected_c_file_path"] = None
                        st.session_state["codice_studente_originale"] = ""
                        st.session_state["codice_studente_modificato"] = ""
                        reset_correction_display_states()

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
                            st.session_state["codice_studente_modificato"] = codice
                        else:
                             st.warning("No .c files found in the selected folder.")
                             st.session_state["selected_c_file_path"] = None

                    # Visualizza l'area di testo editabile solo se un file .c è stato trovato e caricato
                    if st.session_state.get("selected_c_file_path"):
                        current_c_file_name = os.path.basename(st.session_state["selected_c_file_path"])
                        codice_modificato = st.text_area(
                            f"Content of {current_c_file_name}",
                            st.session_state["codice_studente_modificato"],
                            height=200
                        )

                        # Aggiorna lo stato della sessione con il contenuto modificato
                        st.session_state["codice_studente_modificato"] = codice_modificato

                        # Pulsante di download per il codice modificato
                        cognome_nome = sottocartella_scelta.replace(" ", "_")
                        
                        student_name_part_old_format = cognome_nome
                        # current_c_file_name è già definito sopra come os.path.basename(st.session_state["selected_c_file_path"])
                        task_name_from_file = os.path.splitext(current_c_file_name)[0]
                        nome_file_salvato = f"{student_name_part_old_format}_{task_name_from_file}.c"
                        st.download_button("💾 Save code", codice_modificato, file_name=nome_file_salvato, mime="text/plain")
                    else:
                        st.warning("No .c files found in the selected folder.")
                else:
                    st.warning("No subfolders found in the parent folder.")
    else:
        st.warning("No student codes loaded.")

    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        if st.button("🗑️ Delete Student Codes"):
            elimina_cartella()

    # Sezione per la correzione con LLM
    # Prepara una variabile di default per i criteri
    criteri = ""
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
     file = st.session_state["criteri_correzione"]
     # Carica il contenuto solo se non è già nello stato o se il file è cambiato
     if "criteri_modificati" not in st.session_state or st.session_state.get("criteri_file_name") != file.name:
         st.session_state["criteri_modificati"] = file.getvalue().decode("utf-8") # Assumendo UTF-8 per i criteri
         st.session_state["criteri_file_name"] = file.name

     criteri = st.session_state["criteri_modificati"] # Usa il contenuto dallo stato

    # Abilita la sezione di correzione solo se ci sono codici studente caricati, criteri e uno studente/file selezionato
    student_codes_available = st.session_state.get("cartella_codici") and st.session_state.get("criteri_modificati")
    student_selected = False
    
    if student_codes_available:
        # Controlla se è il nuovo formato (dizionario) o il vecchio formato (percorso cartella)
        if isinstance(st.session_state["cartella_codici"], dict):
            # Nuovo formato: controlla se uno studente è selezionato
            student_selected = st.session_state.get("selected_student_name") is not None
        else:
            # Vecchio formato: controlla se un percorso file è selezionato
            student_selected = st.session_state.get("selected_c_file_path") is not None
    
    if student_codes_available and student_selected:

            # Selezione del modello con deepseek come predefinito
            model_options = [
                "deepseek/deepseek-chat-v3-0324",
                "openai/gpt-4o", 
                "anthropic/claude-3.5-sonnet", 
                "google/gemini-flash-1.5",
                "Custom Model"
            ]
            
            selected_option = st.selectbox(
                "Select the model to use for correction:",
                model_options,
                index=0  # Imposta "deepseek/deepseek-chat-v3-0324" come opzione predefinita
            )
            
            if selected_option == "Custom Model":
                modello_scelto = st.text_input(
                    "Enter custom model name:",
                    placeholder="e.g., anthropic/claude-3-haiku"
                )
            else:
                modello_scelto = selected_option

            # Mostra il pulsante di correzione solo se un modello è selezionato
            if modello_scelto:
                # Visualizzazione del codice e degli errori
                if st.button("🤖 Correct"):
                    reset_correction_display_states()

                    criteri = st.session_state.get("criteri_modificati", "")
                    testo_esame = st.session_state.get("testo_modificato", "")
                    codice = st.session_state.get("codice_studente_modificato", "") # Usa il codice dall'area di testo editabile
                    llm_response_content, api_or_model_error = correggi_codice(codice, criteri, testo_esame, modello_scelto, client)

                    if api_or_model_error:
                        st.session_state["api_error_message"] = api_or_model_error
                        reset_correction_display_states() # Assicura che la UI sia pulita in caso di errore API
                    elif llm_response_content is not None:
                        processed_response = llm_response_content.strip()
                        
                        # Rimuovi UTF-8 BOM se presente
                        if processed_response.startswith('\ufeff'):
                            processed_response = processed_response[1:]

                        # Tenta di estrarre il contenuto JSON da un blocco di codice Markdown
                        # Cerca ```json ... ``` o ``` ... ```
                        # Il regex cattura il contenuto tra i delimitatori.
                        # Gestisce il specificatore di linguaggio "json" opzionale e spazi/newline circostanti.
                        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", processed_response)
                        if match:
                            extracted_json_str = match.group(1).strip() # Ottieni il contenuto e fai lo strip
                        else:
                            extracted_json_str = processed_response # Supponi sia JSON grezzo o qualcos'altro
                            
                        if extracted_json_str: # Se non è vuoto dopo lo strip e la rimozione del BOM/Markdown
                            # La risposta non è vuota. Verrà passata a evidenzia_errori_json.
                            # Se è ancora JSON non valido (es. "abc" o malformato), 
                            # evidenzia_errori_json intercetterà l'errore di parsing e lo segnalerà.                            
                            st.session_state["correzioni_json_originale_llm"] = extracted_json_str
                            st.session_state["api_error_message"] = None # Assicurati sia pulito
                        else:
                            st.session_state["api_error_message"] = "LLM returned an empty response or content that became empty after attempting to extract JSON from potential Markdown. Expected a JSON array."
                    else: # llm_response_content is None (and api_or_model_error was not set by correggi_codice)
                        st.session_state["api_error_message"] = "Received no response content from the LLM (response was None)."
            else:
                st.warning("Please select or enter a model name to proceed with correction.")

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
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
            reset_correction_display_states()


    else:
        st.warning("No files uploaded for correction criteria.")

st.divider()

spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

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
            testo = file.getvalue().decode("utf-8") # Assumendo UTF-8 per il testo d'esame
            # Aggiorna testo_modificato se non esiste, o se il nome del file caricato è cambiato
            if "testo_modificato" not in st.session_state or st.session_state.get("testo_file_name") != file.name:
                st.session_state["testo_modificato"] = testo
                st.session_state["testo_file_name"] = file.name # Traccia il nome del file per testo_modificato

            testo_modificato = st.text_area("Content of the Exam Text", st.session_state["testo_modificato"], height=300)

            # Aggiorna lo stato della sessione con il contenuto modificato
            st.session_state["testo_modificato"] = testo_modificato

            # Pulsante per il download del testo
            if st.download_button("💾 Save Exam Text ", testo_modificato, file_name=file.name, mime="text/plain"):
                st.success("Text file downloaded successfully!")

        # Pulsante per eliminare il file
        if st.button("🗑️ Delete Exam Text"):
            elimina_file("testo_esame")
            if "testo_modificato" in st.session_state: # Pulisci anche lo stato associato
                del st.session_state["testo_modificato"]
            if "testo_file_name" in st.session_state: # Assicurati che anche questo venga pulito
                del st.session_state["testo_file_name"]
    else:
        st.warning("No file uploaded for the exam text.")

# Sezione per visualizzare i risultati della correzione (sotto le aree di input)
api_error_msg = st.session_state.get("api_error_message")
json_originale_llm = st.session_state.get("correzioni_json_originale_llm")

if api_error_msg:
    st.divider()
    st.header("Correction Attempt Failed")
    st.error(api_error_msg)
    # Pulisci qualsiasi stato di visualizzazione di correzione riuscita precedente se il tentativo corrente è fallito
    reset_correction_display_states() # Assicura che la UI sia pulita

elif json_originale_llm: # Se c'è un JSON dall'LLM da processare
    st.divider()
    st.header("Correction Results")
    codice_studente_per_evidenziazione = st.session_state.get("codice_studente_modificato", "") 

    # Questa parte viene eseguita solo una volta dopo una nuova chiamata LLM, 
    # o se il JSON originale dell'LLM cambia.
    if "lista_oggetti_errore_iniziali" not in st.session_state or \
       st.session_state.get("last_processed_llm_json") != json_originale_llm:
        
        st.session_state["last_processed_llm_json"] = json_originale_llm

        codice_evidenziato_da_json, totale_deduzioni_iniziale, parsing_error, lista_errori_parsata_da_llm = evidenzia_errori_json(
            codice_studente_per_evidenziazione, 
            json_originale_llm
        )


        if parsing_error:
            st.error(f"Could not process LLM response: JSON Parsing Error: {parsing_error}")
            st.write("The student's code below includes a comment indicating the raw response that caused the parsing failure:")
            st.code(codice_evidenziato_da_json, language="c")
            # Pulisci stati che dipendono da un parsing corretto
            if "lista_oggetti_errore_iniziali" in st.session_state: del st.session_state["lista_oggetti_errore_iniziali"]
            if "codice_corretto_editabile" in st.session_state: del st.session_state["codice_corretto_editabile"]
            st.session_state["punteggio_attuale"] = 0
            st.session_state["json_attuale_da_visualizzare"] = "[]"
            # Non procedere oltre se c'è un errore di parsing
            st.stop() 
        else:
            # Parsing riuscito, inizializza gli stati per la modifica dinamica
            # lista_errori_parsata_da_llm è la lista di dizionari direttamente da evidenzia_errori_json
            if lista_errori_parsata_da_llm is not None:
                st.session_state["lista_oggetti_errore_iniziali"] = lista_errori_parsata_da_llm
            else: # Non dovrebbe succedere se parsing_error è None, ma per sicurezza
                st.error("Internal error: Parsed error list from LLM is unexpectedly None.")
                st.stop() # o gestisci in modo appropriato
            st.session_state["codice_corretto_editabile"] = codice_evidenziato_da_json
            # IMPORTANTE: Sincronizza anche lo stato della text_area con il nuovo contenuto dall'LLM
            st.session_state["text_area_corrected_code_llm"] = codice_evidenziato_da_json
            st.session_state["punteggio_attuale"] = totale_deduzioni_iniziale
            st.session_state["json_attuale_da_visualizzare"] = json_originale_llm

    # --- Interazione dell'utente con l'area di testo ---
    # Questa parte viene eseguita ad ogni rerun se l'area di testo è visibile e inizializzata

    # Non fornire 'value' qui; la 'key' gestirà lo stato della textarea.
    # Il suo valore sarà accessibile tramite st.session_state.text_area_corrected_code_llm.
    # Se st.session_state.text_area_corrected_code_llm non esiste, verrà inizializzata (a stringa vuota di default,
    # ma il blocco sopra la inizializza con il codice LLM quando arriva).
    st.text_area(
        "Corrected Code (Editable):",
        height=400,
        key="text_area_corrected_code_llm"
    )

    # Il testo corrente modificato dall'utente è in st.session_state.text_area_corrected_code_llm
    testo_corrente_nella_textarea = st.session_state.get("text_area_corrected_code_llm", "")

    # Sincronizza codice_corretto_editabile (usato per il download e come "master" prima dell'edit)
    # con il contenuto attuale della textarea, se sono diversi.
    if st.session_state.get("codice_corretto_editabile") != testo_corrente_nella_textarea:
        st.session_state["codice_corretto_editabile"] = testo_corrente_nella_textarea

    # Ricalcola sempre punteggio e JSON basati sul contenuto corrente della textarea
    punteggio_dinamico, errori_ricostruiti_dal_testo = ricostruisci_errori_da_testo_commentato(
        testo_corrente_nella_textarea
    )
    st.session_state["punteggio_attuale"] = punteggio_dinamico
    st.session_state["json_attuale_da_visualizzare"] = json.dumps(errori_ricostruiti_dal_testo, indent=2)

    # Visualizzazione del punteggio e del JSON (dinamicamente aggiornati)
    st.write(f"### ✏️ Total Point Deduction (dynamically updated): `{st.session_state.get('punteggio_attuale', 0)}`")

    # --- INIZIO NUOVA SEZIONE PER PUNTEGGI DETTAGLIATI PER FUNZIONE ---
    if st.session_state.get("codice_corretto_editabile") and \
       st.session_state.get("criteri_modificati") and \
       st.session_state.get("json_attuale_da_visualizzare"):
        
        codice_per_analisi = st.session_state.get("codice_corretto_editabile", "")
        testo_criteri = st.session_state.get("criteri_modificati", "")
        
        try:
            lista_errori_attuali_per_dettaglio = json.loads(st.session_state.get("json_attuale_da_visualizzare", "[]"))
        except json.JSONDecodeError:
            lista_errori_attuali_per_dettaglio = []
            st.warning("Could not parse current error list for detailed score breakdown per function.")

        if codice_per_analisi and testo_criteri: # Procedi solo se abbiamo il codice e i criteri
            
            defined_functions = find_c_function_definitions(codice_per_analisi)
            criteria_func_scores = parse_criteria_function_scores(testo_criteri)

            if not defined_functions:
                st.info("No function definitions found in the code to analyze for detailed scores.")
            else:
                st.markdown("---")
                st.subheader("Function Score Breakdown:")
                for func in defined_functions:
                    func_name = func["name"]
                    base_score = criteria_func_scores.get(func_name, 0.0)
                    
                    deductions_for_func_val = 0
                    deduction_strings = []
                    for error_item in lista_errori_attuali_per_dettaglio:
                        error_line = int(error_item.get("line", 0))
                        if func["start_line"] <= error_line <= func["end_line"]:
                            penalty = float(error_item.get("point_deduction", 0))
                            deductions_for_func_val += penalty # penalty è già negativa
                            deduction_strings.append(f" - {abs(penalty):.1f}")
                    
                    final_score = base_score + deductions_for_func_val
                    calc_details = "".join(deduction_strings)

                    col_func_name, col_func_calc = st.columns([2,3])
                    with col_func_name:
                        st.markdown(f"`{func_name}({base_score:.1f})`:")
                    with col_func_calc:
                        st.markdown(f"`{final_score:.1f} = {base_score:.1f}{calc_details}`")
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;Punteggio finale `{func_name}` = **{final_score:.1f}**")
                    st.markdown("---") # Separatore per la prossima funzione
    # --- FINE NUOVA SEZIONE ---

    # Pulsante di download per il codice corretto editabile
    student_id_part = "unknown_student"
    task_name_part = "unknown_task"

    if "selected_student_name" in st.session_state and \
       st.session_state["selected_student_name"] and \
       "cartella_codici" in st.session_state and \
       isinstance(st.session_state["cartella_codici"], dict) and \
       st.session_state["selected_student_name"] in st.session_state["cartella_codici"]:
        student_id_part = st.session_state["selected_student_name"]
        selected_file_obj = st.session_state["cartella_codici"][student_id_part]
        original_file_base = os.path.splitext(selected_file_obj.name)[0]
        prefix_to_check = student_id_part + "_"
        if original_file_base.startswith(prefix_to_check):
            task_name_part = original_file_base[len(prefix_to_check):]
        else:
            task_name_part = original_file_base
    elif "selected_student_folder" in st.session_state and \
         st.session_state["selected_student_folder"] and \
         "selected_c_file_path" in st.session_state and \
         st.session_state["selected_c_file_path"]:
        student_folder_name = os.path.basename(st.session_state["selected_student_folder"])
        student_id_part = student_folder_name.replace(" ", "_") 
        original_c_file_name = os.path.basename(st.session_state["selected_c_file_path"])
        task_name_part = os.path.splitext(original_c_file_name)[0] 

    if not student_id_part or student_id_part == "unknown_student": student_id_part = "student"
    else: student_id_part = student_id_part.replace(' ', '_')
    if not task_name_part or task_name_part == "unknown_task": task_name_part = "task"
    
    nome_file_corretto_con_commenti = f"{student_id_part}_corrected_{task_name_part}.c"

    st.download_button(
        label="💾 Save Corrected Code with LLM Comments",
        data=st.session_state.get("codice_corretto_editabile", ""), # Usa il valore dallo stato
        file_name=nome_file_corretto_con_commenti,
        mime="text/x-c"
    )

    st.write("### Current Error List (JSON - dynamically updated):")
    try:
        json_to_display = st.session_state.get("json_attuale_da_visualizzare", "[]")
        # Non serve json.loads() qui perché st.json può gestire direttamente una stringa JSON formattata.
        st.json(json_to_display)
    except json.JSONDecodeError:
        st.warning("Could not display current error list as JSON.")
        st.code(st.session_state.get("json_attuale_da_visualizzare", ""))

    
# Aggiunge più spazio vuoto per spingere il bottone verso il basso
for _ in range(10):
    st.write("")

center_col_btn1, center_col_btn2, center_col_btn3 = st.columns([1, 1, 1]) # Rinominate per evitare sovrascrittura

with center_col_btn2: # Usa la colonna centrale per il bottone
    if st.button("Return to the material upload page", use_container_width=True):
        st.switch_page("loading.py")
for _ in range(5):
    st.write("")
