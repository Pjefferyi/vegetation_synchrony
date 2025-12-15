# Background 

This repository contains the scripts that I used to extract data from the MODIS/Terra+Aqua Land Cover Dynamics Yearly L3 Global 500m SIN Grid V061 dataset.

I used the Google Earth Engine library in Python to access this dataset on the Google Earth Engine catalog ("MODIS/061/MCD12Q2"). 

In order to use Python and the gee library in the Rstudio IDE, you can follow the instructions here: https://philippgaertner.github.io/2020/10/use-gee-python-api-in-rstudio/

These instructions suggest writing Python code in a R markdown file, but you can also create and edit Python scripts directly in Rstudio. You can create such a file by selecting: "File" > "New File" > 
"Python Script"

# Workflow to extract the phenology Data

After setting up a python environment that contains the packages necessary to run the python script (ee, pandas, and datetime), tje steps I use to extract the data are as follows: 

1. Make sure that you are  in the cConda Environment that contains the package I need - *Python_set_up.R*
   
2. Run the script to extract the vegetation data -  *Phenology_data_extraction.py*

3. The python script will save the extracted data in a folder on your Google Drive account called "GEE_imports". Once you've dowloaded this file, you can merge it with the "maco_data_analysis_10_2025.csv" file and then inspect it in R. An example is shown in the script - *phen_data_processing.R*
