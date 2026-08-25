#!/usr/bin/env python3

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from datetime import datetime


console = Console()


# ============================================================
# Configuration GNS3
# ============================================================

ROUTERS = {
    "R1": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5000,
    },

    "R2": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5001,
    },

    "R3": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5002,
    },

    "R4": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5003,
    },

    "R5": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5004,
    },

    "R6": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5005,
    },

    "R7": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5006,
    },

    "R8": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5007,
    },

    "R9": {
        "device_type": "cisco_ios_telnet",
        "host": "127.0.0.1",
        "port": 5008,
    },
}


# ============================================================
# Commandes de vérification
# ============================================================

COMMANDS = {
    "OSPF Neighbors": "show ip ospf neighbor",
    "OSPF Routes": "show ip route ospf",
    "OSPF Database": "show ip ospf database",
    "Interfaces": "show ip interface brief",
    "OSPF Interfaces": "show ip ospf interface brief",
    "OSPF Process": "show ip ospf",
    "Routing Protocols": "show ip protocols",
}


# ============================================================
# Répertoires de sortie
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "outputs"
REPORT_DIR = OUTPUT_DIR / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# Connexion
# ============================================================

def connect_router(name, config):

    try:

        console.print(
            f"[cyan]Connexion à {name} "
            f"(Telnet {config['host']}:{config['port']})...[/cyan]"
        )

        connection = ConnectHandler(
            **config,
            conn_timeout=10,
        )

        console.print(
            f"[green]✓ {name} connecté[/green]"
        )

        return connection

    except NetmikoAuthenticationException:

        console.print(
            f"[red]✗ Échec authentification {name}[/red]"
        )

    except NetmikoTimeoutException:

        console.print(
            f"[red]✗ Timeout {name}[/red]"
        )

    except Exception as error:

        console.print(
            f"[red]✗ Erreur {name}: {error}[/red]"
        )

    return None


# ============================================================
# Exécution des commandes
# ============================================================

def run_commands(router_name, connection):

    router_dir = OUTPUT_DIR / router_name
    router_dir.mkdir(exist_ok=True)

    results = {}

    for command_name, command in COMMANDS.items():

        console.print(
            f"  [yellow]→[/yellow] {command}"
        )

        try:

            output = connection.send_command(
                command,
                read_timeout=30,
            )

            results[command_name] = output

            filename = (
                command_name
                .lower()
                .replace(" ", "_")
                .replace("/", "_")
                + ".txt"
            )

            output_file = router_dir / filename

            output_file.write_text(
                output,
                encoding="utf-8",
            )

        except Exception as error:

            results[command_name] = (
                f"ERROR: {error}"
            )

    return results


# ============================================================
# Tableau récapitulatif
# ============================================================

def build_summary(results):

    table = Table(
        title="Vérification OSPF Multi-Area"
    )

    table.add_column(
        "Routeur",
        style="cyan"
    )

    table.add_column(
        "Commande",
        style="yellow"
    )

    table.add_column(
        "Résultat",
        style="green"
    )

    for router, commands in results.items():

        for command_name, output in commands.items():

            if output.startswith("ERROR"):

                status = "ERREUR"

            elif output.strip():

                status = "OK"

            else:

                status = "VIDE"

            table.add_row(
                router,
                command_name,
                status,
            )

    console.print(table)


# ============================================================
# Rapport texte
# ============================================================

def generate_report(results):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    report_file = (
        REPORT_DIR /
        f"ospf_verification_{timestamp}.txt"
    )

    with report_file.open(
        "w",
        encoding="utf-8"
    ) as report:

        report.write(
            "====================================================\n"
        )

        report.write(
            "       OSPF MULTI-AREA - RAPPORT NETMIKO\n"
        )

        report.write(
            "====================================================\n\n"
        )

        report.write(
            f"Date : {datetime.now()}\n\n"
        )

        for router, commands in results.items():

            report.write(
                f"\n{'=' * 60}\n"
            )

            report.write(
                f"{router}\n"
            )

            report.write(
                f"{'=' * 60}\n"
            )

            for command_name, output in commands.items():

                report.write(
                    f"\n--- {command_name} ---\n"
                )

                report.write(
                    output
                )

                report.write("\n")

    console.print(
        f"\n[green]Rapport généré :[/green] "
        f"{report_file}"
    )


# ============================================================
# Main
# ============================================================

def main():

    console.print(
        Panel(
            "[bold cyan]"
            "TP07 - OSPF MULTI-AREA\n"
            "Vérification automatisée avec Netmiko"
            "[/bold cyan]",
            title="GNS3",
        )
    )

    all_results = {}

    for router_name, router_config in ROUTERS.items():

        console.print(
            f"\n[bold blue]===== {router_name} =====[/bold blue]"
        )

        connection = connect_router(
            router_name,
            router_config,
        )

        if connection is None:

            all_results[router_name] = {
                "CONNECTION": "ERROR"
            }

            continue

        try:

            results = run_commands(
                router_name,
                connection,
            )

            all_results[router_name] = results

        finally:

            connection.disconnect()

            console.print(
                f"[green]✓ {router_name} déconnecté[/green]"
            )

    console.print()

    build_summary(
        all_results
    )

    generate_report(
        all_results
    )


if __name__ == "__main__":
    main()