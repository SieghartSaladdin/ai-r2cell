from rich.text import Text


def render_menu(options: list[str], selected_index: int) -> Text:
    """
    Renders the R2CELL selection menu as a Rich Text object.
    Clean layout with a subtle cursor and muted unselected items.
    """
    menu = Text()
    menu.append("\n")
    menu.append("  R2CELL ", style="bold #7c8aff")
    menu.append("Services Gateway\n", style="#888899")
    menu.append("  ─────────────────────\n\n", style="#333344")

    for idx, opt in enumerate(options):
        if opt.startswith("──"):
            menu.append(f"  {'─' * 22}\n", style="#222233")
        elif idx == selected_index:
            menu.append("  ▸ ", style="bold #10b981")
            menu.append(f"{opt}\n", style="bold #e2e8f0")
        else:
            menu.append(f"    {opt}\n", style="#666677")

    menu.append("\n")
    menu.append("  ↑↓ navigate  ⏎ select  q quit\n", style="dim #444455")

    return menu
