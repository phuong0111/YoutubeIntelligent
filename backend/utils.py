import os

def get_filename_without_extension(file_path):
    """
    Extract the filename without extension from a file path.
    
    Parameters:
    file_path (str): Path to the file (e.g., 'downloads/abc.wav', 'C:\\files\\document.pdf')
    
    Returns:
    str: Filename without extension (e.g., 'abc', 'document')
    """
    # Get the basename (filename with extension) from the path
    basename = os.path.basename(file_path)
    
    # Split the basename into filename and extension
    filename_without_extension = os.path.splitext(basename)[0]
    
    return filename_without_extension