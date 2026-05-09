
from django.http import JsonResponse
from project.settings import key_hashing
from cryptography.fernet import Fernet
import uuid
import datetime as dt
import re
from project.settings import CHAR_05, CHAR_10, CHAR_15
from django import template
from datetime import datetime
from django.utils import timezone
from app.helpers import get_local_now
register = template.Library()

@register.filter
def get_id_hashed_of_object(object_id):
    fernet = Fernet(key_hashing)
    encMessage = fernet.encrypt(str(object_id).encode())
    out = (encMessage).decode('ascii')
    return str(out)

def check_if_post_input_valid(text, max_length): 
    if not isinstance(text, str) or text.strip() == '':
        return ''

    pattern = r"^[\S\s][a-zA-Z0-9\u0600-\u06FF\s\)\(\\\/\_\-\³\%]{1," + str(max_length) + r"}\s*$"
    check = re.search(pattern, text)

    if check is not None:
        text = text.strip()
        return text[:max_length] if len(text) > max_length else text
    else:
        return ''
    
@register.filter
def to_12_hour(value):
    try:
        t = datetime.strptime(str(value), "%H:%M:%S")
    except ValueError:
        try:
            t = datetime.strptime(str(value), "%H:%M")
        except ValueError:
            return value  

    formatted = t.strftime("%I:%M %p").lstrip("0")
    return formatted.replace("AM", "a.m.").replace("PM", "p.m.")

def check_valid_text(text):
    check = re.search(r"^/var\s*.*;/g*$", text)
    if check is None:
        return text
    else:
        return ''
    
def get_id_of_object(hash_used):
    decMessage = None
    try :
        fernet = Fernet(key_hashing)
        decMessage = fernet.decrypt(str(hash_used)).decode()
    except Exception as err:
        pass

    return decMessage


def delete(request, model_name, condition):
    deleted_date            = get_local_now()
    object                  = model_name.objects.filter(condition)

    if not object.exists():
        return JsonResponse({"Result": "Fail", "message": "Object not found"}, safe=False, status=404)

    object.update(deleted_by=request.user, deleted_date = deleted_date)

    allJson = {"Result": "Fail"}

    allJson['Result'] = "Success"


    if allJson != None:
        return JsonResponse(allJson, safe=False)
    else:
        allJson['Result'] = "Fail"
from itertools import groupby
from operator import attrgetter
@register.filter
def merge_continuous_slots(slots):
    """
    Takes a list of ClinicSlot objects sorted by start_time
    and merges consecutive ones into (start, end) tuples.
    """
    if not slots:
        return []

    merged = []
    current_start = slots[0].start_time
    current_end = slots[0].end_time

    for slot in slots[1:]:
        if slot.start_time == current_end:
            # extend the block
            current_end = slot.end_time
        else:
            # save the block
            merged.append((current_start, current_end))
            # start new block
            current_start = slot.start_time
            current_end = slot.end_time

    merged.append((current_start, current_end))
    return merged
