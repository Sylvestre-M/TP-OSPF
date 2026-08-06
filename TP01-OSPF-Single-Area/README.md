# TP n°2 — Implémentation d'OSPF (Single Area)

## Présentation

Ce laboratoire a pour objectif de mettre en œuvre **OSPF (Open Shortest Path First)**, un protocole de routage dynamique à **état de liens (Link-State)** largement utilisé dans les réseaux d'entreprise.

Contrairement à RIP, qui repose sur un algorithme à vecteur de distance, OSPF construit une base de données de la topologie du réseau et calcule le meilleur chemin grâce à l'algorithme **Shortest Path First (SPF)** de Dijkstra.

Dans ce TP, l'ensemble des routeurs appartient à **l'Area 0 (Backbone Area)**.

---

## Objectifs pédagogiques

À l'issue de ce TP, vous serez capable de :

- Configurer OSPF sur plusieurs routeurs Cisco.
- Comprendre le rôle des **Router ID**.
- Mettre en œuvre des **interfaces Loopback**.
- Configurer les réseaux à l'aide des **Wildcard Masks**.
- Vérifier la formation des voisinages OSPF.
- Analyser les routes apprises dynamiquement.
- Valider la connectivité entre plusieurs réseaux.

---

## Topologie

Cette architecture est composée de :

- 3 routeurs Cisco
- 3 commutateurs
- 6 postes clients
- 3 réseaux LAN
- 3 liaisons WAN
- 1 Area OSPF (Area 0)

Le schéma de la topologie est disponible dans :

```
topology/topology.png
```

Le projet GNS3 est également fourni afin de reproduire facilement le laboratoire.

---

## Plan d'adressage

### Réseaux LAN

| Réseau | Adresse |
|---------|---------|
| LAN 1 | 192.168.10.0/24 |
| LAN 2 | 192.168.20.0/24 |
| LAN 3 | 192.168.30.0/24 |

### Réseaux WAN

| Liaison | Adresse |
|----------|----------|
| R1 ↔ R2 | 10.0.1.0/30 |
| R1 ↔ R3 | 10.0.2.0/30 |
| R2 ↔ R3 | 10.0.3.0/30 |

### Loopback

| Routeur | Adresse |
|----------|----------|
| R1 | 1.1.1.1/32 |
| R2 | 2.2.2.2/32 |
| R3 | 3.3.3.3/32 |

---

## Fonctionnalités implémentées

- Configuration IPv4
- Configuration des interfaces série
- Configuration des interfaces Loopback
- Configuration d'OSPF Process ID 1
- Configuration des Router ID
- Configuration des Wildcard Masks
- Désactivation de la recherche DNS
- Configuration des interfaces passives (LAN)
- Sauvegarde de la configuration

---

## Vérifications

Les vérifications suivantes ont été réalisées afin de valider le fonctionnement d'OSPF.

### Vérification des voisinages

```bash
show ip ospf neighbor
```

Validation de l'établissement des voisinages OSPF.

---

### Vérification des interfaces

```bash
show ip ospf interface brief
```

Affichage des interfaces participant au processus OSPF.

---

### Vérification de la base de données OSPF

```bash
show ip ospf database
```

Consultation des LSA (Link-State Advertisements).

---

### Vérification des routes

```bash
show ip route ospf
```

Les routes apprises dynamiquement sont identifiées par le code :

```
O
```

---

### Vérification générale

```bash
show ip protocols
```

Permet de contrôler le processus OSPF et les réseaux annoncés.

---

## Tests réalisés

Après configuration, plusieurs tests de connectivité ont été effectués :

- PC1 ↔ PC5
- PC2 ↔ PC6
- PC3 ↔ PC1
- PC4 ↔ PC2

L'ensemble des tests est concluant.

Les captures d'écran sont disponibles dans :

```
screenshots/
```

---

## Arborescence

```
TP-OSPF/
├── README.md
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   └── R3.cfg
├── topology/
│   ├── tp-ospf.gns3
│   └── topology.png
└── screenshots/
    ├── show-ip-ospf-neighbor.png
    ├── show-ip-ospf-interface-brief.png
    ├── show-ip-ospf-database.png
    ├── show-ip-route.png
    ├── show-ip-protocols.png
    └── ping-tests.png
```

---

## Compétences développées

- Routage dynamique
- OSPF Single Area
- Configuration Cisco IOS
- IPv4
- Dépannage réseau
- Analyse des tables de routage
- Analyse des voisinages OSPF
- Validation de la connectivité

---

## Technologies

- Cisco IOS
- OSPFv2
- IPv4
- GNS3

---

## À retenir

Ce laboratoire permet de comprendre les mécanismes fondamentaux d'OSPF :

- découverte automatique des voisins ;
- échange des informations de topologie ;
- calcul du meilleur chemin grâce à l'algorithme SPF ;
- convergence rapide ;
- meilleure évolutivité que RIP.

Il constitue une excellente introduction avant d'aborder des architectures plus avancées telles que **OSPF Multi-Area**, **la redistribution de routes**, ou encore **BGP**.

---

## Auteur

**Sylvestre Mouafo**

Technicien / Administrateur Systèmes & Réseaux

N'hésitez pas à consulter mes autres projets de réseau disponibles sur ce GitHub.