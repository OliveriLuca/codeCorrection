import streamlit as st
import os
import base64
import openai
import anthropic
import textwrap

# Configurazione della chiave API di OpenAI e di Anthropic
# Le chiavi vengono lette dalle variabili d'ambiente per motivi di sicurezza
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Inizializzazione del client OpenAI con la chiave API fornita
client = openai.OpenAI(api_key=openai_api_key)
# Inizializzazione del client Anthropic con la chiave API fornita
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

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

# Funzione per correzione automatica del codice C di uno studente tramite modelli LLM.
def correggi_codice(codice_studente, criteri, testo_esame, modello_scelto):
    # Crea il prompt da inviare al modello, includendo il testo dell'esame, i criteri di correzione e il codice dello studente.
    # Il modello deve rispondere solo con errori o correzioni, senza commenti extra.
    prompt = f"""
    Testo dell'esercizio (se presente):
    {textwrap.dedent(testo_esame) if testo_esame else "N/D"}

    Criteri di correzione:
    {textwrap.dedent(criteri)}

    Codice dello studente:
    ```c
    {codice_studente}
    ```
    Restituisci solo gli errori o le correzioni senza ulteriori commenti o spiegazioni, indicando le righe errate.
    """

    try:
        # Caso: utilizzo del modello GPT-4o di OpenAI
        if modello_scelto == "gpt-4o":
            risposta = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sei un esperto di programmazione in C."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Estrae e restituisce il contenuto della risposta generata dal modello
            return risposta.choices[0].message.content

        # Caso: utilizzo del modello Claude 3.5 Sonnet di Anthropic
        elif modello_scelto == "claude-3.5-sonnet":
            risposta = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                temperature=0.2,
                system="Sei un esperto di programmazione in C.",
                messages=[{"role": "user", "content": prompt}]
            )
            # Estrae e restituisce il testo della risposta
            return risposta.content[0].text

        # Caso: modello non supportato
        else:
            return "Modello non supportato."

    # Gestione errori API OpenAI (es. fine quota)
    except openai.APIError as e:
        if "insufficient_quota" in str(e).lower():
            return "Errore: hai esaurito la quota disponibile per OpenAI. Controlla il tuo piano o aspetta il rinnovo mensile."
        return f"Errore API OpenAI: {e}"

    # Gestione errori API Anthropic (es. fine quota)
    except anthropic.APIStatusError as e:
        if "insufficient_quota" in str(e).lower():
            return "Errore: hai esaurito la quota disponibile per Anthropic. Controlla il tuo piano o aspetta il rinnovo mensile."
        return f"Errore API Claude: {e}"

    # Gestione di altri errori imprevisti
    except Exception as e:
        return f"Errore imprevisto: {e}"

# Genera codice HTML evidenziando le righe del codice studente che contengono errori segnalati nelle correzioni.
def evidenzia_errori(codice_studente, correzioni):
    # Divide il codice dello studente e le correzioni in liste di righe
    righe_codice = codice_studente.split("\n")
    righe_correzioni = correzioni.split("\n")

    codice_modificato = ""  # Stringa per il codice con errori evidenziati

    for i, riga in enumerate(righe_codice):
        errore_corrente = ""

        # Cerca una correzione per la riga corrente
        for cor in righe_correzioni:
            if f"riga {i+1}" in cor.lower() or f"line {i+1}" in cor.lower():
                errore_corrente = cor.strip()
                break  # Usa solo la prima correzione trovata per quella riga

        # Aggiungi la correzione alla riga, se presente
        if errore_corrente:
            codice_modificato += f"{riga}    ← {errore_corrente}\n"
        else:
            codice_modificato += f"{riga}\n"

    return codice_modificato

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    st.header("Codici Studenti")
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        cartella = st.session_state["cartella_codici"]
        st.write(f"\U0001F4C1 **Cartella caricata:** {cartella}")

        if not os.path.exists(cartella) or not os.listdir(cartella):
            st.warning("La cartella caricata non contiene file validi.")
        else:
            sottocartelle = [d for d in os.listdir(cartella) if os.path.isdir(os.path.join(cartella, d))]

            if sottocartelle:
                sottocartella_scelta = st.selectbox("Seleziona uno studente:", sottocartelle)
                percorso_cartella_scelta = os.path.join(cartella, sottocartella_scelta)

                file_c = None
                for file in os.listdir(percorso_cartella_scelta):
                    if file.endswith(".c"):
                        file_c = file
                        break

                if file_c:
                    percorso_file = os.path.join(percorso_cartella_scelta, file_c)
                    with open(percorso_file, "r") as codice_file:
                        codice = codice_file.read()

                    # Salva il codice nello stato della sessione
                    st.session_state["codice_studente"] = codice

                    # Riquadro editabile
                    codice_modificato = st.text_area(
                        f"Contenuto di {file_c}",
                        st.session_state["codice_studente"],
                        height=200
                    )

                    # Aggiorna il codice se modificato
                    if codice_modificato != st.session_state["codice_studente"]:
                        st.session_state["codice_studente"] = codice_modificato

                    cognome_nome = sottocartella_scelta.replace(" ", "_")
                    nome_file_salvato = f"{cognome_nome}_{os.path.basename(cartella)}.c"
                    st.download_button("💾 Salva codice", codice_modificato, file_name=nome_file_salvato, mime="text/plain")
                else:
                    st.warning("Nessun file .c trovato nella cartella selezionata.")
            else:
                st.warning("Nessuna sottocartella trovata nella cartella principale.")
    else:
        st.warning("Nessuna cartella caricata per i codici studenti.")

    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        if st.button("🗑️ Elimina Cartella Codici Studenti"):
            elimina_cartella()

    # Sezione per la correzione con LLM
    # Prepara una variabile di default per i criteri
    criteri = ""
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
     file = st.session_state["criteri_correzione"]
     criteri = file.getvalue().decode("utf-8")

    if "cartella_codici" in st.session_state and criteri:

        if 'sottocartella_scelta' in locals() and file_c:
            modello_scelto = st.radio("Seleziona il modello da usare per la correzione:", ["gpt-4o", "claude-3.5-sonnet"], horizontal=True)

            # Visualizzazione del codice e degli errori
            if st.button("🤖 Correggi"):
                criteri = st.session_state.get("criteri_modificati", "")
                testo_esame = st.session_state.get("testo_modificato", "")
                codice = st.session_state.get("codice_studente", "")
                correzioni = correggi_codice(codice, criteri, testo_esame, modello_scelto)

                if correzioni:
                    # Applica le correzioni direttamente al codice
                    codice_modificato_con_errori = evidenzia_errori(codice, correzioni)

                    # Aggiorna il codice nello stato della sessione
                    st.session_state["codice_studente"] = codice_modificato_con_errori

                    # Rerun per aggiornare il riquadro
                    st.rerun()

                    # Log per verificare il contenuto delle variabili
                    st.write("Codice corretto:", codice_modificato_con_errori)
                    st.write("Codice nello stato della sessione:", st.session_state["codice_studente"])

# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Criteri di Correzione")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        st.write(f" **File caricato:** {file.name}")

        # Visualizza il contenuto del file .txt
        testo = file.getvalue().decode("utf-8")
        if "criteri_modificati" not in st.session_state:
            st.session_state["criteri_modificati"] = testo

        criteri_editabili = st.text_area("Contenuto dei Criteri di Correzione", st.session_state["criteri_modificati"], height=300)

        # Aggiorna lo stato della sessione con il contenuto modificato
        st.session_state["criteri_modificati"] = criteri_editabili

        # Pulsanti per scaricare ed eliminare il file
        if st.download_button("💾Salva Criteri di Correzione", st.session_state["criteri_modificati"], file_name=file.name, mime="text/plain"):
            st.success("File scaricato con successo con le modifiche apportate!")

        if st.button("🗑️Elimina Criteri di Correzione"):
            elimina_file("criteri_correzione")
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Linea di separazione tra le sezioni
st.divider()

# Creazione di una colonna centrale per il Testo d'Esame
spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

#Sezione per visualizzazione testo d'esame
with col3:
    st.header("Testo d'Esame")
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        file = st.session_state["testo_esame"]
        st.write(f" **File caricato:** {file.name}")

        # Verifica se il file è un PDF
        if file.name.endswith(".pdf"):
            mostra_pdf(file)

            # Modifica il tipo MIME per i PDF
            if st.download_button("💾Salva Testo d'Esame", file.getvalue(), file_name=file.name, mime="application/pdf"):
                st.success("File PDF scaricato con successo con le modifiche apportate!")

        # Se il file è un file di testo (modificabile)
        elif file.name.endswith(".txt"):
            testo = file.getvalue().decode("utf-8")
            if "testo_modificato" not in st.session_state:
                st.session_state["testo_modificato"] = testo

            testo_modificato = st.text_area("Contenuto del Testo d'Esame", st.session_state["testo_modificato"], height=300)

            # Aggiorna lo stato della sessione con il contenuto modificato
            st.session_state["testo_modificato"] = testo_modificato

            # Pulsante per il download del testo
            if st.download_button("💾Salva Testo d'Esame ", testo_modificato, file_name=file.name, mime="text/plain"):
                st.success("File di testo scaricato con successo!")

        # Pulsante per eliminare il file
        if st.button("🗑️Elimina Testo d'Esame"):
            elimina_file("testo_esame")
            if "testo_modificato" in st.session_state:
                del st.session_state["testo_modificato"]
    else:
        st.warning("Nessun file caricato per il testo d'esame.")

# Aggiunge più spazio vuoto per spingere il bottone verso il basso
for _ in range(10):
    st.write("")

# Creazione di colonne per centrare il pulsante
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Torna alla pagina di caricamento materiali", use_container_width=True):
        st.switch_page("caricamento.py")

# Aggiunge ancora più spazio sotto il pulsante
for _ in range(5):
    st.write("")
