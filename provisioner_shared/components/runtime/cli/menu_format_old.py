import click

DEFAULT_CONTEXT_SETTINGS = {"max_content_width": 200}

class GroupedOption(click.Option):
    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group

class CustomCommand(click.Command):
    def __init__(self, *args, **kwargs):
        # Set default context settings with max_content_width=200
        kwargs.setdefault("context_settings", DEFAULT_CONTEXT_SETTINGS)
        super().__init__(*args, **kwargs)
 
    def get_help_option(self, ctx):
        """Add `-h` as an alias for `--help`."""
        help_option = super().get_help_option(ctx)
        if help_option is None:
            return None
        return click.Option(
            ["-h", "--help"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help="Show this message and exit.",
            callback=help_option.callback,
        )
    
    def format_help(self, ctx, formatter):
        """Override help formatting for individual commands."""
        # Add empty line at the top
        formatter.write_paragraph()

        # Write USAGE header in uppercase and cyan
        formatter.write_text(click.style("USAGE", fg="cyan"))
        formatter.write_text(f"  {ctx.command_path} [OPTIONS] [ARGS]...")
        formatter.write_paragraph()

        # Write OPTIONS header in uppercase and cyan
        formatter.write_text(click.style("OPTIONS", fg="cyan"))
        
        opts = []
        max_option_length = 0
        for param in ctx.command.params:
            # Skip Arguments when formatting OPTIONS
            if isinstance(param, click.Argument):
                continue

            option_str = ', '.join(param.opts)
            if param.type is not None and param.type.name != "boolean":
                option_str += f" {param.type.name.upper()}"
            if param.metavar:
                option_str += f" {param.metavar}"
            max_option_length = max(max_option_length, len(option_str))
            opts.append((option_str, param.help or ''))
        
        # Add the help option manually if it's missing
        if not any("--help" in param.opts for param in ctx.command.params):
            opts.append(("--help, -h", "Show this message and exit"))

        if opts:
            for option, help_text in opts:
                formatter.write_text(f"  {option.ljust(max_option_length)}  {help_text}")

        # Optionally format positional arguments
        args = [param for param in ctx.command.params if isinstance(param, click.Argument)]
        if not args:
            # Add help instruction at the bottom
            formatter.write_paragraph()
            formatter.write_text(f'Use "{ctx.command_path} --help" for more information about this command.')


class CustomGroup(click.Group):
    def __init__(self, *args, **kwargs):
        # Set default context settings with max_content_width=200
        kwargs.setdefault("context_settings", DEFAULT_CONTEXT_SETTINGS)
        super().__init__(*args, **kwargs)

    def get_help_option(self, ctx):
        """Add `-h` as an alias for `--help`."""
        help_option = super().get_help_option(ctx)
        if help_option is None:
            return None
        return click.Option(
            ["-h", "--help"],
            is_flag=True,
            expose_value=False,
            is_eager=True,
            help="Show this message and exit.",
            callback=help_option.callback,
        )

    def command(self, *args, **kwargs):
        """Override to use CustomCommand."""
        kwargs.setdefault("cls", CustomCommand)
        return super().command(*args, **kwargs)
        
    def format_help(self, ctx, formatter):
        # Add empty line at the top
        formatter.write_paragraph()
        
        # Write title
        formatter.write_text("")
        formatter.write_text("Provision Everything Anywhere (install plugins from https://zachinachshon.com/provisioner)")
        formatter.write_paragraph()

        # Write usage without colon
        formatter.write_text(click.style("USAGE", fg="cyan"))
        formatter.write_text(f"  {ctx.command_path} [OPTIONS] COMMAND [ARGS]...")
        formatter.write_paragraph()

        # Write commands without colon
        formatter.write_text(click.style("AVAILABLE COMMANDS", fg="cyan"))
        commands = []
        for cmd in self.list_commands(ctx):
            command = self.get_command(ctx, cmd)
            if command is None:
                continue
            if cmd == "plugins" or cmd == "config":
                cmd_name = click.style(cmd, fg="yellow")
            else:
                cmd_name = click.style(cmd, fg="green")
            commands.append((cmd_name, command.get_short_help_str()))
        
        if commands:
            formatter.write_dl(commands)
        formatter.write_paragraph()

         # Write options without colon
        formatter.write_text(click.style("OPTIONS", fg="cyan"))

        # 
        # === Grouped Options ===
        # 
        is_grouped = False
        grouped_options = {}

        # Categorize options by group
        for param in self.get_params(ctx):
            group_name = getattr(param, 'group', 'General')
            grouped_options.setdefault(group_name, []).append(param)
        
        # Check if there are multiple groups
        is_grouped = grouped_options.keys() != {"Modifiers"}

        if is_grouped:
            # # Format grouped options
            # for group_name, params in grouped_options.items():
            #     with formatter.section(group_name):
            #         for param in params:
            #             help_record = param.get_help_record(ctx)
            #             if help_record:
            #                 formatter.write_dl([help_record])
            
            # # Gather all options (grouped and ungrouped) to calculate max length
            # all_options = []
            # grouped_options = {}

            # for param in ctx.command.params:
            #     group_name = getattr(param, 'group', 'Other')
            #     grouped_options.setdefault(group_name, []).append(param)
            #     option_str = ', '.join(param.opts)
            #     if param.type is not None and param.type.name != "boolean":
            #         option_str += f" {param.type.name.upper()}"
            #     if param.metavar:
            #         option_str += f" {param.metavar}"
            #     all_options.append(option_str)

            # # Calculate the maximum option length for alignment
            # max_option_length = max(len(opt) for opt in all_options)

            # # Format grouped options with proper alignment
            # for group_name, params in grouped_options.items():
            #     with formatter.section(group_name):
            #         for param in params:
            #             help_record = param.get_help_record(ctx)
            #             if help_record:
            #                 option_str, help_text = help_record
            #                 formatter.write_text(f"  {option_str.ljust(max_option_length)}  {help_text}")

            # Gather all options (grouped and ungrouped) to calculate max length
            all_options = []
            grouped_options = {}

            for param in ctx.command.params:
                group_name = getattr(param, 'group', 'Other Options')
                grouped_options.setdefault(group_name, []).append(param)
                
                # Build the option string with choices if applicable
                option_str = ', '.join(param.opts)
                if isinstance(param.type, click.Choice):
                    option_str += f" [{('|'.join(param.type.choices))}]"
                elif param.type is not None and param.type.name != "boolean":
                    option_str += f" {param.type.name.upper()}"
                if param.metavar:
                    option_str += f" {param.metavar}"
                all_options.append(option_str)

            # Calculate the maximum option length for alignment
            max_option_length = max(len(opt) for opt in all_options)

            # Format grouped options with proper alignment
            for group_name, params in grouped_options.items():
                with formatter.section(group_name):
                    for param in params:
                        help_record = param.get_help_record(ctx)
                        if help_record:
                            option_str, help_text = help_record
                            formatter.write_text(f"  {option_str.ljust(max_option_length)}  {help_text}")


        else:
            # 
            # === Ungrouped Options ===
            # 
            # Format options properly with alignment
            opts = []
            max_option_length = 0
            for param in ctx.command.params:
                option_str = ', '.join(param.opts)
                if param.type is not None and param.type.name != "boolean":
                    option_str += f" {param.type.name.upper()}"
                if param.metavar:
                    option_str += f" {param.metavar}"
                    
                max_option_length = max(max_option_length, len(option_str))
                opts.append((option_str, param.help or ''))
        
            # Add the help option manually if it's missing
            if not any("--help" in param.opts for param in ctx.command.params):
                opts.append(("--help, -h", "Show this message and exit"))

            if opts:
                for option, help_text in opts:
                    formatter.write_text(f"  {option.ljust(max_option_length)}  {help_text}")

        formatter.write_paragraph()

        # Add help instruction at the bottom
        formatter.write_text(f'Use "{ctx.command_path} [command] --help" for more information about a command.')
