# TP05 – Influence de la bande passante sur le coût OSPF

## Présentation

Dans ce cinquième laboratoire consacré au protocole **OSPF (Open Shortest Path First)**, nous étudions l'influence de la **bande passante** sur le calcul automatique de la métrique OSPF.

Par défaut, OSPF calcule le coût d'une interface à partir de sa bande passante. Plus la bande passante est élevée, plus le coût est faible et plus la liaison est privilégiée.

Contrairement au TP précédent, où le coût était modifié manuellement avec la commande **`ip ospf cost`**, ce laboratoire montre comment une modification de la commande **`bandwidth`** influence automatiquement la métrique OSPF.

Cette approche est importante pour comprendre le fonctionnement interne d'OSPF et la manière dont il sélectionne le meilleur chemin.

---

# Objectifs

À l'issue de ce laboratoire, vous serez capable de :

- Comprendre le calcul automatique du coût OSPF.
- Comprendre le rôle de la commande `bandwidth`.
- Observer l'évolution de la métrique OSPF.
- Vérifier la convergence du protocole.
- Analyser le changement de chemin dans la table de routage.
- Comparer l'utilisation de `bandwidth` et `ip ospf cost`.

---

# Rappel

Par défaut, Cisco calcule le coût OSPF grâce à la formule suivante :

```
Coût = Bande passante de référence / Bande passante de l'interface
```

Par défaut :

- Plus la bande passante est élevée, plus le coût est faible.
- Plus le coût est faible, plus OSPF privilégie cette liaison.

Dans ce TP, nous allons volontairement diminuer la bande passante d'une liaison série afin d'observer les conséquences sur le routage.

---

# Topologie

Le laboratoire est composé de :

- 3 routeurs Cisco
- 3 commutateurs
- 6 postes clients
- 3 réseaux LAN
- 3 liaisons WAN série
- 3 interfaces Loopback
- 1 Area OSPF (Area 0)

Le schéma de la topologie est disponible dans le dossier :

```
topology/
```

Le projet GNS3 est également fourni.

---

# Plan d'adressage

## Réseaux LAN

| Réseau | Adresse |
|---------|----------|
| LAN 1 | 192.168.10.0/24 |
| LAN 2 | 192.168.20.0/24 |
| LAN 3 | 192.168.30.0/24 |

## Réseaux WAN

| Liaison | Adresse |
|----------|----------|
| R1 ↔ R2 | 10.0.1.0/30 |
| R2 ↔ R3 | 10.0.2.0/30 |
| R1 ↔ R3 | 10.0.3.0/30 |

## Loopback

| Routeur | Adresse |
|----------|----------|
| R1 | 1.1.1.1/32 |
| R2 | 2.2.2.2/32 |
| R3 | 3.3.3.3/32 |

---

# Déroulement du TP

Dans un premier temps, la topologie est configurée avec les paramètres par défaut.

Le coût OSPF est calculé automatiquement en fonction de la bande passante des interfaces.

Une fois la connectivité vérifiée, la bande passante du lien **R1 ↔ R3** est réduite.

OSPF recalcule alors automatiquement la métrique de cette interface.

Si le nouveau coût devient supérieur à celui du chemin alternatif, OSPF choisit automatiquement un nouvel itinéraire.

---

# Configuration réalisée

Au cours de ce laboratoire :

- Configuration IPv4
- Configuration des interfaces Série
- Configuration des interfaces Loopback
- Configuration des Router ID
- Activation d'OSPF
- Configuration des interfaces passives
- Modification de la bande passante d'une interface Série
- Vérification du recalcul automatique du coût

---

# Vérifications

Les commandes suivantes permettent de vérifier le fonctionnement du protocole.

## Vérifier les voisins

```bash
show ip ospf neighbor
```

---

## Vérifier la bande passante

```bash
show interface serial2/1
```

---

## Vérifier le coût OSPF

```bash
show ip ospf interface serial2/1
```

---

## Vérifier la table de routage

```bash
show ip route ospf
```

---

## Vérifier les informations OSPF

```bash
show ip protocols
```

---

## Vérifier le chemin emprunté

Depuis PC1 :

```bash
trace 192.168.30.10
```

---

# Résultat attendu

Avant la modification de la bande passante :

```
PC1
 │
R1
 │
R3
 │
PC5
```

Après la modification :

```
PC1
 │
R1
 │
R2
 │
R3
 │
PC5
```

Le changement de bande passante entraîne une augmentation du coût OSPF.

OSPF choisit alors automatiquement le chemin présentant le coût total le plus faible.

---

# Différence avec le TP précédent

## TP04

Modification manuelle du coût :

```cisco
ip ospf cost 200
```

Le coût est imposé directement par l'administrateur.

---

## TP05

Modification de la bande passante :

```cisco
bandwidth 64
```

Le coût est recalculé automatiquement par OSPF.

Cette approche reflète davantage le fonctionnement natif du protocole.

---

# Captures d'écran

Le dossier **screenshots/** contient :

- show-interface-before.png
- show-interface-after.png
- show-ip-ospf-interface-before.png
- show-ip-ospf-interface-after.png
- show-ip-route-before.png
- show-ip-route-after.png
- traceroute-before.png
- traceroute-after.png

---

# Arborescence

```text
TP05-OSPF-Bandwidth/
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   └── R3.cfg
├── LICENSE
├── README.md
├── screenshots/
│   ├── show-interface-before.png
│   ├── show-interface-after.png
│   ├── show-ip-ospf-interface-before.png
│   ├── show-ip-ospf-interface-after.png
│   ├── show-ip-route-before.png
│   ├── show-ip-route-after.png
│   ├── traceroute-before.png
│   └── traceroute-after.png
└── topology/
    ├── topology.png
    └── tp05-ospf-bandwidth.gns3
```

---

# Compétences développées

- Configuration OSPF
- Compréhension des métriques
- Manipulation de la bande passante
- Analyse des tables de routage
- Vérification des interfaces
- Utilisation du traceroute
- Dépannage réseau
- Administration Cisco IOS

---

# Technologies utilisées

- Cisco IOS
- OSPFv2
- IPv4
- GNS3

---

# Conclusion

Ce laboratoire démontre que le coût OSPF est directement influencé par la bande passante des interfaces.

En modifiant la valeur de **`bandwidth`**, OSPF recalcule automatiquement la métrique de la liaison et peut sélectionner un nouvel itinéraire sans modifier la topologie physique du réseau.

Cette notion est essentielle pour comprendre le fonctionnement des protocoles de routage dynamiques et constitue une base indispensable avant l'étude des réseaux OSPF multi-aires ou des mécanismes de redistribution.