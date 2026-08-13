# TP06 – Propagation d'une route par défaut avec OSPF

## 📖 Présentation

Dans ce sixième laboratoire consacré au protocole **OSPF (Open Shortest Path First)**, nous allons mettre en place la **propagation d'une route par défaut** dans un domaine OSPF.

L'objectif est de simuler une infrastructure d'entreprise dans laquelle un routeur, **R1**, joue le rôle de **routeur de sortie vers Internet**.

Les routeurs **R2** et **R3** ne possèdent pas de route spécifique vers les réseaux externes. Ils doivent donc utiliser une **route par défaut** apprise dynamiquement via OSPF.

La topologie contient trois routeurs internes appartenant à l'**Area 0** et un quatrième routeur représentant un accès Internet simulé.

---

## 🎯 Objectifs

À l'issue de ce TP, vous serez capable de :

* Comprendre le fonctionnement d'une route par défaut.
* Configurer une route par défaut statique sur un routeur.
* Propager cette route dans un domaine OSPF.
* Comprendre le rôle de `default-information originate`.
* Identifier une route par défaut OSPF dans une table de routage.
* Comprendre le fonctionnement d'une route externe OSPF.
* Vérifier le chemin emprunté vers une destination externe.
* Valider la connectivité entre les réseaux internes et le réseau simulant Internet.

---

# 🏗️ Architecture

La topologie est composée de :

* 4 routeurs Cisco :

  * R1
  * R2
  * R3
  * INTERNET
* 2 commutateurs
* 4 postes clients
* 2 réseaux LAN
* 3 liaisons inter-routeurs OSPF
* 1 liaison entre R1 et le routeur INTERNET
* 3 interfaces Loopback
* 1 Area OSPF : Area 0

### Rôle des équipements

| Équipement | Rôle                               |
| ---------- | ---------------------------------- |
| R1         | Routeur de sortie / ASBR           |
| R2         | Routeur interne                    |
| R3         | Routeur interne                    |
| INTERNET   | Routeur simulant le réseau externe |
| PC1 / PC2  | LAN 1                              |
| PC3 / PC4  | LAN 2                              |

---

# 🌐 Plan d'adressage

## Réseaux WAN

| Liaison       | Réseau        | Adresse côté 1 | Adresse côté 2      |
| ------------- | ------------- | -------------- | ------------------- |
| R1 ↔ R2       | `10.0.0.0/30` | R1 `10.0.0.2`  | R2 `10.0.0.1`       |
| R1 ↔ R3       | `10.0.1.0/30` | R1 `10.0.1.2`  | R3 `10.0.1.1`       |
| R2 ↔ R3       | `10.0.2.0/30` | R2 `10.0.2.1`  | R3 `10.0.2.2`       |
| R1 ↔ INTERNET | `10.0.3.0/30` | R1 `10.0.3.1`  | INTERNET `10.0.3.2` |

---

## Réseaux LAN

| LAN   | Réseau            | Passerelle       |
| ----- | ----------------- | ---------------- |
| LAN 1 | `192.168.10.0/24` | `192.168.10.254` |
| LAN 2 | `192.168.20.0/24` | `192.168.20.254` |

---

## Interfaces Loopback

| Routeur  | Loopback     |
| -------- | ------------ |
| R1       | `1.1.1.1/32` |
| R2       | `2.2.2.2/32` |
| R3       | `3.3.3.3/32` |
| INTERNET | `8.8.8.8/32` |

La Loopback `8.8.8.8/32` est utilisée ici pour simuler une destination externe sur Internet.

---

# 🧩 Principe du laboratoire

Le réseau interne fonctionne avec OSPF.

```text
                  INTERNET
                  8.8.8.8
                     │
                     │ 10.0.3.0/30
                     │
                    R1
                 /      \
                /        \
        10.0.0.0/30    10.0.1.0/30
              /            \
             R2------------R3
                  10.0.2.0/30
```

R1 possède une connexion vers le réseau externe.

Il devient donc le **point de sortie** du réseau OSPF.

---

# 🚪 Route par défaut

R1 possède une route par défaut vers le routeur INTERNET :

```text
0.0.0.0/0 → 10.0.3.2
```

Cette route indique à R1 :

> Pour toute destination inconnue, envoyer le trafic vers INTERNET.

Cependant, le simple fait de créer cette route sur R1 ne suffit pas pour que R2 et R3 l'utilisent.

La route par défaut doit être **annoncée dans OSPF**.

---

# 📡 Propagation avec OSPF

R1 annonce la route par défaut dans le domaine OSPF.

La commande utilisée est :

```cisco
default-information originate
```

Cette commande permet à OSPF de générer une route par défaut externe dans le domaine de routage. Sur Cisco IOS, la route est par défaut de type **E2**.

R2 et R3 peuvent alors apprendre :

```text
O*E2 0.0.0.0/0
```

---

# 🔎 Signification de `O*E2`

Une entrée comme :

```text
O*E2 0.0.0.0/0
```

peut être décomposée ainsi :

| Élément     | Signification                |
| ----------- | ---------------------------- |
| `O`         | Route apprise via OSPF       |
| `*`         | Route candidate par défaut   |
| `E2`        | Route OSPF externe de type 2 |
| `0.0.0.0/0` | Route par défaut             |

---

# 🔄 Chemin du trafic

Lorsqu'un poste du LAN 1 souhaite atteindre une destination externe :

```text
PC1
 │
 ▼
R2
 │
 ▼
R1
 │
 ▼
INTERNET
 │
 ▼
8.8.8.8
```

R2 ne connaît pas nécessairement une route spécifique vers `8.8.8.8`.

Il utilise donc :

```text
0.0.0.0/0
```

apprise via OSPF.

---

# 🧪 Tests

## Vérification des voisinages

Sur R1 :

```cisco
show ip ospf neighbor
```

R1 doit avoir deux voisins :

```text
R2
R3
```

Les voisinages doivent être à l'état :

```text
FULL
```

---

## Vérification de la route par défaut sur R1

```cisco
show ip route
```

R1 doit posséder une route statique par défaut similaire à :

```text
S* 0.0.0.0/0 [1/0] via 10.0.3.2
```

---

## Vérification de la route par défaut sur R2

```cisco
show ip route
```

R2 doit apprendre une route similaire à :

```text
O*E2 0.0.0.0/0
```

---

## Vérification sur R3

```cisco
show ip route
```

R3 doit également apprendre :

```text
O*E2 0.0.0.0/0
```

---

# 🌍 Test vers Internet

Depuis PC1 :

```text
ping 8.8.8.8
```

Puis :

```text
trace 8.8.8.8
```

Le chemin attendu est :

```text
PC1
 ↓
R2
 ↓
R1
 ↓
INTERNET
 ↓
8.8.8.8
```

Depuis PC3 :

```text
ping 8.8.8.8
```

Le chemin attendu est :

```text
PC3
 ↓
R3
 ↓
R1
 ↓
INTERNET
 ↓
8.8.8.8
```

---

# 🔬 Vérification de la base OSPF

Pour analyser les informations distribuées par OSPF :

```cisco
show ip ospf database
```

Cette vérification permet notamment d'observer les informations liées aux routes externes injectées dans le domaine OSPF.

---

# ⚠️ Point important

Une route par défaut créée sur R1 avec :

```text
0.0.0.0/0
```

n'est pas automatiquement propagée par OSPF.

Il faut explicitement demander à OSPF de l'annoncer avec :

```text
default-information originate
```

Cisco précise également qu'il est possible d'utiliser `default-information originate always` pour annoncer la route par défaut même lorsque le routeur ne possède pas lui-même de route par défaut.

Dans ce TP, nous n'utilisons volontairement **pas `always`**, afin de reproduire un fonctionnement réaliste : R1 ne doit annoncer une sortie par défaut que s'il dispose effectivement d'une route par défaut vers l'extérieur.

---

# 📸 Captures d'écran

Les captures suivantes doivent être ajoutées au dossier `screenshots/` :

* `show-ip-ospf-neighbor-R1.png`
* `show-ip-ospf-neighbor-R2.png`
* `show-ip-ospf-neighbor-R3.png`
* `show-ip-route-R1.png`
* `show-ip-route-R2.png`
* `show-ip-route-R3.png`
* `show-ip-ospf-database-R2.png`
* `show-ip-ospf-database-R3.png`
* `ping-internet-PC1.png`
* `ping-internet-PC3.png`
* `traceroute-internet-PC1.png`

---

# 📁 Arborescence

```text
TP06-OSPF-Default-Route/
├── configs/
│   ├── INTERNET.cfg
│   ├── R1.cfg
│   ├── R2.cfg
│   └── R3.cfg
├── LICENSE
├── README.md
├── screenshots/
│   ├── show-ip-ospf-neighbor-R1.png
│   ├── show-ip-ospf-neighbor-R2.png
│   ├── show-ip-ospf-neighbor-R3.png
│   ├── show-ip-route-R1.png
│   ├── show-ip-route-R2.png
│   ├── show-ip-route-R3.png
│   ├── show-ip-ospf-database-R2.png
│   ├── show-ip-ospf-database-R3.png
│   ├── ping-internet-PC1.png
│   ├── ping-internet-PC3.png
│   └── traceroute-internet-PC1.png
└── topology/
    ├── topology.png
    └── tp06-ospf-default-route.gns3
```

---

# 🛠️ Technologies utilisées

* Cisco IOS
* OSPFv2
* IPv4
* GNS3
* Routage statique
* Routage dynamique

---

# 🎓 Compétences développées

* Configuration OSPF
* Configuration d'une route par défaut
* Propagation d'une route par défaut avec OSPF
* Compréhension des routes externes OSPF
* Analyse des tables de routage
* Analyse de la base OSPF
* Utilisation de `ping`
* Utilisation de `traceroute`
* Dépannage réseau
* Administration Cisco IOS

---

# 📌 À retenir

Ce TP permet de comprendre un scénario très courant dans une infrastructure d'entreprise :

```text
                    INTERNET
                       │
                       │
                      R1
                 Routeur de sortie
                    /    \
                   /      \
                  R2------R3
```

R1 possède la connexion vers l'extérieur et annonce une **route par défaut** au domaine OSPF.

R2 et R3 n'ont donc pas besoin de connaître individuellement toutes les destinations externes. Ils peuvent envoyer leur trafic inconnu vers R1 grâce à :

```text
O*E2 0.0.0.0/0
```

Cette architecture constitue une base importante avant d'aborder des notions plus avancées telles que la **redistribution de routes**, les **routes externes OSPF E1/E2** et les architectures **OSPF Multi-Area**.

---

# 👨‍💻 Auteur

**Sylvestre Mouafo**

Technicien / Administrateur Systèmes & Réseaux

Projet réalisé dans le cadre d'une série de laboratoires pratiques consacrés aux technologies de routage et aux infrastructures réseau Cisco.
