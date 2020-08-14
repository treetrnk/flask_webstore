import re
import os
from math import floor
from flask import current_app, flash, request
from flask_login import current_user
from csv import DictReader
from datetime import datetime

def round_half_up(n, decimals=0):
        multiplier = 10 ** decimals
        if decimals == 0:
            return int(floor(n*multiplier + 0.5) / multiplier)
        return floor(n*multiplier + 0.5) / multiplier

def format_hour_length(length):
    timelist = re.split("[^\d.]+", str(length))
    #print("TIMELIST: " + str(timelist))
    if len(timelist) == 4:
        hours = (int(timelist[0]) * 24) + int(timelist[1])
        formatted = hours + float(timelist[2]) / 60 + float(timelist[3]) / 60 / 60
    else:
        formatted = int(timelist[0]) + float(timelist[1]) / 60 + float(timelist[2]) / 60 / 60 
    return round_half_up(formatted, 2)

def convert_to_dict(obj):
    if type(obj) is not dict:
        data = {'repr': repr(obj)}
        for field in obj.__table__.columns:
            data[field.key] = obj.__dict__.get(field.key)
        #for field in obj.__table__.foreign_keys:
        #    data[field.key] = repr(obj.__dict__.get(field.key))
        try:
            data["users"] = obj.users
        except:
            pass
        try:
            data["user"] = obj.user
        except:
            pass
        try:
            data["groups"] = obj.groups
        except:
            pass
        try:
            data["permissions"] = obj.permissions
        except:
            pass
        try:
            data["creator"] = obj.creator
        except:
            pass
        try:
            data["editor"] = obj.editor
        except:
            pass
        try:
            data["parent"] = obj.parent
        except:
            pass
        try:
            data["category"] = obj.category
        except:
            pass
        return data
    return obj

def create_file_if_missing(filepath):
    if not os.path.isfile(filepath):
        open(filepath, 'w')

def log_product_change(product, message):
    log_dir = current_app.config['PRODUCT_LOG_DIR']
    filename = os.path.join(log_dir, product.log_filename())
    
    create_file_if_missing(filename)

    message = datetime.now().strftime('[%Y-%m-%d %I:%M %p | INFO ') + f'| {request.referrer} | {request.method}]\r\n' + message
    
    f = open(filename, 'a')
    f.write(message)
    f.close()

def log_new(obj, message=''):
    data = convert_to_dict(obj)
    output = f'{current_user.username} {message}:\n'
    for key, value in data.items():
        output += f"    {key}: {value}\n"
    #print(output)
    current_app.logger.info(output)
    return True

def log_change(original, updated=None, message='changed something'):
    original_data = convert_to_dict(original)
    if updated:
        output = f'{current_user.username} {message}:\n'
        output += f"Changed object: {original['repr']}\n"
        updated_data = convert_to_dict(updated)
        for key, value in original_data.items():
            if key != 'repr':
                if (key not in updated_data or value != updated_data[key]) and key != 'updated':
                    output += f'    {key}: {value}  ===CHANGED TO===>  {updated_data[key]}\n'
        #print(output)
        current_app.logger.info(output)
        if updated.__class__.__name__ == 'Product':
            log_product_change(updated, output)
        return True
    return original_data
    
def log_form(form_obj):
    for field in form_obj:
        current_app.logger.debug(f'{field.name}: {field.data}')
        for error in field.errors:
            current_app.logger.warning(f'{field.name}: {error}')

def flash_form_errors(form_obj):
    if form_obj.errors:
        msg = """A problem occured with the following fields. 
                Please correct them and try again. 
                <ul>"""
        for error in form_obj.errors:
            msg += f"<li>{error}</li>"
    
        flash(msg, 'danger')

def list_join(seq):
    ''' Join a sequence of lists into a single list, much like str.join
    will join a sequence of strings into a single string.
    '''
    return [x for sub in seq for x in sub]

def encode128(s):
    ''' Code 128 conversion for a font as described at
    https://en.wikipedia.org/wiki/Code_128 and downloaded
    from http://www.barcodelink.net/barcode-font.php
    Only encodes ASCII characters, does not take advantage of
    FNC4 for bytes with the upper bit set. Control characters
    are not optimized and expand to 2 characters each.
    Coded for https://stackoverflow.com/q/52710760/5987

    Pulled from: 
    https://stackoverflow.com/questions/52710760/python-code128-encoder-for-code128-barcode-font
    '''
    code128B_mapping = dict((chr(c), [98, c+64] if c < 32 else [c-32]) for c in range(128))
    code128C_mapping = dict([(u'%02d' % i, [i]) for i in range(100)] + [(u'%d' % i, [100, 16+i]) for i in range(10)])
    code128_chars = u''.join(chr(c) for c in [212] + list(range(33,126+1)) + list(range(200,211+1)))

    if s.isdigit() and len(s) >= 2:
        # use Code 128C, pairs of digits
        codes = [105] + list_join(code128C_mapping[s[i:i+2]] for i in range(0, len(s), 2))
    else:
        # use Code 128B and shift for Code 128A
        codes = [104] + list_join(code128B_mapping[c] for c in s)
    check_digit = (codes[0] + sum(i * x for i,x in enumerate(codes))) % 103
    codes.append(check_digit)
    codes.append(106) # stop code
    return u''.join(code128_chars[x] for x in codes)

def csv_to_dict_list(filestream):
    file_str = filestream.read()
    dict_list = []
    for row in DictReader(file_str.decode().splitlines(), skipinitialspace=True):
        dict_list += [{k: v for k, v in row.items()}]
    return dict_list
