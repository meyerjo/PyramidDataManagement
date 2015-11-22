# Fork purpose
The purpose of this branch is to enhance the web browser experience. Therefore, multiple extensions to the previous framework are made. 
Every result is wrapped within a bootstrap design with an navigation bar, which allows to leave the file preview more easily, and allows direct file access.

# How to manipulate the folder behaviour?
The user is able to add a .settings.json to every folder below the specified root_directory. These settings are propagated recursively to all the subfolders. They can be used to add a specific behaviour to certain filetypes.
Remove specific filetypes from the specific output and so on. An exemplaric .settings.json and a description can be found below

```
{

  "blacklist": ["\\.asv"],
  
  "folder_template": "<i class='fa fa-folder'></i><a tal:attributes='href item' tal:content='item'></a>",
  
  "file_template": "<i class='fa fa-file'></i><a tal:attributes='href item' tal:content='item'></a>",
  
  "specific_filetemplates": {
  
    ".png": {
    
      "group_by": ["^.{4}", "(grid|scalp)plot"],
      
      "elements_per_row": 2,
      
      "template": "<div tal:repeat='(group, rows) sorted(grouped_files.items())' metal:define-macro='filter_depth'><h1 tal:content='group'></h1><div tal:condition='python: type(rows) is dict' tal:define='grouped_files rows'><div  metal:use-macro='template.macros[\"filter_depth\"]'></div></div><div class='row' tal:condition='python: type(rows) is list' tal:repeat='files rows'><div tal:repeat='file files' class='col-sm-${columnwidth}'><div class='row-fluid'><div class='col-sm-12'>File: <span tal:content='file'></div><div class='col-sm-12'><img tal:attributes='src file' class='col-sm-12'></div></div></div></div></div>"
      
    },
    
    ".csv": {
    
      "group_by": ["^.{2}"],
      
      "elements_per_row": 2,
      
      "template": "<div tal:repeat='(group, rows) sorted(grouped_files.items())'><div class='row' tal:repeat='files rows'><div tal:repeat='file files' class='col-sm-${columnwidth}'><div class='row-fluid'><div class='col-sm-12'>File: <a tal:attributes='href file' tal:content='file'></a></div><div class='col-sm-12'><iframe tal:attributes='src file' class='col-sm-12'></iframe></div></div></div></div></div>"
      
    }
    
  }
  
}
```

## blacklist
The field blacklist, contains an array of regular expressions specifying filenames, which shouldn't be displayed in a directory listing.

## folder_template / file_template
The fields folder / file_template specify the template which should be used for regular files. **Usage of folder_template still under development.**

## specific_filetemplates
The field specific_filetemplates, contains a dictionary of behaviour rules for specific filetypes. In this example all png files are supposed to be grouped first, by the first 4 letters of their filename and then by their category as grid or scalpplot.
Furthermore it is specified that always 2 pictures should be displayed in one row. The last field is the template used to display the files.