import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURAZIONE INTERFACCIA (IDENTICA A PRIMA) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- FUNZIONE VISTA 3D (SBLOCCATA COL PREMIUM) ---
def genera_vista_3d(lista_solidi):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    limit = 25
    # Disegno dei piani di riferimento (la "stanza")
    xx, yy = np.meshgrid(np.linspace(-limit, 0, 2), np.linspace(-limit, 0, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.1, color='gray') 
    ax.plot_surface(xx, np.zeros_like(xx), yy + limit, alpha=0.1, color='blue')
    ax.plot_surface(np.zeros_like(xx), xx, yy + limit, alpha=0.1, color='red')
    
    colori = ['#2c3e50', '#2980b9', '#e74c3c']
    for i, dati in enumerate(lista_solidi[:3]):
        L, P, H = float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 5), float(dati.get('dist_pl') or 5)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        # Rappresentazione schematica 3D
        z_base = np.zeros(5)
        z_top = np.full(5, H)
        xi = [x_c-L/2, x_c+L/2, x_c+L/2, x_c-L/2, x_c-L/2]
        yi = [y_c-P/2, y_c-P/2, y_c+P/2, y_c+P/2, y_c-P/2]
        ax.plot(xi, yi, 0, color=colori[i], linewidth=2)
        if 'pir' in dati.get('tipo', '').lower():
            for px, py in zip(xi[:4], yi[:4]): ax.plot([px, x_c], [py, y_c], [0, H], color=colori[i], linewidth=1)
        else:
            ax.plot(xi, yi, H, color=colori[i], linewidth=2)
            for px, py in zip(xi[:4], yi[:4]): ax.plot([px, px], [py, py], [0, H], color=colori[i], linestyle='--', alpha=0.5)
    
    ax.view_init(elev=20, azim=45)
    ax.set_axis_off()
    return fig

# --- MOTORE GRAFICO MULTI-SOLIDO (CON LINEE DI RIBALTAMENTO) ---
def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    limit = 80
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) 
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) 
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(2, limit-5, "P.L.", fontsize=12, fontweight='bold', color='#7f8c8d')
    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    for i, dati in enumerate(lista_solidi[:3]):
        colore = colori[i]
        tipo, L, P, H = str(dati.get('tipo', 'solido')).lower(), float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL, rot, lati = float(dati.get('dist_pv') or (10 + i*15)), float(dati.get('dist_pl') or (10 + i*25)), float(dati.get('rotazione') or 0), int(dati.get('lati') or 4)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        offset_poly = np.pi/4 if (lati == 4 and rot == 0) else 0
        t = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset_poly
        vx, vy = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colore, linewidth=2.5)
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color=colore, linewidth=0.8, alpha=0.5)
        if premium:
            x_min, x_max, y_min, y_max = np.min(vx), np.max(vx), np.min(vy), np.max(vy)
            for px in vx: ax.plot([px, px], [vy[np.where(vx==px)[0][0]], 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
                ax.plot([x_c, x_c], [y_c, 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            else: ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in vy:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=1)
                ax.plot([r, r], [0, H if 'pir' in tipo else 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo or 'con' in tipo: ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else: ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
    if not premium:
        ax.text(-limit/2, limit/2, "🔒 P.V. BLOCCATO\nAcquista la licenza per sbloccare", color='red', alpha=0.4, fontsize=15, ha='center', va='center', fontweight='bold')
        ax.text(limit/2, limit/2, "🔒 P.L. BLOCCATO\nAcquista la licenza per sbloccare", color='red', alpha=0.4, fontsize=15, ha='center', va='center', fontweight='bold')
    return fig

# --- UI BARRA LATERALE (IDENTICA A PRIMA) ---
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

# --- CORPO APP (IDENTICO A PRIMA) ---
st.title("📐 TavolaPronta AI Master")
st.write("Generazione tecnica multi-solido per professionisti e studenti.")
traccia = st.text_area("Cosa vuoi disegnare oggi? (Supporta fino a 3 solidi contemporaneamente):", height=120)
if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Rispondi SOLO JSON con lista 'solidi'. Parametri: tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati."}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            if dati: 
                st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
                if st.session_state.premium:
                    st.divider()
                    st.subheader("📦 Visualizzazione 3D in tempo reale")
                    st.pyplot(genera_vista_3d(dati))
            else: st.warning("Specifica meglio le misure dei solidi")
        except: st.error("Errore nell'elaborazione della traccia")
