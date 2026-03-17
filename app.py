import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LINK ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO MULTI-SOLIDO ---
def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12), facecolor='#f8f9fa')
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 60
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) 
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) 
    
    ax.text(-limit+2, 2, "P.V.", fontsize=14, fontweight='bold', color='#34495e')
    ax.text(-limit+2, -5, "P.O.", fontsize=14, fontweight='bold', color='#34495e')
    ax.text(2, limit-5, "P.L.", fontsize=14, fontweight='bold', color='#34495e')

    # Colori diversi per distinguere i solidi se multipli
    colori = ['black', '#2980b9', '#c0392b']
    
    for i, dati in enumerate(lista_solidi[:3]): # Limite massimo 3 solidi
        colore = colori[i]
        tipo = str(dati.get('tipo', 'solido')).lower()
        L = float(dati.get('lunghezza') or 6)
        P = float(dati.get('profondita') or 5)
        H = float(dati.get('altezza') or 10)
        # Offset automatico per non sovrapporre i solidi (distanza progressiva dal centro)
        dPV = float(dati.get('dist_pv') or 2) + (i * 2) 
        dPL = float(dati.get('dist_pl') or 3) + (i * 12)
        rot = float(dati.get('rotazione') or 0)
        lati = int(dati.get('lati') or 4)

        # 1. PIANO ORIZZONTALE (P.O.)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        offset_poly = np.pi/4 if lati == 4 and rot == 0 else 0
        t = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset_poly
        vx = x_c + (L/2) * np.cos(t)
        vy = y_c + (P/2) * np.sin(t)
        
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colore, linewidth=2.5)
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color=colore, linewidth=1, alpha=0.6)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)

            # 2. PIANO VERTICALE (P.V.)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            
            # 3. PIANO LATERALE (P.L.)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max, y_c if 'pir' in tipo else y_min]:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#e67e22', linestyle='--', linewidth=1, alpha=0.5)
            
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else:
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)

    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile", LINK_MENSILE)
        st.link_button("Accesso Illimitato", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")
        st.warning("🚧 SVILUPPO IN CORSO: La funzione 'Piano Ausiliario' è attualmente in fase di test tecnico.")
        if st.button("Logout"):
            st.session_state.premium = False
            st.rerun()

st.title("📐 TavolaPronta AI Master")
st.markdown("### Generatore di Proiezioni Ortogonali Multi-Solido")
traccia = st.text_area("Descrivi fino a 3 solidi (es: 'Un cubo lato 6 e una piramide base quadrata lato 4'):")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """Rispondi SOLO con un array JSON chiamato 'solidi'. Ogni elemento deve avere i parametri tecnici. Massimo 3 solidi.
            Esempio: {"solidi": [{"tipo": "cubo", "lunghezza": 6, ...}, {"tipo": "piramide", "lunghezza": 4, ...}]}"""
            
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati_json = json.loads(res.choices[0].message.content)
            lista = dati_json.get('solidi', [])
            
            if lista:
                st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
            else:
                st.error("Non ho trovato solidi nella traccia.")
        except Exception as e:
            st.error("Errore nell'analisi della traccia multi-solido.")
