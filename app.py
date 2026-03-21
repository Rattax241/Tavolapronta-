import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURAZIONE INTERFACCIA (IDENTICA) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- NUOVA FUNZIONE: VISTA ASSONOMETRICA 3D ---
def genera_vista_3d_assonometrica(lista_solidi):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    limit = 40
    ax.set_axis_off()
    
    # Rappresentazione dei piani (PO, PV, PL) come griglie trasparenti
    xx, yy = np.meshgrid(np.linspace(-limit, 0, 2), np.linspace(-limit, 0, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.05, color='gray') # PO
    ax.plot_surface(xx, np.zeros_like(xx), yy + limit, alpha=0.05, color='blue') # PV
    ax.plot_surface(np.zeros_like(xx), xx, yy + limit, alpha=0.05, color='red') # PL

    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    
    for i, dati in enumerate(lista_solidi[:3]):
        tipo = str(dati.get('tipo', 'solido')).lower()
        L, P, H = float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 15), float(dati.get('dist_pl') or 15)
        rot, lati = float(dati.get('rotazione') or 0), int(dati.get('lati') or 4)
        
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        offset_poly = np.pi/4 if (lati == 4 and rot == 0) else 0
        t = np.linspace(0, 2*np.pi, lati+1) + angle + offset_poly
        
        # Geometria 3D
        if 'pir' in tipo or 'con' in tipo:
            # Base e Vertice
            bx, by = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
            for x_b, y_b in zip(bx, by):
                ax.plot([x_b, x_c], [y_b, y_c], [0, H], color=colori[i], linewidth=1.5)
            ax.plot(bx, by, 0, color=colori[i], linewidth=2)
        else:
            # Basi inferiore e superiore per Prismi/Cilindri
            bx, by = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
            ax.plot(bx, by, 0, color=colori[i], linewidth=2)
            ax.plot(bx, by, H, color=colori[i], linewidth=2)
            # Spigoli verticali
            step = 1 if lati > 20 else 1
            for x_b, y_b in zip(bx[::step], by[::step]):
                ax.plot([x_b, x_b], [y_b, y_b], [0, H], color=colori[i], linewidth=1, alpha=0.6)

    ax.view_init(elev=20, azim=45)
    return fig

# --- MOTORE GRAFICO PROIEZIONI (IDENTICO) ---
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
        dPV, dPL, rot, lati = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10), float(dati.get('rotazione') or 0), int(dati.get('lati') or 4)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        offset_poly = np.pi/4 if (lati == 4 and rot == 0) else 0
        t = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset_poly
        vx, vy = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colore, linewidth=2.5)
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color=colore, linewidth=0.8, alpha=0.5)
        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            for px in vx: ax.plot([px, px], [vy[np.where(vx==px)[0][0]], 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            if 'pir' in tipo or 'con' in tipo: ax.plot([x_c, x_c], [y_c, 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            if 'pir' in tipo or 'con' in tipo: ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else: ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            ax.plot([x_max, 0], [0, 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            ax.plot([x_max, 0], [H, H], color='#bdc3c7', linestyle='--', linewidth=0.8)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in vy:
                 r = abs(ry)
                 ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=0.8)
            if 'pir' in tipo or 'con' in tipo:
                 r_c = abs(y_c)
                 ax.plot(r_c*np.cos(t_arco), r_c*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=0.8)
            for ry in vy:
                 r = abs(ry)
                 ax.plot([r, r], [0, H if 'pir' in tipo or 'con' in tipo else 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            if 'pir' in tipo or 'con' in tipo:
                 r_c = abs(y_c)
                 ax.plot([r_c, r_c], [0, H], color='#bdc3c7', linestyle='--', linewidth=0.8)
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo or 'con' in tipo: ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else: ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
    if not premium:
        ax.text(-40, 40, "🔒 P.V. BLOCCATO", color='red', alpha=0.4, fontsize=15, ha='center', fontweight='bold')
        ax.text(40, 40, "🔒 P.L. BLOCCATO", color='red', alpha=0.4, fontsize=15, ha='center', fontweight='bold')
    return fig

# --- UI BARRA LATERALE (IDENTICA) ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Premium Master")
    if not st.session_state.premium:
        st.markdown("### 🎟️ Scegli il tuo piano")
        with st.container(border=True):
            st.write("**Master Mensile**"); st.write("🎯 4,99€ / mese")
            st.link_button("Abbonati Ora", LINK_MENSILE, use_container_width=True)
        with st.container(border=True):
            st.write("**Master Lifetime**"); st.write("🚀 19,99€ una tantum")
            st.link_button("Sblocca per Sempre", LINK_LIFETIME, use_container_width=True)
        st.divider()
        code = st.text_input("Inserisci il codice licenza:", type="password")
        if st.button("Attiva Licenza Master", use_container_width=True):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ ABBONAMENTO MASTER ATTIVO")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- CORPO APP ---
st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa vuoi disegnare oggi?", height=120)

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Restituisci JSON
