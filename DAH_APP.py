import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Dashboard Bounkani", layout="wide")

# --- PARAMÈTRES KOBO (À remplir) ---
KOBO_TOKEN = "7f409a0bdd3da09fe59e8ae57e5c099f011d2405" # Exemple: "a1b2c3d4e5f6..."
FORM_ID = "abrJjNyA6FX9LLzg6CUW7f" # Exemple: "aN7Hpxyz..."
KOBO_URL = f"https://kobo.humanitarianresponse.info/api/v2/assets/{FORM_ID}/data/?format=json"

st.title("📊 Rapport de Vulnérabilité : Région du Bounkani")
st.markdown("---")

@st.cache_data(ttl=600) # Rafraîchit les données toutes les 10 minutes
def load_kobo_data():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    # On teste l'URL directe sans le /data/ à la fin pour voir si le formulaire est reconnu
    test_url = f"https://kf.kobotoolbox.org/api/v2/assets/{FORM_ID}/?format=json"
    
    response = requests.get(test_url, headers=headers)
    
    if response.status_code == 200:
        # Si on arrive ici, l'ID est BON. On tente alors de récupérer les données.
        data_url = f"https://kf.kobotoolbox.org/api/v2/assets/{FORM_ID}/data/?format=json"
        data_response = requests.get(data_url, headers=headers)
        if data_response.status_code == 200:
            return pd.DataFrame(data_response.json()['results'])
        else:
            st.error(f"Formulaire trouvé, mais erreur d'accès aux données : {data_response.status_code}")
    elif response.status_code == 404:
        st.error(f"L'ID du formulaire '{FORM_ID}' est introuvable sur kf.kobotoolbox.org. Vérifiez l'ID dans l'URL de votre navigateur.")
    elif response.status_code == 401:
        st.error("Le Token est incorrect ou vous n'avez pas les permissions.")
    else:
        st.error(f"Erreur inconnue : {response.status_code}")
    return None

# Chargement des données
df = load_kobo_data()

if df is not None:
    # --- NETTOYAGE DES DONNÉES (Adapter selon vos noms de colonnes Kobo) ---
    # Souvent Kobo ajoute des préfixes, on les simplifie ici si nécessaire
    
    # 1. INDICATEURS CLÉS (KPI)
    total_menages = len(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Ménages Évalués", total_menages)
    
    # Calculer un exemple : % de besoin WASH (si vous avez une colonne wash_traitement)
    if 'WASH_Traitement' in df.columns:
        besoin_wash = (df['WASH_Traitement'] == 'Rien').sum()
        col2.metric("Urgence WASH", f"{besoin_wash} ménages", delta="Besoin d'aide")

    # 2. GRAPHIQUES
    st.write("### Analyse par Département")
    # Remplacez 'Departement' par le nom exact de votre colonne dans Kobo
    if 'Departement' in df.columns:
        fig_dept = px.bar(df['Departement'].value_counts(), 
                         labels={'value': 'Nombre de ménages', 'index': 'Département'},
                         color_value=df['Departement'].value_counts().index,
                         title="Répartition de la collecte")
        st.plotly_chart(fig_dept, use_container_width=True)

    # 3. RÉPARTITION PAR SEXE
    st.write("### Profil des Chefs de Ménage")
    c1, c2 = st.columns(2)
    with c1:
        if 'Sexe' in df.columns:
            fig_sexe = px.pie(df, names='Sexe', title="Sexe du Chef de Ménage", hole=0.4)
            st.plotly_chart(fig_sexe)
    with c2:
        if 'Nationalite' in df.columns:
            fig_nat = px.pie(df, names='Nationalite', title="Nationalité")
            st.plotly_chart(fig_nat)

    # 4. TABLEAU DE DONNÉES BRUTES
    with st.expander("Voir le détail des fiches collectées"):
        st.dataframe(df)

else:
    st.warning("En attente de synchronisation des données depuis les téléphones des enquêteurs...")

# Bouton de téléchargement Excel pour le QG
if df is not None:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger le rapport complet (CSV)", csv, "rapport_bounkani.csv", "text/csv")
