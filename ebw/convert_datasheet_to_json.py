
import json

def convert_datasheet_to_json(datasheet_path, json_path):
    config_data = {}
    current_section = None

    with open(datasheet_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Simulating") or line.startswith("Grid") or line.startswith("Materials") or line.startswith("Power") or line.startswith("Peak Temp") or line.startswith("Fusion Area"):
                continue

            if line.startswith("---"):
                if "Simulation Parameters" in line:
                    current_section = "simulation_parameters"
                    config_data[current_section] = {}
                elif "Material 1" in line:
                    current_section = "material_1"
                    config_data[current_section] = {"name": "Mild Steel"}
                elif "Material 2" in line:
                    current_section = "material_2"
                    config_data[current_section] = {"name": "Stainless Steel 304"}
                else:
                    current_section = None
            elif current_section:
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Attempt to convert to float or int if possible
                    try:
                        if '.' in value:
                            config_data[current_section][key] = float(value)
                        else:
                            config_data[current_section][key] = int(value)
                    except ValueError:
                        config_data[current_section][key] = value
                except ValueError:
                    # Handle lines that don't conform to key: value, e.g., empty lines within a section
                    pass

    with open(json_path, 'w') as f:
        json.dump(config_data, f, indent=4)

if __name__ == "__main__":
    datasheet_file = "/media/dell/Hard Drive/Summer of code/MME/ERW-pipelines/welding-kar/ebw/datasheet.txt"
    json_file = "/media/dell/Hard Drive/Summer of code/MME/ERW-pipelines/welding-kar/ebw/config.json"
    convert_datasheet_to_json(datasheet_file, json_file)
    print(f"Converted {datasheet_file} to {json_file}")
