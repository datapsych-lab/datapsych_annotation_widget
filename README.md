# Text Annotation Utility for the DataPsych Lab

This repository defines a simple annotation utility that runs as a Jupyter notebook. Tool allows for document-level labeling (with plans to add span-level annotation) according to a label schema defined by the user in a configuration file. This configuration file, as well as files giving the annotation assignments and documents can be placed in a shared location that annotators can access. Annotators can then simply run the Jupyter notebook and begin annotating! 

## Annotation interface
The annotation interface (shown below) was designed to be simple an user friendly. A detailed guide for annotators can be found in annotators_guide.pdf. In short, once the Jupyter notebook has been run, the annotation:

1. Selects their name from the Annotator dropdown
2. Navigates to a document using either the Document dropdown or the navigation buttons
3. Saves annotations by clicking the save button or navigating to another note (annotations are automatically saved).

<img width="1033" height="613" alt="Screenshot 2026-04-07 at 4 48 38 PM" src="https://github.com/user-attachments/assets/ad6c43d5-a0e0-4f5d-b58b-13c1ce0dcc30" />

## Inputs
In addition to the configuration file described below, the annotation tool requires two files:

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
  
