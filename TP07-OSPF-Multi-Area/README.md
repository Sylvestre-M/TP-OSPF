# TP07 – OSPF Multi-Area et automatisation avec Netmiko

## 📖 Présentation

Dans ce laboratoire consacré au protocole **OSPF (Open Shortest Path First)**, nous allons mettre en place une architecture **OSPF Multi-Area** composée de plusieurs zones de routage.

L'objectif est de comprendre la segmentation d'un domaine OSPF en plusieurs **Areas**, le rôle de l'**Area 0**, des **ABR**, ainsi que le fonctionnement des routes **intra-area** et **inter-area**.

Le TP introduit également l'**automatisation réseau avec Python et Netmiko** afin de collecter automatiquement les informations de vérification sur l'ensemble des routeurs.

---

# 🎯 Objectifs

- Comprendre le fonctionnement d'OSPF Multi-Area.
- Comprendre le rôle de l'Area 0.
- Comprendre le rôle d'un ABR.
- Configurer plusieurs Areas OSPF.
- Configurer une Area normale.
- Configurer une Stub Area.
- Configurer une NSSA.
- Configurer des interfaces Loopback.
- Utiliser une Loopback comme Router-ID OSPF.
- Vérifier les voisinages OSPF.
- Vérifier les routes OSPF.
- Analyser la LSDB.
- Identifier les routes intra-area et inter-area.
- Automatiser les vérifications avec Python et Netmiko.

---

# 🏗️ Architecture

## Area 0

L'Area 0 constitue le **Backbone OSPF**.

```text
R1 ─── R2
│      │
│      │
R3 ─── R4
```

## Area 1

Area OSPF normale :

```text
R1
├── R5
└── R6
```

R1 est un **ABR** entre l'Area 0 et l'Area 1.

## Area 2

Area configurée en **Stub** :

```text
R2
│
R7
```

R2 est l'ABR entre l'Area 0 et l'Area 2.

## Area 3

Area configurée en **NSSA** :

```text
      R4
     /  \
   R8    R9
```

R4 est l'ABR entre l'Area 0 et l'Area 3.

---

# 🔢 Plan d'adressage

## Réseaux WAN

| Liaison | Réseau | Adresse côté 1 | Adresse côté 2 |
|---|---|---|---|
| R1 ↔ R2 | `10.0.0.0/30` | R1 `10.0.0.1` | R2 `10.0.0.2` |
| R1 ↔ R3 | `10.0.1.0/30` | R1 `10.0.1.1` | R3 `10.0.1.2` |
| R2 ↔ R3 | `10.0.2.0/30` | R2 `10.0.2.1` | R3 `10.0.2.2` |
| R3 ↔ R4 | `10.0.3.0/30` | R3 `10.0.3.1` | R4 `10.0.3.2` |
| R1 ↔ R5 | `10.0.4.0/30` | R1 `10.0.4.1` | R5 `10.0.4.2` |
| R1 ↔ R6 | `10.0.5.0/30` | R1 `10.0.5.1` | R6 `10.0.5.2` |
| R2 ↔ R7 | `10.0.6.0/30` | R2 `10.0.6.1` | R7 `10.0.6.2` |
| R4 ↔ R8 | `10.0.7.0/30` | R4 `10.0.7.1` | R8 `10.0.7.2` |
| R4 ↔ R9 | `10.0.8.0/30` | R4 `10.0.8.1` | R9 `10.0.8.2` |

---

# 🔄 Loopbacks

| Routeur | Loopback | Router-ID |
|---|---|---|
| R1 | `1.1.1.1/32` | `1.1.1.1` |
| R2 | `2.2.2.2/32` | `2.2.2.2` |
| R3 | `3.3.3.3/32` | `3.3.3.3` |
| R4 | `4.4.4.4/32` | `4.4.4.4` |
| R5 | `5.5.5.5/32` | `5.5.5.5` |
| R6 | `6.6.6.6/32` | `6.6.6.6` |
| R7 | `7.7.7.7/32` | `7.7.7.7` |
| R8 | `8.8.8.8/32` | `8.8.8.8` |
| R9 | `9.9.9.9/32` | `9.9.9.9` |

Les interfaces Loopback permettent d'utiliser une adresse stable comme **Router-ID OSPF**.

---

# 🔀 ABR

Un **ABR (Area Border Router)** possède des interfaces appartenant à plusieurs Areas.

```text
R1
├── Area 0
└── Area 1

R2
├── Area 0
└── Area 2

R4
├── Area 0
└── Area 3
```

Les ABR assurent l'échange des informations de routage entre les différentes Areas.

---

# 📡 Fonctionnement OSPF Multi-Area

Chaque Area possède sa propre base de données OSPF.

L'Area 0 constitue le backbone et permet de relier les différentes Areas.

Les routes peuvent notamment apparaître sous les formes :

```text
O
```

Route intra-area.

```text
O IA
```

Route inter-area.

---

# 🧪 Vérifications

## Interfaces

```cisco
show ip interface brief
```

## Processus OSPF

```cisco
show ip ospf
```

## Voisinage

```cisco
show ip ospf neighbor
```

L'état attendu est :

```text
FULL
```

## Interfaces OSPF

```cisco
show ip ospf interface brief
```

## Routes OSPF

```cisco
show ip route ospf
```

Les routes inter-area apparaissent notamment avec :

```text
O IA
```

## Table de routage

```cisco
show ip route
```

## LSDB

```cisco
show ip ospf database
```

## Protocoles

```cisco
show ip protocols
```

---

# 🤖 Automatisation avec Netmiko

Le projet utilise Python et Netmiko pour automatiser les vérifications.

```text
                    Python
                       │
                    Netmiko
                       │
        ┌──────────────┼──────────────┐
        │              │              │
       R1             R2             R3
        │              │              │
        ├──────────────┼──────────────┤
        │              │              │
       R4             ...            R9
```

Le script doit :

1. Charger la liste des équipements.
2. Établir les connexions SSH.
3. Envoyer les commandes de vérification.
4. Récupérer les sorties.
5. Analyser les informations.
6. Produire un tableau distinct pour chaque commande.
7. Présenter les résultats de manière lisible.
8. Identifier les éventuelles anomalies.

---

# 📊 Organisation des résultats

```text
============================================================
SHOW IP OSPF NEIGHBOR
============================================================

Routeur    Voisin       État       Interface
---------  -----------  ---------  ----------
R1         2.2.2.2      FULL       Serial2/0
R1         3.3.3.3      FULL       Serial2/1
R2         1.1.1.1      FULL       Serial2/0
```

```text
============================================================
SHOW IP ROUTE OSPF
============================================================

Routeur    Réseau        Type       Next-Hop
---------  ------------  ---------  ----------
R1         7.7.7.7/32    O IA       10.0.0.2
R2         5.5.5.5/32    O IA       10.0.0.1
```

---

# 🧪 Tests de connectivité

```text
R5 → 7.7.7.7
R7 → 5.5.5.5
R8 → 6.6.6.6
R9 → 1.1.1.1
```

---

# 📸 Captures d'écran

Les captures sont stockées dans :

```text
screenshots/
```

Exemples :

```text
show-ip-interface-brief-R1.png
show-ip-ospf-neighbor-R1.png
show-ip-ospf-database-R1.png
show-ip-route-ospf-R1.png
```

---

# 📁 Arborescence finale du projet

```text
TP07-OSPF-Multi-Area/
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   ├── R4.cfg
│   ├── R5.cfg
│   ├── R6.cfg
│   ├── R7.cfg
│   ├── R8.cfg
│   └── R9.cfg
│
├── scripts/
│   ├── verify_ospf.py
│   └── requirements.txt
│
├── screenshots/
│   ├── topology.png
│   ├── neighbors/
│   ├── routes/
│   ├── database/
│   └── verification/
│
├── topology/
│   └── TP07-OSPF-Multi-Area.gns3
│
├── addressing-plan.md
├── README.md
└── LICENSE
```

---

# 📂 Description de l'arborescence

| Élément | Utilisation |
|---|---|
| `configs/` | Configurations des routeurs Cisco |
| `scripts/` | Scripts Python Netmiko |
| `screenshots/` | Captures des vérifications |
| `results/` | Résultats générés automatiquement |
| `topology/` | Topologie GNS3 et schéma |
| `.gitignore` | Fichiers exclus du dépôt Git |
| `LICENSE` | Licence du projet |
| `README.md` | Documentation du TP |
| `requirements.txt` | Dépendances Python |

---

# 🛠️ Technologies utilisées

- Cisco IOS
- OSPFv2
- IPv4
- GNS3
- Python 3
- Netmiko
- Tabulate

---

# 📦 Prérequis

- GNS3
- Routeurs Cisco IOS
- Python 3
- Accès SSH aux routeurs
- Netmiko
- Tabulate

Les dépendances Python sont référencées dans :

```text
requirements.txt
```

---

# 🔐 Sécurité

Les identifiants SSH ne doivent jamais être stockés directement dans les scripts ou poussés sur GitHub.

Les informations sensibles doivent être stockées localement ou via des variables d'environnement.

Le fichier contenant ces informations doit être exclu du dépôt avec :

```text
.gitignore
```

---

# 📌 Résultats attendus

- Les interfaces sont `up/up`.
- Les Loopbacks sont accessibles.
- Les Router-ID sont correctement définis.
- Les voisinages OSPF sont `FULL`.
- L'Area 0 fonctionne comme Backbone.
- L'Area 1 fonctionne comme Area normale.
- L'Area 2 fonctionne comme Stub Area.
- L'Area 3 fonctionne comme NSSA.
- Les ABR assurent la communication entre les Areas.
- Les routes inter-area sont présentes.
- Les Loopbacks sont accessibles depuis les différentes Areas.
- Les vérifications peuvent être automatisées avec Netmiko.
- Les résultats sont présentés dans des tableaux distincts.

---

# 🎓 Compétences développées

- OSPF
- OSPF Multi-Area
- Area 0
- ABR
- Router-ID
- Loopback
- LSDB
- LSA
- Stub Area
- NSSA
- Routage inter-area
- Analyse de tables de routage
- Troubleshooting réseau
- Cisco IOS
- GNS3
- Python
- Netmiko
- Automatisation réseau
- Reporting réseau

---

# 📌 À retenir

```text
              AREA 1
             Normal
                │
                R1
                │
                │
AREA 0 ─────── Backbone ─────── R4
                │               │
                R2              │
                │               │
             AREA 2          AREA 3
              Stub            NSSA
                │             /   \
                R7            R8    R9
```

L'**Area 0** constitue le Backbone.

Les **ABR** assurent la communication entre les différentes Areas.

Les **Loopbacks** fournissent des Router-ID stables.

**Netmiko** permet d'automatiser les vérifications et de transformer les sorties CLI des routeurs en données structurées et exploitables.

---

# 👨‍💻 Auteur

**Sylvestre Mouafo**

Technicien / Administrateur Systèmes & Réseaux

Laboratoire pratique consacré au routage dynamique Cisco, à OSPF Multi-Area et à l'automatisation réseau avec Python et Netmiko.