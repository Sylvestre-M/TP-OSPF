# TP10 — Redistribution de routes entre RIP et OSPF

![Cisco](https://img.shields.io/badge/Cisco-IOS-red?logo=cisco)
![GNS3](https://img.shields.io/badge/GNS3-Lab-blue)
![Python](https://img.shields.io/badge/Python-3.x-yellow?logo=python)
![Netmiko](https://img.shields.io/badge/Netmiko-Automation-green)

## 📌 Présentation

Ce TP met en œuvre deux domaines de routage :

- **OSPF Area 0** : R1, R2, R3, R4 et ASBR
- **RIP v2** : R9, R5, R6, R8 et ASBR

L'**ASBR** constitue le point de redistribution entre les deux protocoles.

Objectif final : mettre en place une **redistribution bidirectionnelle RIP ↔ OSPF**, puis vérifier la propagation des routes.

## 🗺️ Topologie

```text
                 OSPF AREA 0
       R1 ───── R2 ───────── R4 ───── R3
                  \          //
                   \        //
                       ASBR
                      /    \
                    RIP    RIP
                    /        \
                   R9        R6
                  /  \      /  \
                 R5   ...   ...   R8
```

## Routeurs

| Routeur | Router-ID | Domaine |
|---|---|---|
| R1 | 1.1.1.1 | OSPF |
| R2 | 2.2.2.2 | OSPF |
| R3 | 3.3.3.3 | OSPF |
| R4 | 4.4.4.4 | OSPF |
| ASBR | 5.5.5.5 | OSPF + RIP |
| R9 | 6.6.6.6 | RIP |
| R5 | 7.7.7.7 | RIP |
| R6 | 8.8.8.8 | RIP |
| R8 | 9.9.9.9 | RIP |

## 🌐 Plan d'adressage

### OSPF — Area 0

| Réseau | Liaison |
|---|---|
| `10.0.1.0/30` | R1 ↔ R2 |
| `10.0.2.0/30` | R1 ↔ R4 |
| `10.0.3.0/30` | R1 ↔ R3 |
| `10.0.4.0/30` | R2 ↔ R3 |
| `10.0.5.0/30` | R2 ↔ R4 |
| `10.0.6.0/30` | R3 ↔ R4 |
| `10.0.7.0/30` | R2 ↔ ASBR |
| `10.0.8.0/30` | R4 ↔ ASBR |

### RIP v2

| Réseau | Liaison |
|---|---|
| `10.0.9.0/30` | ASBR ↔ R9 |
| `10.0.10.0/30` | ASBR ↔ R6 |
| `10.0.11.0/30` | R9 ↔ R5 |
| `10.0.12.0/30` | R9 ↔ R6 |
| `10.0.13.0/30` | R6 ↔ R8 |
| `10.0.14.0/30` | R5 ↔ R8 |

## 🔌 Ports Telnet GNS3

| Routeur | Port |
|---|---:|
| R1 | 5009 |
| R2 | 5010 |
| R3 | 5011 |
| R4 | 5012 |
| R5 | 5013 |
| R6 | 5014 |
| ASBR | 5015 |
| R8 | 5016 |
| R9 | 5017 |

## 🛠️ Installation

```bash
python3 --version
pip install -r requirements.txt
```

Ou :

```bash
pip install netmiko PySide6
```

## 📁 Scripts

### Reset

```bash
python3 scripts/reset_tp10_routers.py
```

### Interfaces / adressage

```bash
python3 scripts/config_tp10_interfaces.py
```

Configure les adresses IP, les hostnames et `no ip domain-lookup`.

### RIP

Routeurs : R9, R5, R6, R8, ASBR.

```cisco
router rip
 version 2
 no auto-summary
 network 10.0.0.0
```

Vérification :

```cisco
show ip protocols
show ip route rip
show ip rip database
```

### OSPF

Routeurs : R1, R2, R3, R4, ASBR.

Exemple R1 :

```cisco
router ospf 1
 router-id 1.1.1.1
 network 10.0.1.0 0.0.0.3 area 0
 network 10.0.2.0 0.0.0.3 area 0
 network 10.0.3.0 0.0.0.3 area 0
```

Vérification :

```cisco
show ip ospf neighbor
show ip ospf interface brief
show ip route ospf
show ip protocols
```

## 🔄 Redistribution OSPF → RIP

Sur **ASBR uniquement** :

```cisco
enable
configure terminal

router rip
 version 2
 no auto-summary
 redistribute ospf 1 metric 2

end
copy running-config startup-config
```

Vérifications :

```cisco
show ip protocols
show ip route rip
```

Sur R9 et R6 :

```cisco
show ip route rip
show ip rip database
```

Les réseaux OSPF doivent apparaître dans le domaine RIP après propagation.

## 🔄 Redistribution RIP → OSPF

À réaliser après validation de la première direction.

Sur **ASBR** :

```cisco
enable
configure terminal

router ospf 1
 redistribute rip subnets

end
copy running-config startup-config
```

Vérification :

```cisco
show ip protocols
show ip route ospf
```

Sur R1, R2, R3 et R4 :

```cisco
show ip route ospf
```

Les réseaux RIP doivent apparaître comme routes OSPF externes.

## 🔎 Vérifications finales

### Interfaces

```cisco
show ip interface brief
```

### OSPF

```cisco
show ip ospf neighbor
show ip ospf interface brief
show ip route ospf
show ip protocols
```

### RIP

```cisco
show ip protocols
show ip route rip
show ip rip database
```

### Table complète

```cisco
show ip route
```

### Connectivité

```cisco
ping <adresse-ip>
traceroute <adresse-ip>
```

## 💾 Sauvegarde

Après chaque étape :

```cisco
copy running-config startup-config
```

Vérification :

```cisco
show startup-config
```

## 🧪 Méthode de validation

Le TP est réalisé progressivement :

1. Adressage IP
2. Hostnames et désactivation DNS
3. RIP v2
4. OSPF Area 0
5. Vérification des voisinages
6. Redistribution OSPF → RIP
7. Vérification des routes RIP
8. Redistribution RIP → OSPF
9. Vérification des routes OSPF
10. Tests de connectivité finaux

La redistribution est volontairement activée **dans une seule direction à la fois** afin de faciliter le diagnostic.

## 🖥️ Automatisation

Les scripts utilisent :

- Python 3
- Netmiko
- PySide6
- Telnet GNS3

Les interfaces graphiques permettent de lancer les configurations et d'afficher les sorties IOS.

Les identifiants Cisco ne doivent jamais être enregistrés dans Git.

## 🔐 `.gitignore`

Recommandé :

```gitignore
__pycache__/
*.pyc
.env
*.log
logs/*
!logs/.gitkeep
```

Ne jamais publier :

- mots de passe ;
- secrets Enable ;
- configurations contenant des credentials ;
- logs contenant des informations sensibles.

## 📊 Progression

| Étape | État |
|---|---|
| Reset routeurs | ✅ |
| Adressage IP | ✅ |
| Hostnames | ✅ |
| Désactivation DNS lookup | ✅ |
| RIP v2 | ✅ |
| OSPF Area 0 | ✅ |
| Vérification OSPF | ✅ |
| OSPF → RIP | ✅ |
| RIP → OSPF | ✅ |
| Vérification finale | ✅ |

## 👨‍💻 Auteur

**Sylvestre Mouafo**

Projet réalisé avec **Cisco IOS + GNS3 + Python/Netmiko**.
