import streamlit as st
import ezdxf
import json
import numpy as np
from groq import Groq

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="TavolaPronta AI Pro", layout="centered", page_icon="📐")

# --- COSTANTI (INCOLLA QUI I TUOI LINK STRIPE REALI) ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TAVOLA2026"

# --- MOTORE GEOMETRICO ---
def genera_tavola_perfetta(dati_json, premium=False):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Layer standard tecnici
    doc.layers.new(name='PROIEZIONI', dxfattribs={'color': 7, 'lineweight': 35})
    doc.layers.new(name='COSTRUZIONE', dxfattribs={'color': 8, 'lineweight': 15})
    doc.layers.new(name='ASSI', dxfattribs={'color': 1})
    
    # Disegno Assi Principali (Linea di Terra e Verticale)
    msp.add_line((-50, 0), (50, 0), dxfattribs={'layer': 'ASSI'})
    msp.add_line((0, -50), (0, 50), dxfattribs={'layer': 'ASSI'})

    for fig in dati_json.get('figure', []):
        x_base = fig.get('x', 10)
        y_base = fig.get('y', -10) 
        r = fig.get('raggio', 5)
        h = fig.get('altezza', 12)
        lati = fig.get('lati', 0)

        # 1. PIANO ORIZZONTALE (P.O.)
        if lati >= 3:
            punti_po = []
            for i in range(lati):
                angle = 2 * np.pi * i / lati
                p_x, p_y = x_base + r * np.cos(angle), y_base + r * np.sin(angle)
                punti_po.append((p_x, p_y))
            punti_po.append(punti_po[0])
            msp.add_lwpolyline(punti_po, dxfattribs={'layer': 'PROIEZIONI'})
        else:
            msp.add_circle((x_base, y_base), radius=r, dxfattribs={'layer': 'PROIEZIONI'})

        # 2. PROIEZIONI VERTICALI E RIBALTAMENTI (SOLO PREMIUM)
        if premium:
            # Vista Frontale (P.V.)
            msp.add_lwpolyline([(x_base-r, 0), (x_base+r, 0), (x_base, h), (x_base-r, 0)], dxfattribs={'layer': 'PROIEZIONI'})
            
            # Linee di richiamo verticali P.O. -> P.V.
            msp.add_line((x_base-r, y_base), (x_base-r, h), dxfattribs={'layer': 'COSTRUZIONE'})
            msp.add_line((x_base+r, y_base), (x_base+r, h), dxfattribs={'layer': 'COSTRUZIONE'})

            # Archi di ribaltamento per P.L. (Il tocco del professore)
            center = (0, 0)
            msp.add_arc(center, radius=abs(y_base-r), start_angle=270, end_angle=360, dxfattribs={'layer': 'COSTRUZIONE'})
            msp.add_arc(center, radius=abs(y_base+r), start_angle=270, end_angle=360, dxfattribs={'layer': 'COSTRUZIONE'})
            
            # Vista Laterale (P.L.)
            x_pl = abs(y_base)
            msp.add_lwpolyline([(x_pl-r, 0), (x_pl+r, 0), (x_pl, h), (x_pl-r, 0)], dxfattribs={'layer': 'PROIEZIONI'})

    nome = "tavola_pro.dxf"
    doc.saveas(nome)
    return nome

# --- INTERFACCIA UTENTE ---
st.title("📐 TavolaPronta AI Pro")
st.write("Genera proiezioni ortogonali complete partendo dalla traccia del libro")

if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.header("💎 Versione Premium")
    if not st.session_state.premium:
        st.write("Sblocca le proiezioni complete P.V. e P.L.")
        st.link_button("Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Lifetime (19,99€)", LINK_LIFETIME)
        st.divider()
        code = st.text_input("Codice ricevuto via mail:")
        if st.button("Attiva Premium"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else:
                st.error("Codice errato")
    else:
        st.success("🌟 Modalità Professionista Attiva")

traccia = st.text_area("Cosa devi disegnare? (Es: Piramide esagonale raggio 5 altezza 12)")

if st.button("🚀 GENERA DISEGNO"):
    if not traccia:
        st.warning("Inserisci il testo dell'esercizio")
    else:
        try:
            with st.spinner("L'intelligenza artificiale sta calcolando le proiezioni..."):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Sei un docente di disegno tecnico. Estrai dati geometrici in JSON: lista 'figure' con tipo, x, y, raggio, altezza, lati (6 per esagono, 3 per triangolo, 0 per cerchio)."},
                        {"role": "user", "content": traccia}
                    ],
                    response_format={"type": "json_object"}
                )
                
                dati = json.loads(res.choices[0].message.content)
                file_path = genera_tavola_perfetta(dati, premium=st.session_state.premium)
                
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="💾 Scarica file .DXF",
                        data=f,
                        file_name="tavola_pronta.dxf",
                        mime="application/dxf"
                    )
                
                if not st.session_state.premium:
                    st.info("💡 Stai scaricando solo il P.O. Passa a Premium per avere anche P.V. e P.L. con gli archi di ribaltamento")
        except Exception as e:
            st.error("Errore: controlla di aver inserito GROQ_API_KEY nei Secrets di Streamlit")

st.divider()
st.caption("TavolaPronta AI - Disegno Tecnico Automatizzato")
