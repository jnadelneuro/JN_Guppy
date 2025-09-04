# just a script to delete all existing output folders :)
# ChatGPT wrote this for me which is based af
import os
import shutil

# set the base directory
base_dir = input('Enter the base directory path (where your synapses folders are): ')

# specify the subfolder suffix
subfolder_suffix = 'output'

# loop through the folders
for folder_name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder_name)

    # loop through the subfolders
    for subfolder_name in os.listdir(folder_path):
        # check if the subfolder ends with the specified suffix
        if subfolder_name.__contains__(subfolder_suffix):
            subfolder_path = os.path.join(folder_path, subfolder_name)
            
            # delete the subfolder
            shutil.rmtree(subfolder_path)
