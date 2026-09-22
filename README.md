# MGMERL Data Automation & Quality Control — V2

Portfolio technique de **Mihajanirina Ravoavy**.

## Pipeline
**mWater / collecte terrain → validation MGMERL → Grande Base → calcul des indicateurs → PITT / reporting**

## Démonstration
- 6 500 formulaires synthétiques ;
- contrôle des doublons ;
- contrôle Femmes + Hommes / Total ;
- validation des unités ;
- détection d'activités hors référentiel ;
- détection de sites manquants ;
- Grande Base relationnelle simulée ;
- moteur de calcul des indicateurs ;
- qualité des données par TA ;
- traçabilité formulaire → activité → indicateur.

## Lancement
```bash
pip install -r requirements.txt
streamlit run app.py
```

Toutes les données sont fictives et anonymisées.
