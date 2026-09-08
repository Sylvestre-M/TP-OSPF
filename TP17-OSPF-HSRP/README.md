# TP17 — OSPF avec redondance HSRP

Projet pédagogique d'automatisation d'une topologie Cisco/GNS3 avec **Telnet**, **HSRP** et **OSPF**.

## Objectifs

- Configurer l'adressage IP.
- Mettre en place le routage inter-VLAN.
- Mettre en place HSRP pour la redondance des passerelles.
- Mettre en place OSPF.
- Vérifier les interfaces, HSRP, voisins et routes OSPF.
- Sauvegarder les configurations.
- Générer des captures PNG des vérifications.
- Conserver les opérations dans des fichiers log.

## Arborescence

```text
TP17-OSPF-HSRP/
├── README.md
├── requirements.txt
├── scripts/
│   ├── reset_devices.py
│   ├── configure_addressing.py
│   ├── configure_hsrp.py
│   ├── configure_ospf.py
│   └── captures_verification_tp17.py
├── configs/
├── captures/
└── logs/
```

## Prérequis

- Python 3.9+
- GNS3
- Routeurs Cisco IOS
- Telnet
- `netmiko`
- `PySide6`
- `Pillow`

Installation :

```bash
pip install -r requirements.txt
```

## Ports Telnet GNS3

| Routeur | Port |
|---|---:|
| R1 | 5000 |
| R2 | 5001 |
| R3 | 5002 |
| R4 | 5003 |
| R5 | 5004 |
| R6 | 5005 |

Les scripts utilisent `127.0.0.1`.

## HSRP

Répartition prévue :

| VLAN | Active | Standby | VIP |
|---|---|---|---|
| VLAN 10 | R1 | R5 | 192.168.10.254 |
| VLAN 20 | R2 | R5 | 192.168.20.254 |
| VLAN 30 | R3 | R6 | 192.168.30.254 |
| VLAN 40 | R4 | R6 | 192.168.40.254 |

Priorités :

```cisco
standby <group> priority 110
standby <group> preempt
```

pour l'Active, et `100` pour le Standby.

**Important :** les deux routeurs HSRP d'un même VLAN doivent partager le même domaine L2.

Vérification :

```cisco
show standby brief
```

## OSPF

Router-ID :

```text
R1 → 1.1.1.1
R2 → 2.2.2.2
R3 → 3.3.3.3
R4 → 4.4.4.4
R5 → 5.5.5.5
R6 → 6.6.6.6
```

Configuration type :

```cisco
router ospf 1
 router-id X.X.X.X
 network <réseau> <wildcard> area <area>
```

Vérifications :

```cisco
show ip ospf neighbor
show ip route ospf
show ip ospf interface brief
```

Les voisinages OSPF attendus doivent être en `FULL`.

## Captures PNG

Le script `captures_verification_tp17.py` exécute :

```cisco
show ip interface brief
show standby brief
show ip ospf neighbor
show ip route ospf
show ip ospf interface brief
```

Pour 6 routeurs, cela représente jusqu'à **30 captures PNG**.

Lancement :

```bash
python captures_verification_tp17.py
```

Les fichiers sont enregistrés dans :

```text
captures/
```

Exemple :

```text
R1_show_ip_interface_brief.png
R1_show_standby_brief.png
R1_show_ip_ospf_neighbor.png
R1_show_ip_route_ospf.png
R1_show_ip_ospf_interface_brief.png
```

## Logs

Les opérations sont enregistrées dans :

```text
logs/
```

Les fichiers sont horodatés et contiennent notamment les connexions, commandes, erreurs et sorties de vérification.

## Sauvegarde

Après configuration :

```cisco
copy running-config startup-config
```

Vérification :

```cisco
show startup-config
```

## Dépannage

### OSPF ne forme pas de voisinage

```cisco
show ip interface brief
show ip ospf neighbor
show ip ospf interface brief
```

Vérifier l'adressage, les interfaces, les réseaux OSPF et les areas.

### HSRP ne fonctionne pas

```cisco
show standby brief
```

Vérifier la VIP, les adresses physiques, les priorités et surtout que les deux interfaces sont dans le même domaine L2.

### Telnet ne répond pas

Tester par exemple :

```bash
telnet 127.0.0.1 5000
```

Puis vérifier que le routeur est démarré dans GNS3 et que le port correspond au script.

## Vérifications finales

Sur chaque routeur :

```cisco
show ip interface brief
show standby brief
show ip ospf neighbor
show ip route ospf
show ip ospf interface brief
```

Puis effectuer des `ping` entre les réseaux/VPCS.

## Avertissement

Les noms d'interfaces et les réseaux de transit doivent correspondre exactement à la topologie GNS3 utilisée. Vérifier la configuration avant d'exécuter un script d'automatisation.
