import os
from flask import current_app
from slugify import slugify
from werkzeug.utils import secure_filename
from datetime import datetime

def save_file(file_data, obj_id='0', text='new_file'):
    dt = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename_list = file_data.filename.split('.')
    extension = filename_list[-1]
    uploaded_filename = file_data.filename.replace('.' + extension, '')
    current_app.logger.debug('FILENAME: ' + uploaded_filename)
    current_app.logger.debug('EXTENSION: ' + extension)
    
    new_filename = f'{obj_id}-{text}-{dt}.{extension}'
    new_path = os.path.join(current_app.config['UPLOAD_DIR'], secure_filename(new_filename))
    file_data.save(new_path)
    return new_path

def delete_file(path):
    try: 
        os.remove(path)
    except:
        current_app.logger.info(f"File '{path}' not found.")
