from configparser import ConfigParser


def lead_config(filename, section):
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        #     print("inner section reached")
        # print("last return")
    else:
        raise Exception(f"Section {section} not found in the {filename} file")
    return config


lead_config("database.ini", "postgresql")
