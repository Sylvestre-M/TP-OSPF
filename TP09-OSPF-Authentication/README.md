# TP09 — OSPF Security & Automation

## 📋 Description

Ce TP a pour objectif de mettre en œuvre, sécuriser et vérifier une
topologie OSPF composée de trois routeurs Cisco.

L'objectif est de passer d'une configuration OSPF fonctionnelle à une
configuration intégrant des mécanismes de sécurité et des contrôles
automatisés.

La configuration et la vérification sont réalisées avec Python,
Netmiko et Telnet.

---

## 🎯 Objectifs

À l'issue du TP, les éléments suivants doivent être maîtrisés :

- configuration de l'adressage IPv4 ;
- configuration d'OSPF ;
- utilisation d'une Area 0 ;
- définition explicite des Router-ID ;
- configuration de `passive-interface` ;
- authentification OSPF MD5 ;
- vérification des adjacencies OSPF ;
- vérification des routes OSPF ;
- automatisation avec Python ;
- connexion aux routeurs via Telnet ;
- génération de fichiers de configuration ;
- génération automatique de captures PNG ;
- génération de rapports de vérification ;
- journalisation des opérations.

---

## 🗺️ Topologie

La topologie est composée de trois routeurs :

```text
                         R1
                        /  \
                       /    \
              10.0.1.0/30  10.0.3.0/30
                     /        \
                    /          \
                   R2----------R3
                       10.0.2.0/30