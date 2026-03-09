import streamlit as st
import ezdxf
import json
# Nota: dovrai installare openai o google-generativeai
import openai 

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="TavolaPronta AI", layout="centered")

# --- SIMULAZIONE DATI UTENTE ---
if 'is_premium' not in st.session_state:
    st.session_state.is_premium = False

# --- FUNZIONE MOTORE GEOMETRICO (DXF) ---
def genera_dxf(dati_geometrici, completo=False):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Layer per distinguere le viste
    doc.layers.new(name='PO', dxfattribs={'color': 1}) # Rosso
    doc.layers.new(name='PV_PL', dxfattribs={'color': 7}) # Bianco/Nero
    
    # Logica semplificata di disegno basata sul JSON dell'IA
    for figura in dati_geometrici.get('figure', []):
        # Disegno su P.O. (Sempre disponibile)
        if figura['tipo'] == 'cilindro':
            msp.add_circle((figura['x'], figura['y']), radius=figura['raggio'], dxfattribs={'layer': 'PO'})
        elif figura['tipo'] == 'piramide':
            # Esempio cerchio circoscritto base esagonale
            msp.add_circle((figura['x'], figura['y']), radius=figura['base'], dxfattribs={'layer': 'PO'})
            
        # Viste PV e PL (Solo se Premium)
        if completo:
            # Qui il codice calcola le proiezioni verticali
            msp.add_line((figura['x'], 0), (figura['x'], figura['altezza']), dxfattribs={'layer': 'PV_PL'})
            st.success("Viste P.V. e P.L. generate con successo!")
            
    doc.saveas("tavola_generata.dxf")
    return "tavola_generata.dxf"

# --- INTERFACCIA UTENTE ---
st.title("📐 TavolaPronta AI")
st.write("Trasforma la traccia del prof in una tavola tecnica perfetta.")

# Area di testo per la traccia
testo_traccia = st.text_area("Incolla qui il testo della Tavola (es. Tav. 11):", height=150)

# Selezione Piano
if not st.session_state.is_premium:
    st.warning("🔓 Piano GRATUITO: Verrà generato solo il Piano Orizzontale (P.O.)")
    if st.button("Passa a Premium (4,99€)"):
        st.session_state.is_premium = True
        st.rerun()
else:
    st.star("🌟 Piano PREMIUM Attivo: Tavola Completa (P.O, P.V, P.L.)")

# Bottone Genera
if st.button("Genera Tavola Pronta"):
    if testo_traccia:
        with st.spinner("L'IA sta risolvendo la geometria..."):
            # Qui simuliamo l'output JSON che l'IA estrarrebbe dal testo
            # In produzione useresti: dati = chiamata_ai(testo_traccia)
            dati_fittizi = {
                "figure": [{"tipo": "cilindro", "x": 5, "y": -5, "raggio": 2, "altezza": 8}]
            }
            
            file_path = genera_dxf(dati_fittizi, completo=st.session_state.is_premium)
            
            with open(file_path, "rb") as file:
                st.download_button(
                    label="⬇️ Scarica file DXF (AutoCAD)",
                    data=file,
                    file_name="TavolaPronta.dxf",
                    mime="application/dxf"
                )
    else:
        st.error("Inserisci il testo della traccia!")

# --- FOOTER ---
st.divider()
st.caption("Creato per studenti disperati. Usare con responsabilità.")
