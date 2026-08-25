from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


# ============================================================
# Paramètres de connexion GNS3
# ============================================================

USERNAME = "admin"
PASSWORD = "cisco"

DEVICES = {
    "R1": {
        "host": "127.0.0.1",
        "port": 5000,
    },
    "R2": {
        "host": "127.0.0.1",
        "port": 5001,
    },
    "R3": {
        "host": "127.0.0.1",
        "port": 5002,
    },
    "R4": {
        "host": "127.0.0.1",
        "port": 5003,
    },
    "R5": {
        "host": "127.0.0.1",
        "port": 5004,
    },
    "R6": {
        "host": "127.0.0.1",
        "port": 5005,
    },
    "R7": {
        "host": "127.0.0.1",
        "port": 5006,
    },
    "R8": {
        "host": "127.0.0.1",
        "port": 5007,
    },
    "R9": {
        "host": "127.0.0.1",
        "port": 5008,
    },
}


# ============================================================
# Configuration de chaque routeur
# ============================================================

CONFIGS = {

    # ========================================================
    # R1
    # Area 0 + Area 1
    # ========================================================

    "R1": [
        "hostname R1",
        "no ip domain lookup",

        # Loopback
        "interface Loopback0",
        "ip address 1.1.1.1 255.255.255.255",
        "no shutdown",
        "exit",

        # R1 <-> R3 - Area 0
        "interface Serial2/0",
        "ip address 10.0.0.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R1 <-> R2 - Area 0
        "interface Serial2/1",
        "ip address 10.0.2.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R1 <-> R5 - Area 1
        "interface Serial2/2",
        "ip address 10.0.4.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R1 <-> R6 - Area 1
        "interface Serial2/3",
        "ip address 10.0.5.1 255.255.255.252",
        "no shutdown",
        "exit",

        # OSPF
        "router ospf 1",
        "router-id 1.1.1.1",

        "network 1.1.1.1 0.0.0.0 area 0",
        "network 10.0.0.0 0.0.0.3 area 0",
        "network 10.0.2.0 0.0.0.3 area 0",

        "network 10.0.4.0 0.0.0.3 area 1",
        "network 10.0.5.0 0.0.0.3 area 1",

        "exit",
    ],


    # ========================================================
    # R2
    # Area 0 + Area 2 Stub
    # ========================================================

    "R2": [
        "hostname R2",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 2.2.2.2 255.255.255.255",
        "no shutdown",
        "exit",

        # R2 <-> R1 - Area 0
        "interface Serial2/1",
        "ip address 10.0.2.2 255.255.255.252",
        "no shutdown",
        "exit",

        # R2 <-> R4 - Area 0
        "interface Serial2/0",
        "ip address 10.0.3.2 255.255.255.252",
        "no shutdown",
        "exit",

        # R2 <-> R7 - Area 2
        "interface Serial2/2",
        "ip address 10.0.6.1 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 2.2.2.2",

        "network 2.2.2.2 0.0.0.0 area 0",
        "network 10.0.2.0 0.0.0.3 area 0",
        "network 10.0.3.0 0.0.0.3 area 0",

        "network 10.0.6.0 0.0.0.3 area 2",

        # Area 2 = Stub
        "area 2 stub",

        "exit",
    ],


    # ========================================================
    # R3
    # Area 0
    # ========================================================

    "R3": [
        "hostname R3",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 3.3.3.3 255.255.255.255",
        "no shutdown",
        "exit",

        # R3 <-> R1
        "interface Serial2/0",
        "ip address 10.0.0.2 255.255.255.252",
        "no shutdown",
        "exit",

        # R3 <-> R4
        "interface Serial2/1",
        "ip address 10.0.1.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 3.3.3.3",

        "network 3.3.3.3 0.0.0.0 area 0",
        "network 10.0.0.0 0.0.0.3 area 0",
        "network 10.0.1.0 0.0.0.3 area 0",

        "exit",
    ],


    # ========================================================
    # R4
    # Area 0 + Area 3 NSSA
    # ========================================================

    "R4": [
        "hostname R4",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 4.4.4.4 255.255.255.255",
        "no shutdown",
        "exit",

        # R4 <-> R3 - Area 0
        "interface Serial2/0",
        "ip address 10.0.1.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R4 <-> R2 - Area 0
        "interface Serial2/1",
        "ip address 10.0.3.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R4 <-> R8 - Area 3
        "interface Serial2/2",
        "ip address 10.0.7.1 255.255.255.252",
        "no shutdown",
        "exit",

        # R4 <-> R9 - Area 3
        "interface Serial2/3",
        "ip address 10.0.8.1 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 4.4.4.4",

        "network 4.4.4.4 0.0.0.0 area 0",

        "network 10.0.1.0 0.0.0.3 area 0",
        "network 10.0.3.0 0.0.0.3 area 0",

        "network 10.0.7.0 0.0.0.3 area 3",
        "network 10.0.8.0 0.0.0.3 area 3",

        # Area 3 = NSSA
        "area 3 nssa",

        "exit",
    ],


    # ========================================================
    # R5
    # Area 1
    # ========================================================

    "R5": [
        "hostname R5",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 5.5.5.5 255.255.255.255",
        "no shutdown",
        "exit",

        # R5 <-> R1
        "interface Serial2/0",
        "ip address 10.0.4.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 5.5.5.5",

        "network 5.5.5.5 0.0.0.0 area 1",
        "network 10.0.4.0 0.0.0.3 area 1",

        "exit",
    ],


    # ========================================================
    # R6
    # Area 1
    # ========================================================

    "R6": [
        "hostname R6",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 6.6.6.6 255.255.255.255",
        "no shutdown",
        "exit",

        # R6 <-> R1
        "interface Serial2/0",
        "ip address 10.0.5.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 6.6.6.6",

        "network 6.6.6.6 0.0.0.0 area 1",
        "network 10.0.5.0 0.0.0.3 area 1",

        "exit",
    ],


    # ========================================================
    # R7
    # Area 2 Stub
    # ========================================================

    "R7": [
        "hostname R7",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 7.7.7.7 255.255.255.255",
        "no shutdown",
        "exit",

        # R7 <-> R2
        "interface Serial2/0",
        "ip address 10.0.6.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 7.7.7.7",

        "network 7.7.7.7 0.0.0.0 area 2",
        "network 10.0.6.0 0.0.0.3 area 2",

        # Area 2 = Stub
        "area 2 stub",

        "exit",
    ],


    # ========================================================
    # R8
    # Area 3 NSSA
    # ========================================================

    "R8": [
        "hostname R8",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 8.8.8.8 255.255.255.255",
        "no shutdown",
        "exit",

        # R8 <-> R4
        "interface Serial2/0",
        "ip address 10.0.7.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 8.8.8.8",

        "network 8.8.8.8 0.0.0.0 area 3",
        "network 10.0.7.0 0.0.0.3 area 3",

        # Area 3 = NSSA
        "area 3 nssa",

        "exit",
    ],


    # ========================================================
    # R9
    # Area 3 NSSA
    # ========================================================

    "R9": [
        "hostname R9",
        "no ip domain lookup",

        "interface Loopback0",
        "ip address 9.9.9.9 255.255.255.255",
        "no shutdown",
        "exit",

        # R9 <-> R4
        "interface Serial2/0",
        "ip address 10.0.8.2 255.255.255.252",
        "no shutdown",
        "exit",

        "router ospf 1",
        "router-id 9.9.9.9",

        "network 9.9.9.9 0.0.0.0 area 3",
        "network 10.0.8.0 0.0.0.3 area 3",

        # Area 3 = NSSA
        "area 3 nssa",

        "exit",
    ],
}


# ============================================================
# Connexion + déploiement
# ============================================================

def configure_router(name, device):
    print(f"\n{'=' * 60}")
    print(f"Connexion à {name} - {device['host']}:{device['port']}")
    print(f"{'=' * 60}")

    router = {
        "device_type": "cisco_ios_telnet",
        "host": device["host"],
        "port": device["port"],
        "username": USERNAME,
        "password": PASSWORD,
        "secret": PASSWORD,
        "fast_cli": False,
    }

    try:
        connection = ConnectHandler(**router)

        print(f"[+] Connecté à {name}")

        connection.enable()

        print(f"[+] Déploiement de la configuration sur {name}...")

        output = connection.send_config_set(
            CONFIGS[name],
            cmd_verify=False
        )

        print(output)

        # Sauvegarde
        connection.save_config()

        print(f"[+] Configuration sauvegardée sur {name}")

        # Vérifications
        print(f"\n--- {name} : OSPF ---")
        print(connection.send_command("show ip ospf", read_timeout=30))

        print(f"\n--- {name} : voisins OSPF ---")
        print(connection.send_command("show ip ospf neighbor", read_timeout=30))

        print(f"\n--- {name} : routes OSPF ---")
        print(connection.send_command("show ip route ospf", read_timeout=30))

        connection.disconnect()

        print(f"[+] {name} terminé.")

    except NetmikoTimeoutException:
        print(f"[!] Timeout lors de la connexion à {name}")

    except NetmikoAuthenticationException:
        print(f"[!] Échec d'authentification sur {name}")

    except Exception as error:
        print(f"[!] Erreur sur {name}: {error}")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    for router_name, router_info in DEVICES.items():
        configure_router(router_name, router_info)

    print("\n" + "=" * 60)
    print("Déploiement OSPF Multi-Area terminé.")
    print("=" * 60)