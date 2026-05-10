# Feu Vert Annecy Dashboard — Guide de Déploiement

## Architecture en un coup d'œil

```
fv-dashboard/
├── engine/                   ← Moteur de données (pur Python, 0 dépendance Streamlit)
│   ├── utils.py              ← Parseurs, constantes de chemins, helpers de format
│   ├── global_stats.py       ← Fichiers SUC (CA, Marge, Fréq, RAF)
│   ├── families.py           ← comparatifCAv2_Famille CSV
│   ├── tires.py              ← Pneus CSV (par saison, catégorie, marque)
│   ├── ratios.py             ← Ratios_Atelier CSV (6 KPIs)
│   ├── vendor_ratios.py      ← Suivi Individuel des ratios (vendeurs LS)
│   └── defects.py            ← CA_Main_d_oeuvre (défectuosité atelier)
├── app.py                    ← Interface Streamlit (3 onglets)
├── .streamlit/config.toml    ← Thème sombre vert FV
├── Dockerfile                ← Image Python 3.12-slim, multi-stage
├── docker-compose.yml        ← Volumes + ports + healthcheck
├── requirements.txt          ← streamlit, pandas, plotly
└── data/                     ← Dossiers CSV (montés en volume)
    ├── SUC/
    ├── familles/
    ├── Pneus/
    ├── ratios_prioritaires/
    ├── suivi_vendeur/
    ├── defectuosite/
    ├── monthly_recap/
    └── trimestres/
```

---

## Prérequis

| Outil          | Version min | Vérification              |
|:---------------|:------------|:--------------------------|
| Docker Engine  | 24.x        | `docker --version`        |
| Docker Compose | v2.x        | `docker compose version`  |
| Python (local) | 3.12        | optionnel, pour dev local |
| Proxmox VM     | Debian 12+  | recommandé                |

---

## Étape 1 — Cloner / copier le projet sur le serveur

```bash
# Sur votre VM Proxmox (via SSH)
cd /opt
git clone <votre-repo> fv-dashboard
# OU copier via scp :
scp -r ./fv-dashboard user@proxmox-ip:/opt/fv-dashboard
cd /opt/fv-dashboard
```

---

## Étape 2 — Créer la structure des dossiers de données

```bash
mkdir -p data/{SUC,familles,Pneus,ratios_prioritaires,suivi_vendeur,defectuosite,monthly_recap,trimestres}
```

Ces dossiers restent **vides** dans le dépôt Git.
Vous y déposerez les CSV chaque semaine (voir Étape 5).

---

## Étape 3 — Ajuster les chemins dans docker-compose.yml (si besoin)

Si vos CSV sont ailleurs sur le serveur (ex. partage NFS, SMB monté en `/mnt/samba/`),
éditez la section `volumes` dans `docker-compose.yml` :

```yaml
volumes:
  # AVANT (chemin relatif local au projet)
  - ./data/SUC:/app/resources/SUC:ro

  # APRÈS (exemple partage NFS monté)
  - /mnt/samba/exports/SUC:/app/resources/SUC:ro
```

> **Ne modifiez jamais le côté droit** (après le `:`).
> Ce sont les chemins internes au conteneur, hardcodés dans `engine/utils.py`.

---

## Étape 4 — Premier démarrage

```bash
cd /opt/fv-dashboard

# Construire l'image et démarrer
docker compose up -d --build

# Vérifier que le conteneur est healthy
docker ps
docker compose logs -f app
```

Accès depuis votre réseau local :
```
http://<ip-proxmox-vm>:8501
```

---

## Étape 5 — Mise à jour hebdomadaire des CSV

C'est la **seule opération répétitive** chaque semaine.

### Quels fichiers déposer, où

| Dossier host `data/`          | Fichier attendu                                      | Identification automatique      |
|:------------------------------|:-----------------------------------------------------|:--------------------------------|
| `SUC/`                        | `SUC - Situation de chiffre*.csv` (×2 : semaine + MTD) | Période courte vs 1er du mois   |
| `SUC/`                        | `SUC - Objectifs Journaliers*.csv`                   | Présence colonne `libelleJour`  |
| `familles/`                   | `comparatifCAv2_Famille*.csv`                        | Nom du fichier                  |
| `Pneus/`                      | `Pneus*.csv`                                         | Nom du fichier                  |
| `ratios_prioritaires/`        | `Ratios_Atelier*.csv`                                | Colonne `libelleUnivers`        |
| `suivi_vendeur/`              | `Suivi Individuel des ratios atelier*.csv`           | Colonne `textbox390`            |
| `defectuosite/`               | `CA_Main_d_oeuvre*.csv`                              | Colonne `technicien3`           |

### Procédure de mise à jour

```bash
# 1. Supprimer les anciens fichiers de la semaine précédente
rm -f data/SUC/*.csv data/familles/*.csv data/Pneus/*.csv \
      data/ratios_prioritaires/*.csv data/suivi_vendeur/*.csv \
      data/defectuosite/*.csv

# 2. Copier les nouveaux exports
cp /chemin/vers/exports/semaine/*.csv data/SUC/
cp /chemin/vers/exports/familles/*.csv data/familles/
# etc.

# 3. Le dashboard se rafraîchit automatiquement (cache TTL = 5 min)
#    OU forcer un rafraîchissement immédiat avec le bouton ⟳ dans l'UI

# En alternative, redémarrer le conteneur pour vider le cache :
docker compose restart app
```

> **Astuce** : Automatiser cette copie avec un script cron ou un partage SMB
> monté directement dans `data/` — le dashboard se met à jour tout seul.

---

## Étape 6 — Accès depuis Windows (bureau)

Si le tableau de bord tourne sur un Proxmox et que votre PC est sur le même réseau :

1. Ouvrez Chrome / Edge
2. Tapez `http://192.168.x.x:8501` (l'IP de votre VM Proxmox)
3. Bookmarkez cette URL

Pour un accès via nom de domaine local (`http://fv.local`), utilisez Traefik
(les labels sont commentés dans `docker-compose.yml`).

---

## Dépannage courant

### Le dashboard affiche "En attente des fichiers CSV"

```bash
# Vérifier que les fichiers sont bien visibles dans le conteneur
docker exec fv_dashboard ls /app/resources/SUC/
docker exec fv_dashboard ls /app/resources/familles/
```

Si vide → les volumes ne sont pas montés correctement.
Vérifiez les chemins dans `docker-compose.yml` et relancez :
```bash
docker compose down && docker compose up -d
```

### Erreur "permission denied" sur les CSV

```bash
# Les fichiers doivent être lisibles par tous
chmod -R o+r data/
```

### Reconstruire l'image après modification du code

```bash
docker compose up -d --build
```

### Reconstruire sans cache (problème de dépendance)

```bash
docker compose build --no-cache && docker compose up -d
```

### Voir les logs en temps réel

```bash
docker compose logs -f app
```

---

## Modifier le thème / couleurs

Editez `.streamlit/config.toml` :
```toml
primaryColor    = "#78BE20"   # vert FV
backgroundColor = "#111827"   # fond
```
Le changement est pris en compte **sans rebuild** (le fichier est monté en volume).
Appuyez sur F5 dans le navigateur pour voir l'effet.

---

## Ajouter un nouveau KPI / nouveau fichier CSV

1. Créez (ou modifiez) un module dans `engine/` selon le pattern existant :
   - une fonction `parse_xxx(folder)` qui retourne `{"df": ..., "available": bool, "errors": [...]}`
2. Importez-la dans `app.py` et ajoutez la section UI dans le bon onglet
3. Reconstruisez l'image : `docker compose up -d --build`

---

## Structure des ports (réseau Proxmox)

```
PC Windows ──[LAN]──► Proxmox VM :8501 ──► Docker container :8501
                       (IP: 192.168.x.x)
```

Si vous souhaitez exposer sur HTTPS :
- Installez Caddy ou Nginx sur la VM comme reverse proxy
- Redirigez le trafic HTTPS :443 → localhost:8501
