def removed_flags(**payload):
    flags = payload["flag_name"]
    if len(flags) == 1:
        return f"removed the flag '{flags[0]}' from the organisation"
    elif len(flags) >= 2:
        formatted_flags = f"{str(flags[:-1])[1:-1]} and '{flags[-1]}'"
        return f"removed the flags {formatted_flags} from the organisation"
