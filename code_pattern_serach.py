import os
import re
import csv
import time
import json
from datetime import timedelta
import datetime
import pandas as pd
import logging
import threading

# Function to read config file
def read_config_file(json_file_path):
    """Reads the configuration from a JSON file."""
    with open(json_file_path, "r") as json_file:
        properties = json.load(json_file)
    return properties

# Function to validate config properties
def validate_config(properties):
    """Validates the configuration properties."""
    required_params = ['source_folder', 'output_folder', 'excluded_extensions', 'regexps', 'skip_folders', 'max_batches']
    for param in required_params:
        if param not in properties:
            print(f"Program stopped because required parameter '{param}' is not in the config.json \n")
            raise ValueError(f"Required parameter '{param}' is not in the config.json")

# Function to create batches
def create_batches(applications, num_batches):
    """Divides applications into batches based on the specified number of batches."""
    batch_size = len(applications) // num_batches
    remaining_apps = len(applications) % num_batches
    batches = []
    start = 0  
    for i in range(num_batches):
        batch_end = start + batch_size + (1 if i < remaining_apps else 0)
        batches.append(applications[start:batch_end])
        start = batch_end    
    return batches

def search_files_in_folder(folder, app_name, skip_folders, excluded_extensions, regexps, table_data, logger):
    """Searches for files in a given folder based on specified conditions."""
    file_count = 0
    errors = 0
    for root, dirs, files in os.walk(folder):
        # Skip folders based on specified conditions
        dirs[:] = [d for d in dirs if d not in skip_folders]
        for file_name in files:
            file_count += 1
            # if file_count % 100 == 0:
            #     print(f"Files processed: {file_count}")
            full_name = os.path.join(root, file_name)
            file_extension = os.path.splitext(full_name)[1].lower()
            if file_extension not in excluded_extensions:
                hits_per_regex = {key: 0 for key in regexps}
                has_hits = False
                has_error = False
                try:
                    with open(full_name, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        for regexp_key, regexp_patterns in regexps.items():
                            for pattern in regexp_patterns:
                                x = re.findall(pattern, content, re.IGNORECASE)
                                if len(x):
                                    hits_per_regex[regexp_key] += len(x)
                                    has_hits = True
                    if not has_hits:
                        errors = 1
                        has_error = True
                except Exception as e:
                    print(e)
                    logger.error(e)

                if has_hits or has_error:
                    table_row = [app_name, full_name, file_extension, 1 if has_error else 0] + list(hits_per_regex.values())
                    table_data.append(table_row)
    return file_count, errors

def process_application(app_names, source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger):
    """Processes each application by searching for files in its folder."""
    for app_name in app_names:
        start_time = time.time()
        table_data = []
        app_folder = os.path.join(source_folder, app_name)
        print(f"Searching in application : {app_name} ........\n")
        logger.info(f"Searching in application : {app_name} ........\n")
        try:
            file_count, errors = search_files_in_folder(app_folder, app_name, skip_folders, excluded_extensions, regexps, table_data, logger)
            output_file = f"{output_folder}\\{app_name} - DetectionResults.csv"
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(table_header)
                writer.writerows(table_data)
            table_data.clear()
            print(f"{file_count} files searched in {timedelta(seconds=time.time()-start_time)} seconds for application : {app_name}.\n")
            logger.info(f"{file_count} files searched in {timedelta(seconds=time.time()-start_time)} seconds for application : {app_name}.\n")
        except Exception as e:
            print(f"Error processing application {app_name}: {e}\n")
            logger.error(f"Error processing application {app_name}: {e}\n")
            continue
    # print(f"Search completed in {timedelta(seconds=time.time()-start_time)} for application : {app_name}.")

# Function to process batch
def process_batch(batches,  source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger):
    """Processes batches of applications concurrently using threads."""
    process_threads = []
    for app_batch in batches:
        thread = threading.Thread(target=process_application, args=(app_batch, source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger))
        thread.start()
        process_threads.append(thread)
    for thread in process_threads:
        thread.join()

def combine_csv(output_folder, logger):
    """Combines the generated CSV files into one."""
    dfs = []
    for file_name in os.listdir(output_folder):
        if file_name.endswith(".csv"):
            file_path = os.path.join(output_folder, file_name)
            df = pd.read_csv(file_path)
            dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    combined_file_path = os.path.join(output_folder, f"combined_results.csv")

    combined_df.to_csv(combined_file_path, index=False)

    print("combined_results.csv file created successfully.\n")
    logger.info("combined_results.csv file created successfully.\n")

# Main function
def main():
    try:
        current_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Read the config file
        properties = read_config_file('config.json')

        # Validate config properties
        validate_config(properties)

        source_folder = properties['source_folder']
        output_folder = properties['output_folder']
        excluded_extensions = properties['excluded_extensions']
        regexps = properties['regexps']
        skip_folders = properties['skip_folders']
        max_batches = int(properties['max_batches'])

        output_folder = output_folder +'\\'+current_datetime

        output_log_file = os.path.join(output_folder, f"code_pattern_search_logs.log")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Output Folder '{output_folder}' created successfully.\n")
        else:
            print(f"Output Folder '{output_folder}' already exists.\n")

        logger = logging.getLogger()
        handler = logging.FileHandler(output_log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        table_header = ["Application", "FileName", "Extension", "Errors"] + list(regexps.keys())
        table_data = []

        app_names = [folder for folder in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, folder))]

        batches = create_batches(app_names, max_batches)
        num_of_apps = len(app_names)
        num_of_batches = len(batches)
        print(f"{num_of_apps} Applications divided into {num_of_batches} Batches.\n")
        logger.info(f"{num_of_apps} Applications divided into {num_of_batches} Batches.\n")

        for count,app_batch in enumerate(batches, start=1):
            print(f"Batch-{count} {app_batch}\n")
            logger.info(f"Batch-{count} {app_batch}\n")

        process_batch(batches, source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger)

        combine_csv(output_folder, logger)

    except Exception as e:
        print("Error:", e, "\n")
        logger.error("Error:", e, "\n")

if __name__ == "__main__":
    main()
