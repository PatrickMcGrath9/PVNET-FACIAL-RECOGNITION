from cv2 import imencode, imdecode, IMREAD_COLOR
from numpy import uint8, ndarray, frombuffer, copy
from base64 import b64decode, b64encode

def encode_ndarray(array:ndarray):
    return b64encode(array.tobytes()).decode('utf-8')

def decode_ndarray(array:str, dtype=float):
    return copy(frombuffer(b64decode(array), dtype=dtype))

def decode_image(image_str:str):
    '''
    Convert image from B64 string
    '''
    return imdecode(decode_ndarray(image_str, dtype=uint8), IMREAD_COLOR)


def encode_image(image:ndarray):
    '''
    Convert image to B64 string
    '''
    return encode_ndarray(imencode('.jpg', image)[1])