
#  **Code Pattern Search Tool**

This tool searches for specific patterns in files across multiple applications, divides the workload into batches, processes them concurrently, and generates combined results in CSV format. The configuration for the tool is provided in a JSON file.


### Installation

1. Clone the repository or download the code:
   
		git clone https://github.com/yourusername/code-pattern-search-tool.git

2. Navigate to the project directory:
   
		cd code-pattern-search-tool

3. Install the required packages:
   
		pip install -r requirements.txt

### Usage
1. Place your configuration file config.json in the root directory of the project. See the Configuration section for details on the required parameters.

2. Run the tool:
   
		python search_tool.py

### Configuration
The tool requires a config.json file with the following structure:

	{
		"source_folder": "path/to/source_folder",
		"output_folder": "path/to/output_folder",
		"excluded_extensions": [".exe", ".dll"],
		"regexps": {
			"pattern1": ["regex1", "regex2"],
			"pattern2": ["regex3"]
		},
		"skip_folders": ["skip_folder1", "skip_folder2"],
		"max_batches": 4
	}

- source_folder: The folder containing application subfolders to be searched.
- output_folder: The folder where the output CSV files will be stored.
- excluded_extensions: List of file extensions to exclude from the search.
- regexps: Dictionary of pattern names and their associated regex patterns to search for.
- skip_folders: List of folder names to skip during the search.
- max_batches: The maximum number of batches to divide the applications into.

### Logging
The tool generates logs in the output_folder with a timestamped log file. The log file records details of the search process, including errors encountered.

### Functions
- read_config_file(json_file_path) :- Reads the configuration from a JSON file.

- validate_config(properties) :- Validates the configuration properties.

- create_batches(applications, num_batches) :- Divides applications into batches based on the specified number of batches.

- search_files_in_folder(folder, app_name, skip_folders, excluded_extensions, regexps, table_data, logger) :- Searches for files in a given folder based on specified conditions.

- process_application(app_names, source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger) -> Processes each application by searching for files in its folder.

- process_batch(batches, source_folder, skip_folders, excluded_extensions, regexps, output_folder, table_header, logger) -> Processes batches of applications concurrently using threads.

- combine_csv(output_folder, logger) -> Combines the generated CSV files into one.

- main() -> Main function that orchestrates the reading of the configuration, validation, batch processing, and CSV combination.
