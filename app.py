import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA (IDENTICA) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO MULTI-SOLIDO CON LINEE DI PROIEZIONE ---
def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 80
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) # Linea di Terra
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) # Asse Verticale
    
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(2, limit-5, "P.L.", fontsize=12, fontweight='bold', color='#7f8c8d')

    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    
    for i, dati in enumerate(lista_solidi[:3]):
        colore = colori[i]
        tipo = str(dati.get('tipo', 'solido')).lower()
        L = float(dati.get('lunghezza') or 6)
        P = float(dati.get('profondita') or 5)
        H = float(dati.get('altezza') or 10)
        dPV = float(dati.get('dist_pv') or (10 + i*15))
        dPL = float(dati.get('dist_pl') or (10 + i*25))
        rot = float(dati.get('rotazione') or 0)
        lati = int(dati.get('lati') or 4)

        # 1. PIANO ORIZZONTALE (P.O.)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        offset_poly = np.pi/4 if (lati == 4 and rot == 0) else 0
        t = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset_poly
        vx, vy = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
        
        # Disegno base P.O.
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colore, linewidth=2.5)
        
        # Spigoli piramide/cono in P.O.
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color=colore, linewidth=0.8, alpha=0.5)

        # 2. VISUALIZZAZIONE PREMIUM (P.V. e P.L. con Proiezioni)
        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            
            # --- LINEE DI PROIEZIONE P.O. -> P.V. (Verticali) ---
            # Proiettiamo i vertici della base e l'eventuale vertice (piramide/cono)
            for px in vx:
                ax.plot([px, px], [vy[np.where(vx==px)[0][0]], 0], color='#bdc3c7', linestyle='--', linewidth=0.8) # Sottili tratteggiate
            
            if 'pir' in tipo or 'con' in tipo:
                 ax.plot([x_c, x_c], [y_c, 0], color='#bdc3c7', linestyle='--', linewidth=0.8)


            # --- PIANO VERTICALE (P.V.) ---
            if 'pir' in tipo or 'con' in tipo:
                # Disegno piramide/cono in P.V.
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else:
                # Disegno prisma/parallelepipedo in P.V.
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            
            # --- LINEE DI PROIEZIONE P.V. -> P.L. (Orizzontali) ---
            # Proiettiamo l'altezza e la base
            ax.plot([x_max, 0], [0, 0], color='#bdc3c7', linestyle='--', linewidth=0.8) # Base
            ax.plot([x_max if 'pir' in tipo or 'con' in tipo else x_max, 0], [H, H], color='#bdc3c7', linestyle='--', linewidth=0.8) # Altezza
            
            # --- ARCHI DI RIBALTAMENTO P.O. -> P.L. ---
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            
            # Ribaltiamo la profondità dei vertici e dell'eventuale centro
            for ry in vy:
                 r = abs(ry)
                 ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=0.8)
                 
            if 'pir' in tipo or 'con' in tipo:
                 r_c = abs(y_c)
                 ax.plot(r_c*np.cos(t_arco), r_c*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=0.8)

            # --- LINEE DI PROIEZIONE VERTICALI IN P.L. ---
            # Dopo il ribaltamento, alziamo le linee tratteggiate in P.L.
            for ry in vy:
                 r = abs(ry)
                 ax.plot([r, r], [0, H if 'pir' in tipo or 'con' in tipo else 0], color='#bdc3c7', linestyle='--', linewidth=0.8)

            if 'pir' in tipo or 'con' in tipo:
                 r_c = abs(y_c)
                 ax.plot([r_c, r_c], [0, H], color='#bdc3c7', linestyle='--', linewidth=0.8)


            # --- PIANO LATERALE (P.L.) ---
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo or 'con' in tipo:
                # Disegno piramide/cono in P.L.
                ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else:
                # Disegno prisma/parallelepipedo in P.L.
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
    
    if not premium:
        # Messaggi di blocco sui piani PV e PL
        ax.text(-limit/2, limit/2, "🔒 P.V. BLOCCATO\nAcquista la licenza per sbloccare", color='red', alpha=0.4, fontsize=15, ha='center', va='center', fontweight='bold')
        ax.text(limit/2, limit/2, "🔒 P.L. BLOCCATO\nAcquista la licenza per sbloccare", color='red', alpha=0.4, fontsize=15, ha='center', va='center', fontweight='bold')

    return fig

# --- UI BARRA LATERALE (IDENTICA) ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Premium Master")
    
    if not st.session_state.premium:
        st.markdown("### 🎟️ Scegli il tuo piano")
        with st.container(border=True):
            st.write("**Master Mensile**")
            st.write("🎯 4,99€ / mese")
            st.link_button("Abbonati Ora", LINK_MENSILE, use_container_width=True)
        
        with st.container(border=True):
            st.write("**Master Lifetime**")
            st.write("🚀 19,99€ una tantum")
            st.link_button("Sblocca per Sempre", LINK_LIFETIME, use_container_width=True)
            
        st.divider()
        st.write("🔑 **Attivazione**")
        code = st.text_input("Inserisci il codice che ti è stato inviato a seguito dell’acquisto:", type="password", placeholder="Codice licenza...")
        if st.button("Attiva Licenza Master", use_container_width=True):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice non valido o scaduto")
    else:
        st.success("✅ ABBONAMENTO MASTER ATTIVO")
        st.info("🚧 **Work in Progress**: Stiamo ottimizzando la Tavola 6 e il Piano Ausiliario.")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- CORPO APP (IDENTICO) ---
st.title("📐 TavolaPronta AI Master")
st.write("Generazione tecnica multi-solido per professionisti e studenti.")

traccia = st.text_area("Cosa vuoi disegnare oggi? (Supporta fino a 3 solidi contemporaneamente):", height=120)

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """Analizza la traccia e restituisci un JSON con una lista 'solidi' (max 3). 
            Parametri: tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati.
            Se cilindro/cono: lati=100.
            Rispondi SOLO JSON."""
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            if dati: st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
            else: st.warning("Specifica meglio le misure dei solidi")
        except: st.error("Errore nell'elaborazione della traccia complessa")