"""
Gmail Creator - CLI Interface
Main entry point. Run with: python main.py
"""
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

from gmail_create import create_one, create_batch
from config import get_account_count, load_accounts

console = Console()


def show_banner():
    console.print("""
[bold cyan]
 ╔═══════════════════════════════════════╗
 ║     📧 Gmail Creator (Termux) 📧     ║
 ║     Selenium + Stealth Edition        ║
 ╚═══════════════════════════════════════╝
[/bold cyan]""")


def show_menu():
    console.print("\n[bold]Menu:[/bold]")
    console.print("  [green]1[/green] - Create 1 account")
    console.print("  [green]2[/green] - Create multiple accounts")
    console.print("  [green]3[/green] - List saved accounts")
    console.print("  [green]4[/green] - Show account count")
    console.print("  [red]0[/red] - Exit\n")


def list_accounts():
    accounts = load_accounts()
    if not accounts:
        console.print("[yellow]No saved accounts.[/yellow]")
        return
    table = Table(title="📧 Saved Accounts")
    table.add_column("#", style="dim")
    table.add_column("Email", style="cyan")
    table.add_column("Password", style="green")
    table.add_column("Profile", style="magenta")
    table.add_column("Created", style="dim")
    for i, acc in enumerate(accounts, 1):
        table.add_row(str(i), acc.get("email", ""), acc.get("password", ""),
                      acc.get("profile", ""), acc.get("created_at", "")[:10])
    console.print(table)


def run_create_one(proxy=None, sms_provider=None):
    console.print("\n[bold cyan]Creating single account...[/bold cyan]\n")
    result = create_one(proxy=proxy, sms_provider=sms_provider)
    if result["success"]:
        console.print(Panel(
            f"[bold green]✅ Account Created![/bold green]\n\n"
            f"📧 Email: [cyan]{result['email']}[/cyan]\n"
            f"🔐 Password: [green]{result['password']}[/green]\n"
            f"👤 Name: {result.get('name', '')}",
            title="Success", border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ Failed: {result.get('error', 'Unknown')}[/bold red]",
            title="Error", border_style="red",
        ))


def run_create_batch(proxy=None, sms_provider=None):
    count = IntPrompt.ask("How many accounts?", default=1)
    if count < 1:
        return
    console.print(f"\n[bold cyan]Creating {count} accounts...[/bold cyan]\n")
    results = create_batch(count, proxy=proxy, sms_provider=sms_provider)
    success = sum(1 for r in results if r["success"])
    console.print(Panel(
        f"✅ Success: [green]{success}[/green]\n"
        f"❌ Failed: [red]{len(results) - success}[/red]\n"
        f"📊 Total saved: {get_account_count()}",
        title="Summary", border_style="cyan",
    ))


def main():
    show_banner()

    parser = argparse.ArgumentParser(description="Gmail Creator for Termux")
    parser.add_argument("-n", "--count", type=int, help="Number of accounts to create")
    parser.add_argument("--proxy", type=str, help="Proxy URL")
    parser.add_argument("--sms", type=str, choices=["sms_activate", "five_sim", "manual"])
    parser.add_argument("--test", action="store_true", help="Create 1 account")
    parser.add_argument("--list", action="store_true", help="List saved accounts")
    args = parser.parse_args()

    if args.count:
        run_create_batch(proxy=args.proxy, sms_provider=args.sms)
        return
    if args.test:
        run_create_one(proxy=args.proxy, sms_provider=args.sms)
        return
    if args.list:
        list_accounts()
        return

    while True:
        show_menu()
        choice = Prompt.ask("Select", default="0")
        if choice == "1":
            run_create_one()
        elif choice == "2":
            run_create_batch()
        elif choice == "3":
            list_accounts()
        elif choice == "4":
            console.print(f"\n📊 Total: [cyan]{get_account_count()}[/cyan]\n")
        elif choice == "0":
            console.print("[dim]Goodbye! 👋[/dim]")
            break


if __name__ == "__main__":
    main()
