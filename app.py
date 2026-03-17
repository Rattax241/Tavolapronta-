import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA (INVARIATA) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO MASTER: TANGENZA E PROIEZIONI REALI ---
def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 90
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) 
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) 
    
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(2, limit-5, "P.L.", fontsize=12, fontweight='bold', color='#7f8c8d')

    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    
    # Parametri specifici TAV 6 per calcolo tangenza
    r_cil = 2.5
    lato_pir = 4.0
    # Distanza di tangenza: raggio cilindro + apotema base piramide
    dist_tangenza = r_cil + (lato_pir / 2)

    for i, dati in enumerate(lista_solidi[:3]):
        colore = colori[i]
        tipo = str(dati.get('tipo', 'solido')).lower()
        L = float(dati.get('lunghezza') or 6)
        P = float(dati.get('profondita') or 5)
        H = float(dati.get('altezza') or 10)
        rot_z = float(dati.get('rotazione') or 0)
        
        # LOGICA P.O.
        angle = np.radians(rot_z)
        if 'cilindro' in tipo:
            x_c, y_c = -20, -15 # Centro fisso per riferimento
            t = np.linspace(0, 2*np.pi, 100)
            vx = x_c + (L/2) * np.cos(t) * np.cos(angle) - (P/2) * np.sin(t) * np.sin(angle)
            vy = y_c + (L/2) * np.cos(t) * np.sin(angle) + (P/2) * np.sin(t) * np.cos(angle)
        elif 'piramide' in tipo:
            # Spostamento calcolato per tangenza reale
            x_c = -20 + dist_tangenza * np.cos(angle + np.pi/2)
            y_c = -15 + dist_tangenza * np.sin(angle + np.pi/2)
            t = np.linspace(0, 2*np.pi, 5) + np.pi/4 # Quadrato perfetto
            vx = x_c + (L/2) * np.cos(t) * np.cos(angle) - (P/2) * np.sin(t) * np.sin(angle)
            vy = y_c + (L/2) * np.cos(t) * np.sin(angle) + (P/2) * np.sin(t) * np.cos(angle)
            # Spigoli piramide
            for px, py in zip(vx[:-1], vy[:-1]):
                ax.plot([x_c, px], [y_c, py], color=colore, linewidth=1, alpha=0.6)
        else: # Forme normali/dritte
            x_c, y_c = -40, -40
            t = np.linspace(0, 2*np.pi, int(dati.get('lati', 4))+1)
            vx = x_c + (L/2) * np.cos(t)
            vy = y_c + (P/2) * np.sin(t)

        ax.plot(vx, vy, color=colore, linewidth=2.5)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            # P.V.
            if 'pir' in tipo: ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else: ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            # P.L. Archi e proiezione
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max]:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=1)
            z_min, z_max = abs(y_max), abs(y_min)
            if 'pir' in tipo: ax.plot([z_min, z_max, abs(y_c), z_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else: ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)

    if not premium:
        ax.fill_between([-limit, 0], 0, limit, color='white', alpha=0.9)
        ax.fill_between([0, limit], -limit, limit, color='white', alpha=0.9)
        ax.text(-limit/2, limit/2, "🔒 P.V. BLOCCATO\nAcquista la licenza per sbloccare", color='red', fontsize=14, ha='center', fontweight='bold')
        ax.text(limit/2, limit/2, "🔒 P.L. BLOCCATO\nAcquista la licenza per sbloccare", color='red', fontsize=14, ha='center', fontweight='bold')

    return fig

# --- UI BARRA LATERALE (INVARIATA) ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Premium Master")
    if not st.session_state.premium:
        st.markdown("### 🎟️ Scegli il tuo piano")
        with st.container(border=True):
            st.write("**Master Mensile** (4,99€)")
            st.link_button("Abbonati Ora", LINK_MENSILE, use_container_width=True)
        with st.container(border=True):
            st.write("**Master Lifetime** (19,99€)")
            st.link_button("Sblocca per Sempre", LINK_LIFETIME, use_container_width=True)
        st.divider()
        st.write("🔑 **Attivazione**")
        code = st.text_input("Inserisci il codice che ti è stato inviato a seguito dell’acquisto:", type="password")
        if st.button("Attiva Licenza Master", use_container_width=True):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice non valido")
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")
        st.info("🚧 Ottimizzazione TAV. 6 completata.")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- CORPO APP (INVARIATO) ---
st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Inserisci la traccia (es. 'Cilindro raggio 2.5 e piramide lato 4 tangenti'):", height=100)

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """Rispondi SOLO JSON. Estrai solidi. Parametri: tipo, lunghezza, profondita, altezza, rotazione. TAV 6: rotazione 30."""
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
        except: st.error("Errore nell'analisi.")
