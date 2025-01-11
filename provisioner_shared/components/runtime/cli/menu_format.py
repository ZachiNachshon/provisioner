import click

DEFAULT_CONTEXT_SETTINGS = {"max_content_width": 200}


def normalize_cli_item(item: str) -> str:
    return item.replace("-", "_")


class GroupedOption(click.Option):
    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group


class CustomCommand(click.Command):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("context_settings", DEFAULT_CONTEXT_SETTINGS)
        super().__init__(*args, **kwargs)

    def get_help_option(self, ctx):
        """Add `-h` as an alias for `--help`."""
        help_option = super().get_help_option(ctx)
        if help_option is None:
            return None
        # return click.Option(
        return GroupedOption(
            ["--help", "-h"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help="Show this message and exit.",
            callback=help_option.callback,
            group="Modifiers",
        )

    def format_help(self, ctx, formatter):
        formatter.write_paragraph()

        # Write USAGE
        formatter.write_text(click.style("USAGE", fg="cyan"))
        formatter.write_text(f"  {ctx.command_path} [OPTIONS] [ARGS]...")
        formatter.write_paragraph()

        # Write OPTIONS header
        formatter.write_text(click.style("OPTIONS", fg="cyan"))

        # Collect options
        opts = []
        modifiers = []
        max_option_length = 0
        for param in self.get_params(ctx):
            # Separate grouped options
            group_name = getattr(param, "group", "General")
            option_str = ", ".join(param.opts)
            if param.type and param.type.name != "boolean":
                option_str += f" {param.type.name.upper()}"
            if param.metavar:
                option_str += f" {param.metavar}"

            max_option_length = max(max_option_length, len(option_str))
            if group_name == "Modifiers":
                str_value = "" if isinstance(param, click.Argument) else param.help or ""
                modifiers.append((option_str, str_value))
            else:
                str_value = "" if isinstance(param, click.Argument) else param.help or ""
                opts.append((option_str, str_value))

        # Format OPTIONS (non-grouped options or "General" group)
        if opts:
            for option, help_text in opts:
                formatter.write_text(f"  {option.ljust(max_option_length)}  {help_text}")

        # Add MODIFIERS section if applicable
        if modifiers:
            formatter.write_paragraph()
            formatter.write_text(click.style("MODIFIERS", fg="cyan"))
            for option, help_text in modifiers:
                formatter.write_text(f"  {option.ljust(max_option_length)}  {help_text}")

        formatter.write_paragraph()
        formatter.write_text(f'Use "{ctx.command_path} [command] --help" for more information about a command.')


class CustomGroup(click.Group):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("context_settings", DEFAULT_CONTEXT_SETTINGS)
        super().__init__(*args, **kwargs)

    def command(self, *args, **kwargs):
        kwargs.setdefault("cls", CustomCommand)
        return super().command(*args, **kwargs)

    def get_help_option(self, ctx):
        """Add `-h` as an alias for `--help`."""
        help_option = super().get_help_option(ctx)
        if help_option is None:
            return None
        # return click.Option(
        return GroupedOption(
            ["--help", "-h"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help="Show this message and exit.",
            callback=help_option.callback,
            group="Modifiers",
        )

    def format_help(self, ctx, formatter):
        # Add empty line at the top
        formatter.write_paragraph()

        # Write title
        formatter.write_text("")
        formatter.write_text(
            "Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)"
        )
        formatter.write_paragraph()

        # Write usage without colon
        formatter.write_text(click.style("USAGE", fg="cyan"))
        formatter.write_text(f"  {ctx.command_path} [OPTIONS] COMMAND [ARGS]...")
        formatter.write_paragraph()

        # Write available commands
        formatter.write_text(click.style("AVAILABLE COMMANDS", fg="cyan"))
        commands = []
        for cmd in self.list_commands(ctx):
            command = self.get_command(ctx, cmd)
            if command is None:
                continue
            cmd_name = click.style(cmd, fg="green" if cmd not in ["plugins", "config"] else "yellow")
            commands.append((cmd_name, command.get_short_help_str()))

        if commands:
            formatter.write_dl(commands)

        all_options = []
        grouped_options = {}

        # Collect options
        opts = []
        modifiers = []
        max_option_length = 0
        for param in self.get_params(ctx):
            # Separate grouped options
            group_name = getattr(param, "group", "General")
            # Used for later formatting of group vs. non-grouped options
            grouped_options.setdefault(group_name, []).append(param)
            option_str = ", ".join(param.opts)
            if isinstance(param.type, click.Choice):
                option_str += f" [{('|'.join(param.type.choices))}]"
            elif param.type is not None and param.type.name != "boolean":
                option_str += f" {param.type.name.upper()}"
            if param.metavar:
                option_str += f" {param.metavar}"
            all_options.append(option_str)

            if group_name == "Modifiers":
                modifiers.append((option_str, param.help or ""))
            else:
                opts.append((option_str, param.help or ""))

            # Calculate the maximum option length for alignment
            max_option_length = max(len(opt) for opt in all_options)

        # Check if there are multiple groups, if so we will group options
        is_grouped = grouped_options.keys() != {"Modifiers"}

        # Skip the OPTIONS section if there are no options
        if len(opts) > 0:
            # Write OPTIONS header
            formatter.write_paragraph()
            formatter.write_text(click.style("OPTIONS", fg="cyan"))

        # === Grouped Options ===
        if is_grouped:
            # We don't need the modifiers, we'll have those in a separate section
            grouped_options.pop("Modifiers", None)

            # Format grouped options with proper alignment
            for group_name, params in grouped_options.items():
                with formatter.section(group_name):
                    for param in params:
                        help_record = param.get_help_record(ctx)
                        if help_record:
                            option_str, help_text = help_record
                            formatter.write_text(f"{option_str.ljust(max_option_length)}  {help_text}")
        # === Ungrouped Options ===
        else:
            # Format OPTIONS (non-grouped options or "General" group)
            if opts:
                for option, help_text in opts:
                    formatter.write_text(f"{option.ljust(max_option_length)}  {help_text}")

        # Add MODIFIERS section if applicable
        if modifiers:
            formatter.write_paragraph()
            formatter.write_text(click.style("MODIFIERS", fg="cyan"))
            for option, help_text in modifiers:
                formatter.write_text(f"  {option.ljust(max_option_length)}  {help_text}")

        formatter.write_paragraph()

        # Add help instruction
        formatter.write_text(f'Use "{ctx.command_path} [command] --help" for more information about a command.')
