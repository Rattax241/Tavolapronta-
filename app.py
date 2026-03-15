import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 65
    # Assi principali
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    
    if not lista_dati: return fig

    for dati in lista_dati:
        # Recupero dati con "paracadute" per evitare errori NoneType
        tipo = str(dati.get('tipo', 'solido')).lower()
        L = float(dati.get('lunghezza', 6) or 6)
        P = float(dati.get('profondita', L) or L)
        H = float(dati.get('altezza', 10) or 10)
        dPV = float(dati.get('dist_pv', 5) or 5)
        dPL = float(dati.get('dist_pl', 5) or 5)
        lati = int(dati.get('lati', 4) or 4)
        rot = float(dati.get('rotazione', 0) or 0)
        aux = dati.get('piano_ausiliario', False)
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Raddrizzamento quadrati
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        
        # Calcolo vertici PO
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx = x_c + (L/2) * np.cos(theta)
        vy = y_c + (P/2) * np.sin(theta)
        
        # 1. DISEGNO P.O.
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2)
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color='black', linewidth=0.8)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)

            # 2. PIANO VERTICALE (P.V.)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)

            # 3. PIANO LATERALE (P.L. con Archi)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max, y_c]:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.6)
            
            # 4. PIANO AUSILIARIO (Solo se richiesto)
            if aux:
                ang_pa = np.radians(-30) # Inclinazione asse ausiliario
                # Linea di terra ausiliaria
                ax.plot([-limit, 0], [-20 + -limit*np.tan(ang_pa), -20], color='purple', linewidth=1.2, linestyle='-.')
                # Proiezioni perpendicolari (stile immagine postata)
                for i in range(len(vx)):
                    ax.plot([vx[i], vx[i]-15], [vy[i], vy[i]+25], color='purple', linestyle=':', linewidth=0.5, alpha=0.4)

    return fig

# --- INTERFACCIA ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else: st.success("✅ MODALITÀ MASTER ATTIVA")

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Scrivi la traccia qui:", placeholder="Esempio: Parallelepipedo 6x4x10 ruotato di 30 gradi con piano ausiliario...")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """Restituisci JSON lista 'solidi'. 
            Regole: Se menziona 'piano ausiliario' o 'vera forma', piano_ausiliario: true.
            Assicurati che 'lati', 'rotazione', 'lunghezza' siano numeri e mai null.
            JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati", "piano_ausiliario"}]}"""
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            lista = json.loads(res.choices[0].message.content).get("solidi", [])
            st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
        except Exception as e:
            st.error(f"L'IA ha avuto un piccolo intoppo tecnico. Riprova tra un istante.")

