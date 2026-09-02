# TP OSPF – Open Shortest Path First

![Cisco](https://img.shields.io/badge/Cisco-IOS-blue?style=for-the-badge&logo=cisco)
![OSPF](https://img.shields.io/badge/OSPFv2-Routing-success?style=for-the-badge)
![IPv4](https://img.shields.io/badge/IPv4-Networking-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## Présentation

Ce dépôt regroupe une série de **travaux pratiques (TP)** consacrés à **OSPF (Open Shortest Path First)**, un protocole de routage dynamique **à état de liens (Link-State)** largement utilisé dans les réseaux d'entreprise.

L'objectif de cette série est de découvrir progressivement les mécanismes d'OSPF, depuis une configuration simple jusqu'à des scénarios avancés proches des environnements de production.

Chaque TP est documenté et comprend :

- une topologie réseau ;
- un plan d'adressage ;
- les fichiers de configuration Cisco IOS ;
- des captures d'écran des vérifications ;
- une documentation détaillée.

---

# Objectifs

À travers ces laboratoires, vous apprendrez à :

- Configurer OSPF sur des routeurs Cisco.
- Comprendre le fonctionnement des voisinages OSPF.
- Étudier l'élection DR / BDR.
- Concevoir des architectures Multi-Area.
- Optimiser le routage grâce aux coûts et à la bande passante.
- Sécuriser OSPF avec l'authentification.
- Mettre en œuvre la redistribution de routes.
- Dépanner un réseau OSPF.

---

# Contenu du dépôt

| TP | Sujet | Niveau | Statut |
|----|-------|:------:|:------:|
| TP01 | OSPF Single Area | 🟢 Débutant | ✅ |
| TP02 | Élection DR / BDR | 🟢 Débutant | ✅ |
| TP03 | Passive Interface | 🟢 Débutant | ⏳ |
| TP04 | Modification du coût OSPF | 🟢 Débutant | ✅ |
| TP05 | Bande passante et métrique | 🟡 Intermédiaire | ✅ |
| TP06 | Route par défaut | 🟡 Intermédiaire | ✅ |
| TP07 | OSPF Multi-Area | 🟡 Intermédiaire | ✅ |
| TP08 | Résumé de routes | 🟡 Intermédiaire | ✅ |
| TP09 | Authentification OSPF | 🟡 Intermédiaire | ✅ |
| TP10 | Redistribution RIP ↔ OSPF | 🔴 Avancé | ✅ |
| TP17 | OSPF avec HSRP | 🔴 Avancé | ⏳ |

---

# Structure du dépôt

```
TP-OSPF/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── TP01-OSPF-Single-Area/
├── TP02-DR-BDR-Election/
├── TP03-Passive-Interface/
├── TP04-OSPF-Cost/
├── TP05-Bandwidth/
├── TP06-Default-Route/
├── TP07-Multi-Area/
├── TP08-Route-Summarization/
├── TP09-OSPF-Authentication/
├── TP10-RIP-to-OSPF-Redistribution/
└── TP17-OSPF-HSRP/
```

---

# Prérequis

- GNS3, EVE-NG ou Cisco CML
- Cisco IOS
- Connaissances de base en IPv4
- Connaissances des protocoles de routage

---

# Technologies utilisées

- Cisco IOS
- OSPFv2
- IPv4
- Cisco CLI
- GNS3

---

# Compétences développées

- Routage dynamique
- Configuration Cisco IOS
- Conception de réseaux
- Analyse des tables de routage
- Dépannage réseau
- Optimisation du routage
- Sécurisation d'OSPF
- Bonnes pratiques d'administration réseau

---

# À propos

Ce dépôt fait partie d'une série de laboratoires consacrés aux technologies réseaux Cisco. L'objectif est de documenter ma progression, de partager des exemples concrets de configuration et de constituer un portfolio technique.

---

# Licence

Ce projet est distribué sous la licence **MIT**.

Voir le fichier **LICENSE** pour plus d'informations.

---

# Auteur

Sylvestre Mouafo

Technicien / Administrateur Systèmes & Réseaux

- GitHub : https://github.com/Sylvestre-M/
- LinkedIn : https://www.linkedin.com/in/vedel-sylvestre/