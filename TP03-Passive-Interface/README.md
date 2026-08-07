# TP03 – Configuration des interfaces passives OSPF

## Présentation

Dans ce troisième laboratoire consacré au protocole **OSPF (Open Shortest Path First)**, nous abordons une fonctionnalité essentielle : les **interfaces passives** (*Passive Interface*).

Par défaut, OSPF envoie périodiquement des **paquets Hello** sur toutes les interfaces participant au processus de routage afin de découvrir et de maintenir les relations de voisinage avec les autres routeurs.

Cependant, sur un réseau local (LAN) où seuls des postes clients sont connectés, aucun voisin OSPF n'est attendu. Continuer à envoyer des paquets Hello sur ces interfaces est donc inutile.

La commande **`passive-interface`** permet de résoudre ce problème.

Une interface configurée en mode passif :

- continue d'annoncer son réseau dans OSPF ;
- n'envoie plus de paquets Hello ;
- ne forme aucun voisin OSPF sur cette interface.

Cette configuration est une **bonne pratique** largement utilisée dans les infrastructures professionnelles.

---

# Objectifs

À la fin de ce TP, vous serez capable de :

- comprendre le rôle d'une interface passive ;
- configurer des interfaces passives sous Cisco IOS ;
- vérifier que les réseaux LAN restent annoncés dans OSPF ;
- vérifier que les voisinages OSPF sont uniquement établis entre les routeurs ;
- analyser le fonctionnement du protocole avant et après la configuration.

---

# Topologie

Cette topologie est composée de :

- 3 routeurs Cisco
- 3 commutateurs
- 6 postes clients
- 3 réseaux LAN
- 3 liaisons WAN en série
- 3 interfaces Loopback
- 1 Area OSPF (Area 0)

Le schéma de la topologie est disponible dans le dossier **topology/**.

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

# Configuration réalisée

Au cours de ce laboratoire, les opérations suivantes ont été réalisées :

- configuration des interfaces Ethernet et Série ;
- configuration des interfaces Loopback ;
- activation du protocole OSPF ;
- définition des Router ID ;
- annonce des réseaux dans l'Area 0 ;
- désactivation de la recherche DNS ;
- configuration des interfaces LAN en mode **Passive Interface**.

---

# Vérifications

Les commandes suivantes permettent de valider la configuration.

## Vérifier les voisinages OSPF

```bash
show ip ospf neighbor
```

Les voisinages doivent rester à l'état **FULL** uniquement entre les routeurs.

---

## Vérifier les interfaces OSPF

```bash
show ip ospf interface brief
```

Permet de visualiser les interfaces participant au processus OSPF.

---

## Vérifier les interfaces passives

```bash
show ip protocols
```

Les interfaces Ethernet doivent apparaître dans la liste des interfaces passives.

---

## Vérifier les routes

```bash
show ip route ospf
```

Les réseaux distants doivent continuer à être appris malgré l'utilisation des interfaces passives.

---

## Tester la connectivité

Depuis chaque PC :

- ping vers LAN 1
- ping vers LAN 2
- ping vers LAN 3

Tous les postes doivent communiquer.

---

# Résultat obtenu

Après la configuration :

- les interfaces Ethernet des réseaux LAN n'envoient plus de paquets Hello ;
- les réseaux LAN restent annoncés dans OSPF ;
- les voisinages sont uniquement établis sur les liaisons WAN ;
- la connectivité entre les trois réseaux est conservée.

---

# Pourquoi utiliser les interfaces passives ?

L'utilisation des interfaces passives présente plusieurs avantages :

- réduction du trafic OSPF inutile ;
- diminution de la charge processeur des routeurs ;
- amélioration de la sécurité en empêchant la création accidentelle de voisinages sur les réseaux utilisateurs ;
- respect des bonnes pratiques de conception des réseaux d'entreprise.

Dans un environnement professionnel, les interfaces connectées aux postes utilisateurs sont généralement configurées en **Passive Interface**.

---

# Structure du projet

```text
TP03-Passive-Interface/
├── configs/
│   ├── R1.cfg
│   ├── R2.cfg
│   └── R3.cfg
├── LICENSE
├── README.md
├── screenshots/
│   ├── show-ip-protocols-R1.png
│   ├── show-ip-protocols-R2.png
│   └── show-ip-protocols-R3.png
└── topology/
    ├── topology.png
    └── tp03-passive-interface.gns3
```

---

# Compétences développées

- Configuration d'OSPF
- Configuration des interfaces passives
- Configuration des Router ID
- Configuration des interfaces Loopback
- Analyse des voisinages OSPF
- Vérification des tables de routage
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

Ce TP met en évidence l'intérêt des **interfaces passives** dans un réseau OSPF. Bien qu'elles empêchent l'envoi des paquets Hello sur les interfaces LAN, elles continuent d'annoncer les réseaux connectés aux autres routeurs. Cette fonctionnalité permet d'optimiser le fonctionnement d'OSPF tout en renforçant la sécurité et en appliquant une bonne pratique largement adoptée dans les infrastructures d'entreprise.