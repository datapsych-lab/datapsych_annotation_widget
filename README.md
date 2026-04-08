# Text Annotation Widget for the DataPsych Lab

This repository defines a simple annotation tool that runs as a Jupyter notebook. The tool allows for document-level labeling (with plans to add span-level annotation) according to a label schema defined by the user in a configuration file. This configuration file, as well as files giving the annotation assignments and documents can be placed in a shared location that annotators can access. Annotators can then simply run the Jupyter notebook and begin annotating! 

## Annotation interface
The annotation interface (shown below) was designed to be simple and user friendly. A detailed guide for annotators can be found in annotators_guide.pdf. In short, once the Jupyter notebook has been run, the annotation:

1. Selects their name from the Annotator dropdown
2. Navigates to a document using either the Document dropdown or the navigation buttons
3. Saves annotations by clicking the save button or navigating to another note (annotations are automatically saved).

<img width="1032" height="693" alt="readme_screenshot" src="https://github.com/user-attachments/assets/4be3aa72-0df0-4275-bb37-4f1c98720155" />

## Inputs
In addition to the configuration file described below, the annotation tool requires two input files:

### Documents file
The documents should be stored in a CSV file with two columns: 
1. The `document_id` should contain the ID used to match documents to annotators. This is converted to a string by the annotation tool.
2. The `document` column should contain the text of the document.

#### Pulling documents from a DataBricks SQL database
To avoid storing data in flat files, when running the tool in DataBricks, documents can also be pulled from a database table. To do this, the name of the table and columns for the document text and IDs are specified in the configuration file. Note that annotators will need appropriate permissions to pull data from the specified table if using this option.

### Annotation assignments file
The annotation assignments should be stored in a CSV file with two columns. This file should contain one row for each annotator/document assignment and overlapping assignments are allowed:
1. The `annotator` column contains the annotators name or identifier. This is used to name the output files and identify annotators in the user interface.
2. The `document_id` column contains the document ID.

## Outputs
Annotations are saved to JSON files. Output file names are formatted as `<project_name>__AnnotationOutput_<annotator>.json`. These files have the following structure:

```json
{
  "<document_id_1>": {"<label_name_1>":[<list_of_selected_values>], "<label_name_2>":[<list_of_selected_values>],...},
  "<document_id_2>": {"<label_name_1>":[<list_of_selected_values>], "<label_name_2>":[<list_of_selected_values>],...},
  ...
}
```
  
## Configuration
All options, including the label schema are given in a configuration file that should be placed in the directory shared with annotators. Configuration files are in INI format. Three configuration examples are provided along with the repository and information on each of the required sections are given below:

### [project]
This section specifies the `ProjectName` parameter used for output file naming.

```ini
[project]
ProjectName = Test
```

### [io]
This section is used to specify the input files and output file directory. It should specify the following parameters:
1. `AssignmentsFilePath`: Path to the annotator assignments CSV file. Annotators must have read permissions.
2. `DocumentsFilePath`: Path to the documents CSV file. Annotators must have read permissions. If pulling from a SQL database, this should be left blank.
3. `DocumentsTable`: If pulling from a SQL database, the name of the table containing documents is given here. If pulling from a CSV file, this is ignored.
4. `DocumentIDColumn`: If pulling from a SQL database, the column containing document IDs.
5. `DocumentTextColumn`: If pulling from a SQL database, the column containg document text.
6. `OutputDirPath`: Path to the directory where output files will be stored. Annotators must have write permissions for this directory.

```ini
[io]
AssignmentsFilePath = ./data/annotator_assignments.csv
DocumentsFilePath = ./data/documents.csv
DocumentsTable = 
DocumentIDColumn = 
DocumentTextColumn = 
OutputDirPath = ./outputs/
```

### [document.labels]
This section specifies the document-level labeling schema. This section may contain any number of parameters, each corresponding to a separate label type. Each label type is displayed in a separate tab as shown in the screenshot above. A parameter corresponds to the tab name and the label values are given in a pipe delimeted list like: `LabelName = <value1>|<value2>|<value3>`. Note that the tool does not force the values to be mutualy exclusive. This allows for additionally flexibility in the labeling schema, but if mutual exclusivity is needed, then annotators should be instructed to select only on label from each tab.

```ini
[document.labels]
LabelName1 = <value1>|<value2>|<value3>
LabelName2 = <value1>|<value2>|<value3>|<value4>
```
