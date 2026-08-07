# TP n°2 — Élection du DR et du BDR avec OSPF

## 📖 Présentation

Dans ce laboratoire, nous étudions le mécanisme d'élection du **Designated Router (DR)** et du **Backup Designated Router (BDR)** dans un réseau **OSPF Broadcast**.

Lorsqu'un segment Ethernet relie plusieurs routeurs OSPF, une élection est organisée afin de limiter le nombre d'adjacences et de réduire le trafic d'échange des informations de topologie (LSA).

L'objectif de ce TP est de comprendre :

- le fonctionnement de l'élection DR/BDR ;
- l'influence de la priorité OSPF ;
- le rôle du Router ID ;
- le comportement non préemptif d'OSPF.

---

## 🎯 Objectifs

- Déployer OSPF sur un réseau Ethernet partagé.
- Configurer les Router ID.
- Modifier les priorités OSPF.
- Identifier le DR, le BDR et les DROTHER.
- Observer le comportement de l'élection.
- Comprendre pourquoi OSPF est un protocole non préemptif.

---

## 🖥️ Topologie

Cette architecture est composée de :

- 4 routeurs Cisco
- 1 switch Ethernet
- 4 réseaux LAN
- 1 réseau Ethernet partagé
- 4 interfaces Loopback

Le dossier **topology/** contient :

- le schéma réseau ;
- le projet GNS3.

---

## 🌐 Plan d'adressage

### Réseau OSPF partagé

| Routeur | Adresse |
|----------|----------|
| R1 | 10.0.0.1/24 |
| R2 | 10.0.0.2/24 |
| R3 | 10.0.0.3/24 |
| R4 | 10.0.0.4/24 |

### Réseaux LAN

| Routeur | Réseau |
|----------|---------|
| R1 | 192.168.10.0/24 |
| R2 | 192.168.20.0/24 |
| R3 | 192.168.30.0/24 |
| R4 | 192.168.40.0/24 |

### Interfaces Loopback

| Routeur | Adresse |
|----------|----------|
| R1 | 1.1.1.1/32 |
| R2 | 2.2.2.2/32 |
| R3 | 3.3.3.3/32 |
| R4 | 4.4.4.4/32 |

---

## ⚙️ Configuration réalisée

- Configuration IPv4
- Configuration des interfaces Loopback
- Configuration d'OSPF Area 0
- Définition des Router ID
- Configuration des priorités OSPF
- Désactivation de la recherche DNS
- Configuration des interfaces passives sur les LAN

---

## 🧪 Vérifications

Les commandes suivantes ont permis de valider le fonctionnement du protocole.

### Vérification des voisins

```bash
show ip ospf neighbor
```

---

### Vérification du DR et du BDR

```bash
show ip ospf interface Ethernet0/0
```

---

### Vérification des routes

```bash
show ip route ospf
```

---

### Vérification de la base de données

```bash
show ip ospf database
```

---

### Vérification générale

```bash
show ip protocols
```

---

## 🔬 Expériences réalisées

Au cours du laboratoire, plusieurs scénarios ont été testés :

- Élection initiale du DR et du BDR.
- Modification des priorités OSPF.
- Redémarrage du processus OSPF (`clear ip ospf process`).
- Observation de l'influence de l'ordre de redémarrage des routeurs.
- Validation du comportement **non préemptif** d'OSPF.

---

## 📌 Résultats

Ce TP met en évidence plusieurs points importants :

- Le routeur ayant la priorité la plus élevée est favorisé lors de l'élection.
- En cas d'égalité, le Router ID départage les routeurs.
- Une fois le DR élu, il conserve son rôle jusqu'à sa disparition.
- Un routeur rejoignant le réseau avec une priorité supérieure ne remplace pas automatiquement le DR.

---

## 📂 Arborescence

```text
TP-OSPF-DR-BDR/
├── README.md
├── LICENSE
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── topology/
│   ├── tp-ospf-dr-bdr.gns3
│   └── topology.png
└── screenshots/
    ├── show-ip-ospf-neighbor.png
    ├── show-ip-ospf-interface.png
    ├── show-ip-route-ospf.png
    ├── show-ip-ospf-database.png
    └── show-ip-protocols.png
```

---

## 🛠️ Technologies

- Cisco IOS
- OSPFv2
- IPv4
- GNS3
- Cisco CLI

---

## 📚 Compétences acquises

- Déploiement d'OSPF
- Compréhension du fonctionnement DR / BDR
- Gestion des priorités OSPF
- Configuration des Router ID
- Analyse des voisinages OSPF
- Analyse de la base de données OSPF
- Dépannage et validation d'une élection OSPF

---

## 🚀 Conclusion

Ce laboratoire permet de comprendre en détail le mécanisme d'élection DR/BDR sur un réseau Ethernet multi-accès. Il constitue une étape importante avant d'aborder des fonctionnalités OSPF plus avancées telles que les **Multi-Area**, les **Stub Areas**, la **redistribution de routes** ou encore l'**authentification OSPF**.