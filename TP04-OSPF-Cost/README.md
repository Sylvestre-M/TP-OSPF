# TP04 – Modification du coût OSPF (OSPF Cost)

## Présentation

Dans ce quatrième laboratoire consacré au protocole **OSPF (Open Shortest Path First)**, nous nous intéressons à l'un des mécanismes les plus importants du protocole : **la métrique OSPF**, également appelée **Cost**.

Lorsqu'un routeur connaît plusieurs chemins pour atteindre une même destination, OSPF ne sélectionne pas le chemin comportant le moins de sauts. Il applique l'algorithme **Shortest Path First (SPF)** de Dijkstra afin de calculer le **coût total** de chaque itinéraire et retient celui dont la métrique est la plus faible.

L'objectif de ce TP est de comprendre comment cette métrique influence le routage et comment il est possible de modifier le chemin emprunté par les paquets sans modifier la topologie physique du réseau.

---

# Objectifs

À l'issue de ce laboratoire, vous serez capable de :

- Comprendre le principe de la métrique OSPF.
- Identifier le chemin choisi par OSPF.
- Modifier manuellement le coût d'une interface.
- Observer la convergence du protocole.
- Vérifier les modifications dans la table de routage.
- Analyser le chemin emprunté grâce au traceroute.

---

# Rappels sur le coût OSPF

Chaque interface OSPF possède un **coût**.

Le coût d'un chemin correspond à la **somme des coûts** de toutes les interfaces traversées.

OSPF sélectionne toujours le chemin dont le **coût total est le plus faible**.

Par défaut, Cisco calcule automatiquement ce coût en fonction de la bande passante de l'interface.

Plus le coût est faible, plus la liaison est privilégiée.

Le coût peut également être configuré manuellement avec :

```cisco
ip ospf cost <valeur>
```

---

# Topologie

Le laboratoire est composé de :

- 3 routeurs Cisco
- 3 commutateurs
- 6 postes clients
- 3 réseaux LAN
- 3 liaisons WAN en série
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

# Fonctionnement du TP

Avant toute modification, les deux chemins permettant d'atteindre le réseau **192.168.30.0/24** sont disponibles.

## Chemin direct

```
PC1
 │
R1
 │
R3
 │
PC5
```

## Chemin alternatif

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

Par défaut, le lien direct possède un coût plus faible.

OSPF choisit donc ce chemin.

Dans ce laboratoire, le coût de la liaison **R1 ↔ R3** est volontairement augmenté afin d'obliger OSPF à privilégier le chemin passant par **R2**.

---

# Configuration réalisée

Les opérations suivantes ont été effectuées :

- Configuration IPv4
- Configuration des interfaces Série
- Configuration des interfaces Loopback
- Configuration des Router ID
- Activation d'OSPF Area 0
- Configuration des interfaces passives
- Modification du coût OSPF
- Vérification de la convergence

---

# Vérifications

Les commandes suivantes permettent de valider le fonctionnement du protocole.

## Vérifier les voisins OSPF

```bash
show ip ospf neighbor
```

Les voisinages doivent rester à l'état **FULL**.

---

## Vérifier le coût des interfaces

```bash
show ip ospf interface
```

Cette commande permet de visualiser le coût attribué à chaque interface.

---

## Vérifier la table de routage

```bash
show ip route ospf
```

Les routes OSPF apparaissent avec le code :

```
O
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

Le traceroute permet de visualiser précisément les routeurs traversés avant et après la modification du coût.

---

# Résultat attendu

Avant la modification :

```
PC1
 │
R1
 │
R3
 │
PC5
```

Après avoir augmenté le coût :

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

OSPF choisit désormais le chemin dont le **coût total est le plus faible**.

---

# Pourquoi modifier le coût ?

La modification des métriques OSPF permet notamment de :

- privilégier certaines liaisons ;
- mettre en place des liens de secours ;
- optimiser les performances du réseau ;
- répartir le trafic ;
- contrôler les décisions de routage.

Cette fonctionnalité est utilisée quotidiennement dans les réseaux d'entreprise.

---

# Captures d'écran

Le dossier **screenshots/** contient les captures permettant de valider le TP :

- `show-ip-ospf-interface-R1.png`
- `show-ip-route-before.png`
- `show-ip-route-after.png`
- `traceroute-before.png`
- `traceroute-after.png`

Ces captures illustrent le changement de chemin après modification de la métrique OSPF.

---

# Structure du projet

```text
TP04-OSPF-Cost/
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   └── R3.cfg
├── LICENSE
├── README.md
├── screenshots/
│   ├── show-ip-ospf-interface-R1.png
│   ├── show-ip-route-before.png
│   ├── show-ip-route-after.png
│   ├── traceroute-before.png
│   └── traceroute-after.png
└── topology/
    ├── topology.png
    └── tp04-ospf-cost.gns3
```

---

# Compétences développées

- Configuration d'OSPF
- Manipulation des métriques OSPF
- Compréhension de l'algorithme SPF
- Analyse des tables de routage
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

Ce laboratoire met en évidence l'importance des métriques dans le protocole OSPF.

En modifiant simplement le coût d'une interface, il est possible d'influencer les décisions de routage sans modifier la topologie physique du réseau.

Cette technique est essentielle pour optimiser les performances, mettre en place des chemins de secours ou adapter les flux aux contraintes d'une infrastructure d'entreprise.

La compréhension des métriques OSPF constitue une compétence fondamentale pour tout administrateur ou ingénieur réseau travaillant sur des infrastructures Cisco.