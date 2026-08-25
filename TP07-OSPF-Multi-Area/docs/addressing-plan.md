# Plan d'adressage — TP07 OSPF Multi-Area

## 1. Présentation

Ce document présente le plan d'adressage IP utilisé dans le TP07 consacré à la mise en œuvre d'une architecture **OSPF Multi-Area**.

La topologie utilise :

- 9 routeurs Cisco : R1 à R9
- des liaisons point-à-point en `/30`
- une Loopback0 sur chaque routeur
- les Loopback comme Router-ID OSPF
- 4 zones OSPF :
  - Area 0 — Backbone
  - Area 1 — Normal Area
  - Area 2 — Stub Area
  - Area 3 — NSSA

---

# 2. Loopbacks

Les Loopback0 sont utilisées comme Router-ID OSPF.

| Routeur | Interface | Adresse IP | Masque | Router-ID |
|---|---|---|---|---|
| R1 | Loopback0 | 1.1.1.1 | /32 | 1.1.1.1 |
| R2 | Loopback0 | 2.2.2.2 | /32 | 2.2.2.2 |
| R3 | Loopback0 | 3.3.3.3 | /32 | 3.3.3.3 |
| R4 | Loopback0 | 4.4.4.4 | /32 | 4.4.4.4 |
| R5 | Loopback0 | 5.5.5.5 | /32 | 5.5.5.5 |
| R6 | Loopback0 | 6.6.6.6 | /32 | 6.6.6.6 |
| R7 | Loopback0 | 7.7.7.7 | /32 | 7.7.7.7 |
| R8 | Loopback0 | 8.8.8.8 | /32 | 8.8.8.8 |
| R9 | Loopback0 | 9.9.9.9 | /32 | 9.9.9.9 |

---

# 3. Liaisons inter-routeurs

Les liaisons point-à-point utilisent des réseaux `/30`.

Chaque réseau fournit :

- 2 adresses IP utilisables
- 1 adresse réseau
- 1 adresse de broadcast

| Liaison | Réseau | Adresse R1/R2/etc. | Adresse R3/R4/etc. | Area |
|---|---|---|---|---|
| R1 ↔ R3 | 10.0.0.0/30 | R1: 10.0.0.1 | R3: 10.0.0.2 | 0 |
| R3 ↔ R4 | 10.0.1.0/30 | R3: 10.0.1.2 | R4: 10.0.1.1 | 0 |
| R1 ↔ R2 | 10.0.2.0/30 | R1: 10.0.2.1 | R2: 10.0.2.2 | 0 |
| R2 ↔ R4 | 10.0.3.0/30 | R2: 10.0.3.2 | R4: 10.0.3.1 | 0 |
| R1 ↔ R5 | 10.0.4.0/30 | R1: 10.0.4.1 | R5: 10.0.4.2 | 1 |
| R1 ↔ R6 | 10.0.5.0/30 | R1: 10.0.5.1 | R6: 10.0.5.2 | 1 |
| R2 ↔ R7 | 10.0.6.0/30 | R2: 10.0.6.1 | R7: 10.0.6.2 | 2 |
| R4 ↔ R8 | 10.0.7.0/30 | R4: 10.0.7.1 | R8: 10.0.7.2 | 3 |
| R4 ↔ R9 | 10.0.8.0/30 | R4: 10.0.8.1 | R9: 10.0.8.2 | 3 |

---

# 4. Synthèse par routeur

## R1

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 1.1.1.1 | /32 | 0 |
| Serial2/0 | 10.0.0.1 | /30 | 0 |
| Serial2/1 | 10.0.2.1 | /30 | 0 |
| Serial2/2 | 10.0.4.1 | /30 | 1 |
| Serial2/3 | 10.0.5.1 | /30 | 1 |

**Rôle : ABR Area 0 / Area 1**

---

## R2

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 2.2.2.2 | /32 | 0 |
| Serial2/1 | 10.0.2.2 | /30 | 0 |
| Serial2/0 | 10.0.3.2 | /30 | 0 |
| Serial2/2 | 10.0.6.1 | /30 | 2 |

**Rôle : ABR Area 0 / Area 2**

**Area 2 : Stub**

---

## R3

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 3.3.3.3 | /32 | 0 |
| Serial2/0 | 10.0.0.2 | /30 | 0 |
| Serial2/1 | 10.0.1.2 | /30 | 0 |

**Rôle : routeur interne Area 0**

---

## R4

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 4.4.4.4 | /32 | 0 |
| Serial2/0 | 10.0.1.1 | /30 | 0 |
| Serial2/1 | 10.0.3.1 | /30 | 0 |
| Serial2/2 | 10.0.7.1 | /30 | 3 |
| Serial2/3 | 10.0.8.1 | /30 | 3 |

**Rôle : ABR Area 0 / Area 3**

**Area 3 : NSSA**

---

## R5

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 5.5.5.5 | /32 | 1 |
| Serial2/0 | 10.0.4.2 | /30 | 1 |

**Rôle : routeur interne Area 1**

---

## R6

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 6.6.6.6 | /32 | 1 |
| Serial2/0 | 10.0.5.2 | /30 | 1 |

**Rôle : routeur interne Area 1**

---

## R7

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 7.7.7.7 | /32 | 2 |
| Serial2/0 | 10.0.6.2 | /30 | 2 |

**Rôle : routeur interne Area 2**

**Area 2 : Stub**

---

## R8

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 8.8.8.8 | /32 | 3 |
| Serial2/0 | 10.0.7.2 | /30 | 3 |

**Rôle : routeur interne Area 3**

**Area 3 : NSSA**

---

## R9

| Interface | Adresse IP | Masque | Area |
|---|---|---|---|
| Loopback0 | 9.9.9.9 | /32 | 3 |
| Serial2/0 | 10.0.8.2 | /30 | 3 |

**Rôle : routeur interne Area 3**

**Area 3 : NSSA**

---

# 5. Organisation des Areas

```text
                         AREA 1
                    ┌─────────────┐
                    │             │
                   R5            R6
                    │             │
                    └──────R1─────┘
                           │
                           │
                         AREA 0
                           │
                ┌──────────┼──────────┐
                │          │          │
               R3─────────R4─────────R2
                           │          │
                           │          │
                        AREA 3      AREA 2
                         NSSA        STUB
                       ┌─────┐         │
                       │     │         │
                      R8     R9       R7