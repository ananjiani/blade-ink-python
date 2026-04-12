"""Load the Bink C library."""
import os
import platform
import ctypes.util

def _load_library():
    # First, look for a bundled bink shared object on the lib folder.
    system = platform.system()
    library_name = None
    if system == 'Windows':
        library_name = 'bink.dll'
    elif system == 'Darwin':
        library_name = 'libbink.dylib'
    else:
        library_name = 'libbink.so'

    arch = "x86_64/"

    if platform.machine() == "arm64":
        arch = "arm64/"

    _filename = os.path.join(os.path.dirname(__file__), 'native/' + arch + library_name)

    # If no bundled shared object is found, look for a system-wide installed one.
    if not os.path.exists(_filename):
        # on windows all ctypes does when checking for the library
        # is to append .dll to the end and look for an exact match
        # within any entry in PATH.
        _filename = ctypes.util.find_library('bink')

        if _filename is None:
            if platform.system() == 'Windows':
                # Check current working directory for dll as ctypes fails to do so
                _filename = os.path.join(os.path.realpath('.'), "bink.dll")
            else:
                _filename = library_name

    try:
        #print("lib filename: ", _filename)
        lib = ctypes.CDLL(_filename)
    except (OSError, TypeError) as exc:
        lib = None
        raise RuntimeError('bink library not found') from exc
    return lib

LIB = _load_library()

LIB.bink_story_new.argtypes = [
    ctypes.POINTER(
        ctypes.c_void_p), ctypes.c_char_p, ctypes.POINTER(
            ctypes.c_char_p)]
LIB.bink_story_new.restype = ctypes.c_int

LIB.bink_story_can_continue.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_bool)]
LIB.bink_story_can_continue.restype = ctypes.c_int

BINK_OK = 0
BINK_FAIL = 1
BINK_FAIL_NULL_POINTER = 2

# --- Variable get/set ---

LIB.bink_var_get.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
LIB.bink_var_get.restype = ctypes.c_int

LIB.bink_var_set.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
LIB.bink_var_set.restype = ctypes.c_int

# --- Value constructors ---

LIB.bink_value_new_bool.argtypes = [ctypes.c_bool]
LIB.bink_value_new_bool.restype = ctypes.c_void_p

LIB.bink_value_new_int.argtypes = [ctypes.c_int64]
LIB.bink_value_new_int.restype = ctypes.c_void_p

LIB.bink_value_new_float.argtypes = [ctypes.c_double]
LIB.bink_value_new_float.restype = ctypes.c_void_p

LIB.bink_value_new_string.argtypes = [ctypes.c_char_p]
LIB.bink_value_new_string.restype = ctypes.c_void_p

# --- Value getters ---

LIB.bink_value_get_bool.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_bool)]
LIB.bink_value_get_bool.restype = ctypes.c_int

LIB.bink_value_get_int.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_int64)]
LIB.bink_value_get_int.restype = ctypes.c_int

LIB.bink_value_get_float.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
LIB.bink_value_get_float.restype = ctypes.c_int

LIB.bink_value_get_string.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
LIB.bink_value_get_string.restype = ctypes.c_int

LIB.bink_value_free.argtypes = [ctypes.c_void_p]
LIB.bink_value_free.restype = None

# --- External functions ---

LIB.bink_fun_args_count.argtypes = [ctypes.c_void_p]
LIB.bink_fun_args_count.restype = ctypes.c_int

LIB.bink_fun_args_get.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
LIB.bink_fun_args_get.restype = ctypes.c_int

# Callback type: void* fn(void* fun_args, void* userdata)
EXTERNAL_FUNCTION_CB = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)

LIB.bink_bind_external_function.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, EXTERNAL_FUNCTION_CB, ctypes.c_void_p]
LIB.bink_bind_external_function.restype = ctypes.c_int

LIB.bink_unbind_external_function.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p]
LIB.bink_unbind_external_function.restype = ctypes.c_int

# Callback type: void fn(void* var_name, void* new_value, void* userdata)
VARIABLE_OBSERVER_CB = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p)

LIB.bink_observe_variable.argtypes = [
    ctypes.c_void_p, ctypes.c_char_p, VARIABLE_OBSERVER_CB, ctypes.c_void_p]
LIB.bink_observe_variable.restype = ctypes.c_int
