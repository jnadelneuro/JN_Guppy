import os

# Path to the directory containing your folders
folder_path = r"C:\Users\jan7154\Documents\aCUS_analysis\all\photometry\processed"  # <-- change this to your directory

# Loop through each item in the folder
for folder in os.listdir(folder_path):
    old_folder_path = os.path.join(folder_path, folder)
    # Check if it is a directory
    if os.path.isdir(old_folder_path):
        # Process only if the folder name contains '_JN-' and starts with 'WT'
        if '_JN-' in folder and folder.startswith('WT'):
            # Split the folder name into two parts: left and right of '_JN-'
            left_part, right_part = folder.split('_JN-', 1)
            # Make sure left_part starts with 'WT'; if it doesn't already have an underscore after WT, add it
            if left_part.startswith('WT') and not left_part.startswith('WT_'):
                new_left = 'WT_' + left_part[2:]
            else:
                new_left = left_part
            # Construct the new folder name by placing JN first, then the modified left part, 
            # and finally the right part (with a hyphen separator)
            new_folder = f"JN_{new_left}-{right_part}"
            new_folder_path = os.path.join(folder_path, new_folder)
            print(f"Renaming '{folder}' to '{new_folder}'")
            os.rename(old_folder_path, new_folder_path)
