if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            
            # Prompt rinforzato per evitare valori nulli
            prompt_sistema = """
            Sei un ingegnere. Estrai i dati e rispondi SOLO in JSON. 
            IMPORTANTE: Tutti i valori devono essere NUMERI, mai null.
            Se manca un dato usa questi default: lunghezza:6, profondita:4, altezza:10, dist_pv:5, dist_pl:7, rotazione:0, lati:4.
            Se la traccia chiede 'piano ausiliario' o 'vera forma', piano_ausiliario: true.
            JSON: {"tipo": "string", "lunghezza": 6, "profondita": 4, "altezza": 10, "dist_pv": 5, "dist_pl": 7, "rotazione": 0, "lati": 4, "piano_ausiliario": false}
            """
            
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            
            # Caricamento e validazione istantanea
            dati_raw = json.loads(res.choices[0].message.content)
            
            # Sanificazione manuale post-IA
            dati_puliti = {
                'tipo': str(dati_raw.get('tipo', 'solido')),
                'lunghezza': float(dati_raw.get('lunghezza') or 6),
                'profondita': float(dati_raw.get('profondita') or 4),
                'altezza': float(dati_raw.get('altezza') or 10),
                'dist_pv': float(dati_raw.get('dist_pv') or 5),
                'dist_pl': float(dati_raw.get('dist_pl') or 7),
                'rotazione': float(dati_raw.get('rotazione') or 0),
                'lati': int(dati_raw.get('lati') or 4),
                'piano_ausiliario': bool(dati_raw.get('piano_ausiliario', False))
            }
            
            st.pyplot(genera_proiezione_ortogonale(dati_puliti, premium=st.session_state.premium))
            
        except Exception as e:
            st.error(f"Errore tecnico: {e}. Prova a ricaricare la pagina o a scrivere la traccia in modo più semplice.")
