import ipywidgets as widgets
import json
import os
import configparser
import pandas as pd
from functools import partial
from IPython.display import display
from pyspark.sql import SparkSession

class AnnotationWidget:
  """
    Defines an annotation widget for basic document level annotation.
    This widget allows users to annotate documents with predefined labels,
    save their annotations, and navigate through documents.
  """
  def __init__(self,config_file_path):
    """
      Initialize the annotator widget.
      Loads configuration, document data, and sets up paths and labels.
    """

    # Check for a config file in the current directory
    if not os.path.exists(config_file_path):
      raise FileNotFoundError(f'{config_file_path} not found.')

    # Read configuration from the config file
    config = configparser.ConfigParser()
    config.read(config_file_path)

    # Project name from config
    self.project_name = config['project']['ProjectName']

    # Path to the CSV file containing documents
    if config['io']['DocumentsFilePath'] == '':
      # If DocumentsFilePath is empty then pull from SQL table
      self.documents_path = None
      self.documents_table = config['io']['DocumentsTable']
      self.document_id_column = config['io']['DocumentIDColumn']
      self.document_text_column = config['io']['DocumentTextColumn']
    else:
      # Else pull load from the document csv
      self.documents_path = config['io']['DocumentsFilePath']

    # Directory where annotation outputs will be saved
    self.outputs_dir = config['io']['OutputDirPath']
    # List of label names (e.g., categories)
    self.label_names = [ln for ln in config['document.labels']]
    # Dictionary mapping label names to their possible values
    self.document_labels = {ln:[v for v in config['document.labels'][ln].split('|')] for ln in config['document.labels']}

    # Check if the output directory exists
    if not os.path.exists(self.outputs_dir):
      raise FileNotFoundError(f'No file directory found at {self.outputs_dir}')

    # Load documents and annotators from the CSV file
    self.assignments = pd.read_csv(config['io']['AssignmentsFilePath'],dtype=str)
    self.assignments = self.assignments.sort_values(['annotator','document_id'])
    self.annotators = sorted(list(self.assignments.annotator.unique()))
    self.load_documents()

  def load_documents(self):
    """
      Loads the documents CSV file into a pandas DataFrame.
      Extracts the list of annotators from the DataFrame.
    """
    if self.documents_path is None:
      qry = f"select {self.document_id_column} as document_id, {self.document_text_column} as document from {self.documents_table};"
      spark = SparkSession.builder.appName(f"Annotation tool: {self.project_name}").getOrCreate()
      self.documents = spark.sql(qry).toPandas().astype(str)
    else:
      # Check if the documents file exists
      if not os.path.exists(self.documents_path):
        raise FileNotFoundError(f'{self.documents_path} not found.')
      self.documents = pd.read_csv(self.documents_path,dtype=str)

  def load_output_file(self):
    """
      Loads the annotation output file for the current annotator.
      If the file does not exist, initializes an empty annotation dictionary.
    """
    self.output_filename = f'{self.project_name}_AnnotationOutput_{self.cur_annotator}.json'
    self.output_path = self.outputs_dir + '/' + self.output_filename
    if not os.path.exists(self.output_path):
      # No output file found, start with empty annotations
      self.cur_annotations = {}
    else:
      # Load existing annotations from file
      with open(self.output_path,'r') as f:
        self.cur_annotations = json.load(f)

  def annotate(self):
    """
      Main annotation interface.
      Sets up widgets for annotator and document selection, annotation tabs,
      navigation buttons, and handles annotation saving and navigation.
    """
    output = widgets.Output()
    with output:
      print()

    # Initialize annotation state variables
    self.cur_annotator = None
    self.cur_annotations = {}
    self.cur_doc_id = 'None'
    self.cur_doc_idx = 0
    self.doc_id_list = ['None']
    self.cur_documents = {'None':''}

    # Create dropdown menu for annotators
    annotator_dropdown = widgets.Dropdown(
      options=['Select annotator'] + self.annotators,
      description='Annotator:',
      value='Select annotator'
    )

    # Create dropdown menu for documents
    document_dropdown = widgets.Dropdown(
        options=['None'],
        description='Document:',
        value='None'
    )

    # Handler for label toggle buttons
    def on_toggle(label_tab, button_name, change):
      # Add or remove label value from annotation based on toggle state
      if change['new'] and button_name not in self.cur_annotations[self.cur_doc_id][label_tab]:
        self.cur_annotations[self.cur_doc_id][label_tab].append(button_name)
      elif not change['new'] and button_name in self.cur_annotations[self.cur_doc_id][label_tab]:
        self.cur_annotations[self.cur_doc_id][label_tab].remove(button_name)

    # Create annotation tabs for each label name
    children = []
    for ln in self.label_names:
      # Create toggle buttons for each label value
      checkboxes = [widgets.ToggleButton(value=False, description=label) for label in self.document_labels[ln]]
      # Add the toggle handler for each button
      for cb,label in zip(checkboxes,self.document_labels[ln]):
        cb.observe(partial(on_toggle,ln,label),names='value')
      checkbox_box = widgets.HBox(checkboxes)
      children.append(checkbox_box)
    
    tab = widgets.Tab(children=children)
    for i,ln in enumerate(self.label_names):
      tab.set_title(i,ln)

    # Text area to display the document content
    doc_text = widgets.Textarea(
      placeholder='',
      disabled=False,
      layout=widgets.Layout(width='99%', height='300px')
    )

    # Load annotation values for the current document
    def load_annotations():
      for i,ln in enumerate(self.label_names):
        for j,lv in enumerate(self.document_labels[ln]):
          if self.cur_doc_id in self.cur_annotations:
            tab.children[i].children[j].value = lv in self.cur_annotations[self.cur_doc_id][ln]
          else:
            tab.children[i].children[j].value = False

    # Update the interface for a new document
    def update_doc(new_doc_id):
      with output:
        write_annotations()
        self.cur_doc_id = new_doc_id
        self.cur_doc_idx = self.doc_id_list.index(self.cur_doc_id)
        if self.cur_doc_id not in self.cur_annotations:
          self.cur_annotations[self.cur_doc_id] = {ln:[] for ln in self.label_names}
        load_annotations()
        doc_text.value = self.cur_documents[self.cur_doc_id]

        output.clear_output()
        print(f"Moved to doc {self.cur_doc_id}")

    # Handler for document dropdown change
    def on_document_dropdown_change(change):
      if change['type'] == 'change' and change['name'] == 'value' and change['new'] != 'Select document':
        update_doc(change['new'])

    document_dropdown.observe(on_document_dropdown_change, names='value')

    # Handler for annotator dropdown change
    def on_annotator_dropdown_change(change):
      if change['type'] == 'change' and change['name'] == 'value' and change['new'] != 'Select annotator':
        with output:
          prev_doc_id = self.cur_doc_id
          self.cur_annotator = change['new']
          mask = self.assignments.annotator == self.cur_annotator
          cur_documents_df = self.assignments[mask][['document_id']].merge(self.documents,how='inner')
          assert cur_documents_df.shape[0] == mask.sum()
          self.cur_documents = dict(zip(cur_documents_df.document_id,cur_documents_df.document))
          self.doc_id_list = sorted(list(self.cur_documents.keys()))
    
        
          output.clear_output()
          self.load_output_file()

        self.cur_doc_id = self.doc_id_list[0]
        self.cur_doc_idx = 0
        document_dropdown.options=self.doc_id_list
        if prev_doc_id == self.cur_doc_id:
          update_doc(self.cur_doc_id)

    annotator_dropdown.observe(on_annotator_dropdown_change, names='value')

    # Create Save, Previous, Next, and Next Unlabeled buttons for navigation
    save_button = widgets.Button(description='Save', button_style='success')
    prev_button = widgets.Button(description='Previous', button_style='warning')
    next_button = widgets.Button(description='Next', button_style='info')
    next_unlabeled_button = widgets.Button(description='Next unlabeled', button_style='info')

    # Write current annotations to the output file
    def write_annotations():
      with open(self.output_path,'w') as f:
        json.dump(self.cur_annotations,f)

    # Handler for Save button click
    def on_save_clicked(b):
      write_annotations()
      with output:
        output.clear_output()
        print("Annotations saved")

    # Handler for Next button click
    def on_next_clicked(b):
      if self.cur_doc_idx < len(self.doc_id_list) - 1:
        document_dropdown.value = self.doc_id_list[self.cur_doc_idx+1]
      else:
          with output:
            output.clear_output()
            print("No more documents")

    # Handler for Previous button click
    def on_prev_clicked(b):
      if self.cur_doc_idx > 0:
        document_dropdown.value = self.doc_id_list[self.cur_doc_idx-1]
      else:
          with output:
              output.clear_output()
              print("At first document")

    # Handler for Next Unlabeled button click
    def on_next_unlabeled_clicked(b):
      found_unlabeled = False
      for i in range(self.cur_doc_idx+1,len(self.doc_id_list)):
        if not self.doc_id_list[i] in self.cur_annotations:
          document_dropdown.value = self.doc_id_list[i]
          found_unlabeled = True
          break
      if not found_unlabeled:
        with output:
          output.clear_output()
          print("No unlabeled documents")

    # Attach button click handlers to their respective functions
    save_button.on_click(on_save_clicked)
    prev_button.on_click(on_prev_clicked)
    next_button.on_click(on_next_clicked)
    next_unlabeled_button.on_click(on_next_unlabeled_clicked)

    # Layout for navigation controls
    navigation_box = widgets.HBox([
      annotator_dropdown,
      document_dropdown,
      save_button, 
      prev_button, 
      next_button,
      next_unlabeled_button
    ])

    # Main widget layout: navigation, annotation tabs, document text, and output
    widget_box = widgets.VBox([
      navigation_box,
      tab,
      doc_text,
      output
    ])

    # Display the annotation widget in the notebook
    display(widget_box)

def main():
  # Instantiate the annotation widget
  annotation_widget = AnnotationWidget()

if __name__ == '__main__':
  # Run the main function if this script is executed directly
  main()