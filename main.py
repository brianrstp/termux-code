"""
Gmail Creator - CLI Interface
Main entry point. Run with: python main.py
"""
import asyncio
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from gmail_create import create_one, create_batch
from config import get_account_count, load_accounts

console = Console()


def show_banner():
    banner = """
[bold cyan]
 ╔═══════════════════════════════════════╗
 ║     📧 Gmail Creator (Termux) 📧     ║
 ║     Playwright + Stealth Edition      ║
 ╚═══════════════════════════════════════╝
[/bold cyan]"""
    console.print(banner)


def show_menu():
    console.print("\n[bold]Menu:[/bold]")
    console.print("  [green]1[/green] - Create 1 account")
    console.print("  [green]2[/green] - Create multiple accounts")
    console.print("  [green]3[/green] - List saved accounts")
    console.print("  [green]4[/green] - Show account count")
    console.print("  [green]5[/green] - Settings")
    console.print("  [red]0[/red] - Exit\n")


def list_accounts():
    """Display saved accounts in a table."""
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
        table.add_row(
            str(i),
            acc.get("email", ""),
            acc.get("password", ""),
            acc.get("profile", ""),
            acc.get("created_at", "")[:10],
        )

    console.print(table)


async def run_create_one(proxy: str = None, sms_provider: str = None):
    """Create a single account interactively."""
    console.print("\n[bold cyan]Creating single account...[/bold cyan]\n")

    result = await create_one(proxy=proxy, sms_provider=sms_provider)

    if result["success"]:
        console.print(Panel(
            f"[bold green]✅ Account Created Successfully![/bold green]\n\n"
            f"📧 Email: [cyan]{result['email']}[/cyan]\n"
            f"🔐 Password: [green]{result['password']}[/green]\n"
            f"👤 Name: {result.get('name', '')}",
            title="Success",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ Failed: {result.get('error', 'Unknown error')}[/bold red]",
            title="Error",
            border_style="red",
        ))


async def run_create_batch(proxy: str = None, sms_provider: str = None):
    """Create multiple accounts."""
    count = IntPrompt.ask("How many accounts to create?", default=1)
    if count < 1:
        console.print("[red]Invalid count.[/red]")
        return

    console.print(f"\n[bold cyan]Creating {count} accounts...[/bold cyan]\n")
    results = await create_batch(count, proxy=proxy, sms_provider=sms_provider)

    # Summary
    success = sum(1 for r in results if r["success"])
    failed = len(results) - success

    console.print(Panel(
        f"[bold]Batch Complete![/bold]\n\n"
        f"✅ Success: [green]{success}[/green]\n"
        f"❌ Failed: [red]{failed}[/red]\n"
        f"📊 Total accounts: {get_account_count()}",
        title="Summary",
        border_style="cyan",
    ))


async def settings_menu():
    """Show and modify settings."""
    from config import HEADLESS, SMS_PROVIDER, PROXY

    console.print(Panel(
        f"🖥️  Headless Mode: [cyan]{HEADLESS}[/cyan]\n"
        f"📱 SMS Provider: [cyan]{SMS_PROVIDER}[/cyan]\n"
        f"🌐 Proxy: [cyan]{PROXY or 'None'}[/cyan]",
        title="Current Settings",
    ))

    console.print("\n[bold]Settings:[/bold]")
    console.print("  [green]1[/green] - Toggle headless mode")
    console.print("  [green]2[/green] - Set SMS provider")
    console.print("  [green]3[/green] - Set proxy")
    console.print("  [green]0[/green] - Back\n")

    choice = Prompt.ask("Select", default="0")
    # Note: Settings changes require editing config.py
    # This is a simplified version
    if choice == "1":
        console.print("[yellow]Edit HEADLESS in config.py to change.[/yellow]")
    elif choice == "2":
        console.print("[yellow]Edit SMS_PROVIDER in config.py (sms_activate / five_sim / manual).[/yellow]")
    elif choice == "3":
        console.print("[yellow]Set PROXY environment variable or edit config.py.[/yellow]")


async def main():
    show_banner()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Gmail Creator for Termux")
    parser.add_argument("-n", "--count", type=int, help="Number of accounts to create")
    parser.add_argument("--proxy", type=str, help="Proxy URL")
    parser.add_argument("--sms", type=str, choices=["sms_activate", "five_sim", "manual"],
                        help="SMS provider")
    parser.add_argument("--test", action="store_true", help="Quick test - create 1 account")
    parser.add_argument("--list", action="store_true", help="List saved accounts")

    args = parser.parse_args()

    # CLI mode
    if args.count:
        await run_create_batch(proxy=args.proxy, sms_provider=args.sms)
        return

    if args.test:
        await run_create_one(proxy=args.proxy, sms_provider=args.sms)
        return

    if args.list:
        list_accounts()
        return

    # Interactive mode
    while True:
        show_menu()
        choice = Prompt.ask("Select", default="0")

        if choice == "1":
            await run_create_one()
        elif choice == "2":
            await run_create_batch()
        elif choice == "3":
            list_accounts()
        elif choice == "4":
            console.print(f"\n📊 Total saved accounts: [cyan]{get_account_count()}[/cyan]\n")
        elif choice == "5":
            await settings_menu()
        elif choice == "0":
            console.print("[dim]Goodbye! 👋[/dim]")
            break
        else:
            console.print("[red]Invalid option.[/red]")


if __name__ == "__main__":
    asyncio.run(main())
