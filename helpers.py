import secrets
import string

def random_string_generator():
    random_string = ''.join(
        (secrets.choice(string.ascii_letters + string.digits + string.punctuation) 
        for i in range(20))
    )
    return random_string

def results_url_compiler(base_url, start_index):
    return base_url + str(start_index)